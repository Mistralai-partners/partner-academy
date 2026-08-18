"""Publish helpers for release-tools.

This is the "before" state that diff-to-review.patch proposes to change. The reviewer
reads the patch and flags the risks; it never applies or edits anything.
"""

import subprocess


def verify_signature(artifact):
    """Return True if the artifact signature is valid."""
    return subprocess.run(["gpg", "--verify", f"{artifact}.sig", artifact],
                          check=False).returncode == 0


def publish(artifact, registry_url, token):
    """Upload a build artifact to the release registry."""
    if not verify_signature(artifact):
        raise RuntimeError("artifact signature check failed; refusing to publish")

    cmd = ["curl", "-sf", "-H", f"Authorization: Bearer {token}", registry_url]
    result = subprocess.run(
        cmd + ["--data-binary", f"@{artifact}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"publish failed: {result.stderr.decode()}")
    return result.stdout.decode()
