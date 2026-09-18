#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "firmware" / "app"
FILES = [
    "hallbulb_light_state.c",
    "hallbulb_light_state.h",
    "hallbulb_zcl_adapter.c",
    "hallbulb_zcl_adapter.h",
]
SOURCE_ENTRIES = ["hallbulb_light_state.c", "hallbulb_zcl_adapter.c"]


def require_once(text, needle, label):
    count = text.count(needle)
    if count != 1:
        raise RuntimeError(f"expected exactly one {label}, found {count}")


def copy_sources(project_dir: Path):
    for name in FILES:
        shutil.copy2(APP_DIR / name, project_dir / name)


def patch_app(app_c: Path):
    text = app_c.read_text(encoding="utf-8")
    include = '#include "hallbulb_zcl_adapter.h"\n'
    changed = False
    if include not in text:
        require_once(text, '#include "app/framework/include/af.h"\n', "af include")
        text = text.replace('#include "app/framework/include/af.h"\n',
                            '#include "app/framework/include/af.h"\n' + include, 1)
        changed = True
    marker = "  (void)value;\n"
    sync_block = (
        "\n  if (mask == CLUSTER_MASK_SERVER\n"
        "      && (clusterId == ZCL_ON_OFF_CLUSTER_ID\n"
        "          || clusterId == ZCL_LEVEL_CONTROL_CLUSTER_ID\n"
        "          || clusterId == ZCL_COLOR_CONTROL_CLUSTER_ID)) {\n"
        "    hb_zcl_sync_output(endpoint);\n"
        "  }\n"
    )
    if "hb_zcl_sync_output(endpoint);" not in text:
        require_once(text, marker, "post-attribute value marker")
        text = text.replace(marker, marker + sync_block, 1)
        changed = True
    if changed:
        app_c.write_text(text, encoding="utf-8")


def patch_seed(project_dir: Path, slcp: Path):
    copy_sources(project_dir)
    text = slcp.read_text(encoding="utf-8")
    for name in SOURCE_ENTRIES:
        if f"- path: {name}" not in text:
            require_once(text, "- path: app.c\n", "app.c source entry")
            text = text.replace("- path: app.c\n", f"- path: app.c\n- path: {name}\n", 1)
    slcp.write_text(text, encoding="utf-8")
    patch_app(project_dir / "app.c")
    print(f"Patched SLC seed project: {slcp.name}")

def stage_generated(project_dir: Path):
    copy_sources(project_dir)
    app_c = project_dir / "app.c"
    text = app_c.read_text(encoding="utf-8")
    if '#include "hallbulb_zcl_adapter.h"' not in text:
        raise RuntimeError("generated app.c is missing the light-core include")
    if "hb_zcl_sync_output(endpoint);" not in text:
        raise RuntimeError("generated app.c is missing the light-core sync hook")
    print(f"Staged headers/sources into generated project: {project_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()
    project_dir = args.project_dir.resolve()
    slcp_files = list(project_dir.glob("*.slcp"))
    if len(slcp_files) == 1:
        patch_seed(project_dir, slcp_files[0])
    elif len(slcp_files) == 0:
        stage_generated(project_dir)
    else:
        raise RuntimeError(f"expected zero or one .slcp in {project_dir}, found {len(slcp_files)}")


if __name__ == "__main__":
    main()
