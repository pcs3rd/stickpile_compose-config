#!/usr/bin/env python3
"""
generate_stack_table.py

Parses all compose.yaml files in the repo and updates the STACKS_README.md
between <!-- STACK-TABLE:<path> --> / <!-- /STACK-TABLE:<path> --> markers.
Also updates the <!-- LAST-UPDATED --> timestamp.

Usage:
    python3 scripts/generate_stack_table.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Run: pip install pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
README_PATH = REPO_ROOT / "docs" / "services-overview.md"


def parse_image(image_str: str) -> tuple[str, str]:
    """Split 'image:tag' or 'image@sha256:...' into (image, version)."""
    if not image_str:
        return ("*unknown*", "*unknown*")
    # Strip sha256 digest suffix for display, keep the tag
    image_str = str(image_str)
    at_pos = image_str.find("@")
    if at_pos != -1:
        image_str = image_str[:at_pos]
    if ":" in image_str:
        # Split on last colon to handle registries with ports (e.g. registry:5000/img:tag)
        last_colon = image_str.rfind(":")
        image = image_str[:last_colon]
        version = image_str[last_colon + 1:]
    else:
        image = image_str
        version = "latest"
    return image, version


def get_networks(service: dict) -> str:
    """Return a human-readable network string for a service."""
    network_mode = service.get("network_mode")
    if network_mode:
        return f"`{network_mode}` (network_mode)"

    networks = service.get("networks")
    if not networks:
        return "*(none defined)*"

    if isinstance(networks, list):
        names = networks
    elif isinstance(networks, dict):
        names = list(networks.keys())
    else:
        return "*(none defined)*"

    return ", ".join(f"`{n}`" for n in names)


def get_depends_on(service: dict) -> str:
    """Return ✅ (with deps listed) or ❌."""
    deps = service.get("depends_on")
    if not deps:
        return "❌"
    if isinstance(deps, list):
        names = deps
    elif isinstance(deps, dict):
        names = list(deps.keys())
    else:
        return "❌"
    return "✅ (" + ", ".join(f"`{d}`" for d in names) + ")"


def generate_table(compose_path: Path) -> str | None:
    """Parse a compose.yaml and return a markdown table string."""
    try:
        with open(compose_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"  WARNING: Could not parse {compose_path}: {e}")
        return None

    if not data or "services" not in data:
        return None

    services = data["services"]
    rows = []
    for name, svc in services.items():
        if not svc:
            continue
        image_raw = svc.get("image", "")
        image, version = parse_image(image_raw)
        networks = get_networks(svc)
        depends = get_depends_on(svc)
        rows.append(f"| `{name}` | `{image}` | `{version}` | {networks} | {depends} |")

    if not rows:
        return None

    lines = [
        "| Container | Image | Version | Networks | depends_on |",
        "|---|---|---|---|---|",
    ] + rows
    return "\n".join(lines)


def update_readme(readme_path: Path) -> int:
    """Find all STACK-TABLE markers in the README and replace their contents."""
    content = readme_path.read_text()
    updated = content
    changes = 0

    # Find all stack table markers
    marker_pattern = re.compile(
        r"(<!-- STACK-TABLE:(?P<path>[^>]+) -->)\n.*?\n(<!-- /STACK-TABLE:(?P=path) -->)",
        re.DOTALL,
    )

    for match in marker_pattern.finditer(content):
        stack_path = match.group("path").strip()
        compose_file = REPO_ROOT / stack_path / "compose.yaml"

        if not compose_file.exists():
            print(f"  SKIP: {compose_file} not found")
            continue

        print(f"  Processing: {stack_path}")
        table = generate_table(compose_file)
        if table is None:
            print(f"  SKIP: No services found in {compose_file}")
            continue

        open_marker = f"<!-- STACK-TABLE:{stack_path} -->"
        close_marker = f"<!-- /STACK-TABLE:{stack_path} -->"
        replacement = f"{open_marker}\n{table}\n{close_marker}"

        if replacement not in updated:
            updated = updated.replace(match.group(0), replacement)
            changes += 1

    # Update the LAST-UPDATED timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    updated = re.sub(
        r"<!-- LAST-UPDATED -->.*?<!-- /LAST-UPDATED -->",
        f"<!-- LAST-UPDATED -->{timestamp}<!-- /LAST-UPDATED -->",
        updated,
    )

    if updated != content:
        readme_path.write_text(updated)
        print(f"  README updated ({changes} table(s) changed).")
    else:
        print("  README already up to date.")

    return changes


if __name__ == "__main__":
    print(f"Updating {README_PATH}...")
    update_readme(README_PATH)
