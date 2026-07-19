import re


def parse_version_parts(version):

    version = str(
        version or ""
    ).strip().lstrip("vV")

    parts = []

    for part in re.split(
        r"[^0-9]+",
        version
    ):

        if part:

            parts.append(int(part))

    while len(parts) < 3:

        parts.append(0)

    return tuple(parts[:3])


def is_newer_version(latest_version, current_version):

    return parse_version_parts(latest_version) > parse_version_parts(
        current_version
    )

