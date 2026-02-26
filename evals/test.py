from pydriller import Repository
import json

# Repos to mine
repos = ["https://github.com/tiangolo/fastapi"]
dataset = []

for commit in Repository(repos, only_modifications_with_file_types=['.py']).traverse_commits():
    # Only look for bug-fix commits
    if "fix" in commit.msg.lower() and len(commit.modified_files) == 1:
        for m in commit.modified_files:
            dataset.append({
                "commit_hash": commit.hash,
                "issue_description": commit.msg,
                "code_before": m.source_code_before, # The "Test Input"
                "fix_code": m.source_code,           # The "Ground Truth"
                "diff": m.diff
            })
    if len(dataset) >= 50: break

with open("golden_set.jsonl", "w") as f:
    for entry in dataset:
        f.write(json.dumps(entry) + "\n")