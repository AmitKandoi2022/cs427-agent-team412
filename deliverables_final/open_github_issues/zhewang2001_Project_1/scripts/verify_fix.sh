#!/usr/bin/env bash
# quick script to sanity check that files and config were generated
set -euo pipefail

echo "Verifying Project issue #1 deliverable"

# Check required files exist
test -f app/build.gradle
test -f config/checkstyle/checkstyle.xml
test -f app/src/main/java/edu/uiuc/cs427app/MainActivity.java
test -f app/src/main/java/edu/uiuc/cs427app/DetailsActivity.java
test -f app/src/main/java/edu/uiuc/cs427app/package-info.java

echo "Checking Checkstyle wiring..."
grep -q "id 'checkstyle'" app/build.gradle
grep -q "checkstyle.xml" app/build.gradle

echo "Checking Javadoc rules..."
grep -q "JavadocMethod" config/checkstyle/checkstyle.xml
grep -q "JavadocType" config/checkstyle/checkstyle.xml
grep -q "JavadocVariable" config/checkstyle/checkstyle.xml

echo "Checking Javadoc comments added..."
grep -q '/\*\*' app/src/main/java/edu/uiuc/cs427app/MainActivity.java
grep -q '/\*\*' app/src/main/java/edu/uiuc/cs427app/DetailsActivity.java

echo "NOTE: Java not available, skipping gradlew checkstyle"
echo "done"