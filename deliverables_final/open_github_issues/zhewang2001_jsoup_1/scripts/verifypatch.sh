#!/bin/bash
set -e

echo "=== Step 1: Cloning repository ==="
git clone https://github.com/zhewang2001/jsoup.git jsoup-verify
cd jsoup-verify

echo "=== Step 2: Applying pom.xml patch ==="
python3 - << 'PYEOF'
with open("pom.xml", "r") as f:
    content = f.read()

# Add clover executions block
old_clover = """			<plugin>
				<groupId>org.openclover</groupId>
				<artifactId>clover-maven-plugin</artifactId>
				<version>4.4.1</version>
				<configuration>
					<encoding>UTF-8</encoding>
				</configuration>
			</plugin>"""

new_clover = """			<plugin>
				<groupId>org.openclover</groupId>
				<artifactId>clover-maven-plugin</artifactId>
				<version>4.4.1</version>
				<configuration>
					<encoding>UTF-8</encoding>
				</configuration>
				<executions>
					<execution>
						<id>clover-setup</id>
						<phase>pre-integration-test</phase>
						<goals>
							<goal>setup</goal>
						</goals>
					</execution>
					<execution>
						<id>clover</id>
						<phase>post-integration-test</phase>
						<goals>
							<goal>clover</goal>
						</goals>
					</execution>
				</executions>
			</plugin>
			<plugin>
				<groupId>org.jacoco</groupId>
				<artifactId>jacoco-maven-plugin</artifactId>
				<version>0.8.8</version>
				<executions>
					<execution>
						<goals>
							<goal>prepare-agent</goal>
						</goals>
					</execution>
					<execution>
						<id>report</id>
						<phase>prepare-package</phase>
						<goals>
							<goal>report</goal>
						</goals>
					</execution>
				</executions>
			</plugin>"""

if old_clover in content:
    content = content.replace(old_clover, new_clover)
    with open("pom.xml", "w") as f:
        f.write(content)
    print("pom.xml patched successfully")
else:
    print("ERROR: Could not find clover plugin block in pom.xml - check indentation/formatting")
    exit(1)
PYEOF

echo "=== Step 3: Creating comparison script ==="
cat > compare_coverage.sh << 'SCRIPTEOF'
#!/bin/bash

echo "Extracting JaCoCo covered lines..."
awk '
BEGIN { current_package = ""; current_filename = ""; }
/<package name=/{
    pkg_line = $0;
    match(pkg_line, /name="[^"]*"/);
    current_package = substr(pkg_line, RSTART+6, RLENGTH-7);
}
/<class .* sourcefilename=/{
    class_line = $0;
    match(class_line, /sourcefilename="[^"]*"/);
    current_filename = substr(class_line, RSTART+16, RLENGTH-17);
}
/<line nr=.* ci=/{
    line_data = $0;
    match(line_data, /nr="[0-9]+"/);
    line_nr = substr(line_data, RSTART+4, RLENGTH-5);
    match(line_data, /ci="[0-9]+"/);
    ci = substr(line_data, RSTART+4, RLENGTH-5);
    if (ci > 0) { print current_package "/" current_filename ":" line_nr }
}' target/site/jacoco/jacoco.xml > jacoco_covered_lines.txt

echo "Extracting Clover covered lines..."
awk '
BEGIN { current_package = ""; current_filename = ""; }
/<package name=/{
    pkg_line = $0;
    match(pkg_line, /name="[^"]*"/);
    current_package = substr(pkg_line, RSTART+6, RLENGTH-7);
    gsub(/\./, "/", current_package);
}
/<file name=.* path=/{
    file_line = $0;
    match(file_line, /name="[^"]*"/);
    current_filename = substr(file_line, RSTART+6, RLENGTH-7);
}
/<line num=.* count=/{
    line_data = $0;
    match(line_data, /num="[0-9]+"/);
    line_nr = substr(line_data, RSTART+5, RLENGTH-6);
    match(line_data, /count="[0-9]+"/);
    count = substr(line_data, RSTART+7, RLENGTH-8);
    if (count > 0) { print current_package "/" current_filename ":" line_nr }
}' target/site/clover/clover.xml > clover_covered_lines.txt

echo "Generating comparison file..."
echo "Lines covered by JaCoCo but not Clover:" > coverage_comparison.txt
comm -23 <(sort jacoco_covered_lines.txt) <(sort clover_covered_lines.txt) >> coverage_comparison.txt
echo "" >> coverage_comparison.txt
echo "Lines covered by Clover but not JaCoCo:" >> coverage_comparison.txt
comm -13 <(sort jacoco_covered_lines.txt) <(sort clover_covered_lines.txt) >> coverage_comparison.txt

rm jacoco_covered_lines.txt clover_covered_lines.txt
SCRIPTEOF
chmod +x compare_coverage.sh

echo "=== Step 4: Running Maven build and generating reports inside Docker ==="
docker run --rm \
  -v "$(pwd)":/testbed \
  -w /testbed \
  python:3.11 \
  bash -c "
    apt-get update -q &&
    apt-get install -y -q maven &&
    mvn clean install jacoco:report clover:clover &&
    bash compare_coverage.sh
  "

echo "=== Step 5: Verifying outputs ==="
PASS=true

if [ -f "target/site/jacoco/jacoco.xml" ]; then
    echo "PASS: JaCoCo report exists"
else
    echo "FAIL: JaCoCo report missing"
    PASS=false
fi

if [ -f "target/site/clover/clover.xml" ]; then
    echo "PASS: Clover report exists"
else
    echo "FAIL: Clover report missing"
    PASS=false
fi

if [ -f "coverage_comparison.txt" ]; then
    echo "PASS: coverage_comparison.txt exists"
else
    echo "FAIL: coverage_comparison.txt missing"
    PASS=false
fi

echo ""
echo "=== Coverage Comparison Results ==="
cat coverage_comparison.txt

echo ""
if [ "$PASS" = true ]; then
    echo "=== ALL CHECKS PASSED - The agent fix works correctly ==="
else
    echo "=== SOME CHECKS FAILED - Review output above ==="
fi