#!/usr/bin/env bash
cat > releasenotes.md << EOF
{
    "commit_id": "${GITHUB_SHA}",
    "branch_name": "${GITHUB_REF}"
}
EOF
