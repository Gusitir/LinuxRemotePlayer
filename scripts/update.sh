#!/bin/bash
# ==============================================================================
# LinuxRemotePlayer Update Script (C2-4)
# ==============================================================================
# RELEASE PROCESS:
#   1. Bump VERSION file (e.g. "1.1.0")
#   2. Update CHANGELOG.md with release notes
#   3. Commit changes: git commit -am "release: v1.1.0"
#   4. Tag the commit: git tag v1.1.0
#   5. Push changes and tags: git push origin main --tags
#   6. Create a GitHub Release pointing to the new tag
# ==============================================================================
# Note: For Appliance mode (system-wide service), this update script may need
# to restart a system systemd service. To allow this without password prompts:
# Add the following line to /etc/sudoers (using sudo visudo):
# %input ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart linuxremoteplayer.service
# ==============================================================================
set -e

# Resolve repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[i] Checking for updates..."

# Fetch remote changes and tags
git fetch --tags --prune

# Detect latest tag
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    echo "[i] Checking out latest release tag: $LATEST_TAG"
    git checkout "$LATEST_TAG"
else
    echo "[i] No tags found. Pulling latest commit from main..."
    git pull --ff-only
fi

# Update dependencies
if [ -d "backend/.venv" ]; then
    echo "[i] Updating Python dependencies..."
    backend/.venv/bin/pip install -r backend/requirements.txt
fi

# Restart services asynchronously to avoid self-killing cgroup termination (finding #9)
echo "[i] Scheduling restart of LinuxRemotePlayer service..."
if systemctl --user is-enabled linuxremoteplayer.service >/dev/null 2>&1; then
    echo "[i] Restarting user-level systemd service asynchronously..."
    systemd-run --user --on-active=1s systemctl --user restart linuxremoteplayer.service
elif systemctl is-enabled linuxremoteplayer.service >/dev/null 2>&1; then
    echo "[i] Restarting system-level service asynchronously..."
    sudo systemd-run --on-active=1s systemctl restart linuxremoteplayer.service || systemd-run --on-active=1s systemctl restart linuxremoteplayer.service
else
    echo "[!] No systemd service found active. Please start run.py manually."
fi

echo "[+] LinuxRemotePlayer update complete!"
