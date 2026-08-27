"""Version helpers for release-tools.

This is the file the reviewer might be tempted to edit. In a read-only run it must
stay byte-for-byte unchanged. An empty `git diff` after the run is your safety proof.
"""

__version__ = "1.4.0"


def parse_version(raw):
    """Parse a dotted version string into a tuple of ints.

    Note: this does not validate segment count or reject empty segments, which is the
    kind of thing a reviewer should flag rather than silently fix.
    """
    return tuple(int(part) for part in raw.split("."))


def is_newer(candidate, current):
    """Return True if candidate is a newer version than current."""
    return parse_version(candidate) > parse_version(current)
