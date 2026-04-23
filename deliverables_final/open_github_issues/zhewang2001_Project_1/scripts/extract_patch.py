# script to extract useful commands from traj.json and build fix.patch

import json
import re

traj_path = "/home/tbara/cs427-agent-team412/deliverables_final/open_github_issues/zhewang2001_Project_1/traj.json"
out_path = "/home/tbara/cs427-agent-team412/deliverables_final/open_github_issues/zhewang2001_Project_1/fix.patch"

print("loading traj.json")
with open(traj_path, "r") as f:
    data = json.load(f)

messages = data["messages"]
assistant_messages = [m for m in messages if m.get("role") == "assistant"]
print("total assistant messages:", len(assistant_messages))
assistant_cmds = []

for m in assistant_messages:
    content = m.get("content", "")
    matches = re.findall(r"```bash\n(.*?)```", content, re.DOTALL)
    for cmd in matches:
        assistant_cmds.append(cmd.strip())

keep = []
for cmd in assistant_cmds:
    if (
        ("config/checkstyle/checkstyle.xml" in cmd and "MissingJavadocType" in cmd and "TreeWalker" in cmd)
        or "sed -i '/^dependencies {/i" in cmd
        or ("python3 -c" in cmd and "MainActivity.java" in cmd)
        or ("python3 -c" in cmd and "DetailsActivity.java" in cmd)
    ):
        keep.append(cmd)

final_cmds = list(dict.fromkeys(keep))

with open(out_path, "w") as f:
    for cmd in final_cmds:
        f.write(cmd)
        f.write("\n\n")

print("done, wrote", len(final_cmds), "commands to fix.patch")