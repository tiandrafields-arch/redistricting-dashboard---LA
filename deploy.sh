#!/usr/bin/env bash
#
# deploy.sh — publish the Louisiana Redistricting Equity Dashboard to GitHub Pages.
#
# What it does:
#   1. Clones your GitHub repo fresh into a temporary folder (so it always
#      builds on the true published state, never a stale copy).
#   2. Copies index.html (and README.md if changed) from THIS folder into it.
#   3. Commits and pushes. GitHub Pages rebuilds the live site in about a minute.
#
# It only touches index.html and README.md, so any other files already in the
# repo are left untouched. No force-push, so nothing on GitHub is ever clobbered.
#
# Run it from a terminal that can reach the internet:
#     cd "/Users/tiandrafields/Documents/Claude/Projects/Redistricting - Louisiana"
#     bash deploy.sh
#
set -euo pipefail

REPO_URL="https://github.com/tiandrafields-arch/redistricting-dashboard---LA.git"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "→ Cloning $REPO_URL ..."
git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo"

echo "→ Applying updated files ..."
cp "$SRC_DIR/index.html" "$TMP_DIR/repo/index.html"
if [ -f "$SRC_DIR/README.md" ]; then
  cp "$SRC_DIR/README.md" "$TMP_DIR/repo/README.md"
fi

cd "$TMP_DIR/repo"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if git diff --quiet; then
  echo "✓ Nothing changed — the live site already matches these files. Done."
  exit 0
fi

git add index.html README.md 2>/dev/null || git add index.html
git commit -m "Update dashboard: RDH change-analysis reconciliation

- Dual-basis Black VAP table (Any Part Black vs. Black alone)
- Removed / Retained / Added composition for all six districts
- Litigation status updated: Act 2 in effect for Nov 3, 2026; challenge pending"

echo "→ Pushing to $BRANCH ..."
echo ""
echo "This repo is owned by the account 'tiandrafields-arch'. Your Mac's saved"
echo "GitHub login is a different account, so paste a token for tiandrafields-arch"
echo "below. (Make one at: GitHub → Settings → Developer settings → Personal access"
echo "tokens → Fine-grained → this repo → Contents: Read and write.)"
echo ""
# You can supply the token inline so there is no prompt to paste into:
#     GH_TOKEN=github_pat_xxxxx bash deploy.sh
if [ -z "${GH_TOKEN:-}" ]; then
  read -rp "Paste GitHub token for tiandrafields-arch (it WILL show on screen), or press Enter to use your saved login: " GH_TOKEN
fi
if [ -n "${GH_TOKEN:-}" ]; then
  git push "https://tiandrafields-arch:${GH_TOKEN}@github.com/tiandrafields-arch/redistricting-dashboard---LA.git" "$BRANCH"
else
  git push origin "$BRANCH"
fi

echo ""
echo "✓ Pushed. GitHub Pages will rebuild in about a minute."
echo "  Live: https://tiandrafields-arch.github.io/redistricting-dashboard---LA/"
