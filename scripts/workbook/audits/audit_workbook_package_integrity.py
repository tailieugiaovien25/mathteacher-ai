import argparse
import json
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_WORKBOOK = Path(
    "data/working/LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

OUTPUT_FILE = Path(
    "output/reports/workbook_package_integrity_audit.json"
)

EXPECTED_CONTROL_RELATED_PARTS = 74
EXPECTED_VML_PARTS = 3
EXPECTED_VBA_SIZE = 429568


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Audit package/relationship integrity "
            "của workbook XLSM."
        )
    )

    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook cần audit.",
    )

    return parser.parse_args()


def normalize_target(
    source_part: str,
    target: str,
) -> str:
    if target.startswith("/"):
        return target.lstrip("/")

    source_dir = posixpath.dirname(
        source_part
    )

    return posixpath.normpath(
        posixpath.join(
            source_dir,
            target,
        )
    ).lstrip("/")


def source_part_from_rels(
    rels_path: str,
) -> str | None:
    if rels_path == "_rels/.rels":
        return ""

    if "/_rels/" not in rels_path:
        return None

    folder, filename = rels_path.split(
        "/_rels/",
        1,
    )

    if not filename.endswith(".rels"):
        return None

    original_name = filename[:-5]

    return posixpath.join(
        folder,
        original_name,
    )


def inspect_relationships(
    archive: zipfile.ZipFile,
) -> dict:
    names = set(
        archive.namelist()
    )

    missing_targets = []
    external_targets = []

    relationship_count = 0

    rel_files = sorted(
        path
        for path in names
        if path.endswith(".rels")
    )

    for rels_path in rel_files:
        try:
            root = ET.fromstring(
                archive.read(
                    rels_path
                )
            )

        except ET.ParseError as exc:
            missing_targets.append(
                {
                    "rels_path": rels_path,
                    "reason": (
                        "REL_XML_PARSE_ERROR"
                    ),
                    "detail": str(exc),
                }
            )

            continue

        source_part = (
            source_part_from_rels(
                rels_path
            )
        )

        if source_part is None:
            continue

        for rel in root:
            relationship_count += 1

            rel_id = rel.attrib.get(
                "Id"
            )

            target = rel.attrib.get(
                "Target"
            )

            target_mode = rel.attrib.get(
                "TargetMode"
            )

            rel_type = rel.attrib.get(
                "Type"
            )

            if not target:
                missing_targets.append(
                    {
                        "rels_path": (
                            rels_path
                        ),
                        "relationship_id": (
                            rel_id
                        ),
                        "reason": (
                            "EMPTY_TARGET"
                        ),
                    }
                )

                continue

            if target_mode == "External":
                external_targets.append(
                    {
                        "rels_path": (
                            rels_path
                        ),
                        "relationship_id": (
                            rel_id
                        ),
                        "target": target,
                        "type": rel_type,
                    }
                )

                continue

            if source_part == "":
                resolved = (
                    target.lstrip("/")
                )
            else:
                resolved = (
                    normalize_target(
                        source_part,
                        target,
                    )
                )

            if resolved not in names:
                missing_targets.append(
                    {
                        "rels_path": (
                            rels_path
                        ),
                        "relationship_id": (
                            rel_id
                        ),
                        "target": target,
                        "resolved_target": (
                            resolved
                        ),
                        "type": rel_type,
                        "reason": (
                            "TARGET_PART_MISSING"
                        ),
                    }
                )

    return {
        "relationship_count": (
            relationship_count
        ),
        "relationship_file_count": (
            len(rel_files)
        ),
        "missing_targets": (
            missing_targets
        ),
        "external_targets": (
            external_targets
        ),
    }


def inspect_control_related_parts(
    archive: zipfile.ZipFile,
) -> dict:
    names = set(
        archive.namelist()
    )

    control_parts = sorted(
        path
        for path in names
        if (
            path.startswith(
                "xl/controls/"
            )
            and not path.endswith(
                ".rels"
            )
        )
    )

    ctrl_prop_parts = sorted(
        path
        for path in names
        if path.startswith(
            "xl/ctrlProps/"
        )
    )

    control_rel_files = sorted(
        path
        for path in names
        if (
            path.startswith(
                "xl/controls/_rels/"
            )
            and path.endswith(
                ".rels"
            )
        )
    )

    combined_count = (
        len(control_parts)
        + len(ctrl_prop_parts)
    )

    return {
        "control_parts": (
            control_parts
        ),
        "control_part_count": (
            len(control_parts)
        ),
        "ctrl_prop_parts": (
            ctrl_prop_parts
        ),
        "ctrl_prop_part_count": (
            len(ctrl_prop_parts)
        ),
        "control_relationship_files": (
            control_rel_files
        ),
        "control_relationship_file_count": (
            len(control_rel_files)
        ),
        "combined_control_related_count": (
            combined_count
        ),
    }


def inspect_package(
    workbook: Path,
) -> dict:
    with zipfile.ZipFile(
        workbook,
        "r",
    ) as archive:
        bad_zip_entry = (
            archive.testzip()
        )

        names = set(
            archive.namelist()
        )

        relationships = (
            inspect_relationships(
                archive
            )
        )

        controls = (
            inspect_control_related_parts(
                archive
            )
        )

        vml_parts = sorted(
            path
            for path in names
            if "vmlDrawing" in path
        )

        drawing_parts = sorted(
            path
            for path in names
            if path.startswith(
                "xl/drawings/"
            )
        )

        vba_present = (
            "xl/vbaProject.bin"
            in names
        )

        vba_size = None

        if vba_present:
            vba_size = len(
                archive.read(
                    "xl/vbaProject.bin"
                )
            )

    return {
        "zip_integrity_ok": (
            bad_zip_entry is None
        ),
        "bad_zip_entry": (
            bad_zip_entry
        ),
        "package_part_count": (
            len(names)
        ),
        "relationships": (
            relationships
        ),
        "controls": (
            controls
        ),
        "vml_parts": (
            vml_parts
        ),
        "vml_part_count": (
            len(vml_parts)
        ),
        "drawing_parts": (
            drawing_parts
        ),
        "drawing_part_count": (
            len(drawing_parts)
        ),
        "vba_present": (
            vba_present
        ),
        "vba_size_bytes": (
            vba_size
        ),
    }


def main():
    args = parse_args()

    workbook = args.workbook

    if not workbook.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: "
            f"{workbook}"
        )

    print("=" * 72)

    print(
        "M5-XLS-CLEANUP-01D4 - "
        "PACKAGE / RELATIONSHIP INTEGRITY"
    )

    print("=" * 72)

    print(
        "Chế độ: READ / AUDIT ONLY"
    )

    print(
        "Workbook sẽ KHÔNG bị thay đổi."
    )

    print(
        f"Workbook đang audit: "
        f"{workbook}"
    )

    result = inspect_package(
        workbook
    )

    relationships = result[
        "relationships"
    ]

    controls = result[
        "controls"
    ]

    missing_targets = (
        relationships[
            "missing_targets"
        ]
    )

    external_targets = (
        relationships[
            "external_targets"
        ]
    )

    control_count = (
        controls[
            "control_part_count"
        ]
    )

    ctrl_prop_count = (
        controls[
            "ctrl_prop_part_count"
        ]
    )

    combined_control_count = (
        controls[
            "combined_control_related_count"
        ]
    )

    control_rel_count = (
        controls[
            "control_relationship_file_count"
        ]
    )

    zip_pass = (
        result[
            "zip_integrity_ok"
        ]
    )

    relationship_pass = (
        len(missing_targets) == 0
    )

    control_pass = (
        combined_control_count
        == EXPECTED_CONTROL_RELATED_PARTS
    )

    vml_pass = (
        result[
            "vml_part_count"
        ]
        == EXPECTED_VML_PARTS
    )

    vba_pass = (
        result[
            "vba_present"
        ]
        and result[
            "vba_size_bytes"
        ]
        == EXPECTED_VBA_SIZE
    )

    pass_result = (
        zip_pass
        and relationship_pass
        and control_pass
        and vml_pass
        and vba_pass
    )

    report = {
        "audit_id": (
            "M5-XLS-CLEANUP-01D4"
        ),
        "mode": (
            "READ_ONLY_AUDIT"
        ),
        "workbook_modified": False,
        "workbook": str(
            workbook
        ),

        "summary": {
            "zip_integrity_ok": (
                zip_pass
            ),
            "package_part_count": (
                result[
                    "package_part_count"
                ]
            ),
            "relationship_file_count": (
                relationships[
                    "relationship_file_count"
                ]
            ),
            "relationship_count": (
                relationships[
                    "relationship_count"
                ]
            ),
            "missing_relationship_targets": (
                len(
                    missing_targets
                )
            ),
            "external_relationship_targets": (
                len(
                    external_targets
                )
            ),
            "control_parts": (
                control_count
            ),
            "ctrl_prop_parts": (
                ctrl_prop_count
            ),
            "combined_control_related_parts": (
                combined_control_count
            ),
            "control_relationship_files": (
                control_rel_count
            ),
            "vml_parts": (
                result[
                    "vml_part_count"
                ]
            ),
            "drawing_parts": (
                result[
                    "drawing_part_count"
                ]
            ),
            "vba_present": (
                result[
                    "vba_present"
                ]
            ),
            "vba_size_bytes": (
                result[
                    "vba_size_bytes"
                ]
            ),
            "integrity_pass": (
                pass_result
            ),
        },

        "missing_targets": (
            missing_targets
        ),

        "external_targets": (
            external_targets
        ),

        "control_details": (
            controls
        ),
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        "ZIP integrity: "
        + (
            "PASS"
            if zip_pass
            else "FAIL"
        )
    )

    print(
        f"Package parts: "
        f"{result['package_part_count']}"
    )

    print(
        "Relationship files: "
        f"{relationships['relationship_file_count']}"
    )

    print(
        "Relationships: "
        f"{relationships['relationship_count']}"
    )

    print(
        "Missing relationship targets: "
        f"{len(missing_targets)}"
    )

    print(
        "External relationship targets: "
        f"{len(external_targets)}"
    )

    print()
    print("CONTROL STRUCTURE")
    print("=" * 72)

    print(
        f"xl/controls parts: "
        f"{control_count}"
    )

    print(
        f"xl/ctrlProps parts: "
        f"{ctrl_prop_count}"
    )

    print(
        "Combined Control/Prop parts: "
        f"{combined_control_count}"
    )

    print(
        "Expected Control/Prop parts: "
        f"{EXPECTED_CONTROL_RELATED_PARTS}"
    )

    print(
        "Control structure: "
        + (
            "PASS"
            if control_pass
            else "FAIL"
        )
    )

    print(
        f"Control .rels files: "
        f"{control_rel_count}"
    )

    print()
    print("OTHER PACKAGE STRUCTURE")
    print("=" * 72)

    print(
        f"VML parts: "
        f"{result['vml_part_count']}"
    )

    print(
        "VML structure: "
        + (
            "PASS"
            if vml_pass
            else "FAIL"
        )
    )

    print(
        f"Drawing parts: "
        f"{result['drawing_part_count']}"
    )

    print(
        "VBA project: "
        + (
            "PASS"
            if result[
                "vba_present"
            ]
            else "FAIL"
        )
    )

    print(
        "VBA size: "
        f"{result['vba_size_bytes']}"
    )

    print(
        "VBA structure: "
        + (
            "PASS"
            if vba_pass
            else "FAIL"
        )
    )

    if missing_targets:
        print()
        print(
            "MISSING RELATIONSHIP TARGETS"
        )

        for item in (
            missing_targets[:20]
        ):
            print(
                f"- {item}"
            )

    if external_targets:
        print()
        print(
            "EXTERNAL RELATIONSHIPS"
        )

        for item in (
            external_targets[:20]
        ):
            print(
                f"- {item}"
            )

    print()
    print(
        "Đã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    if pass_result:
        print()
        print(
            "KẾT QUẢ: "
            "PACKAGE INTEGRITY REGRESSION PASS"
        )

    else:
        print()
        print(
            "KẾT QUẢ: "
            "PACKAGE INTEGRITY REGRESSION FAIL"
        )

        raise RuntimeError(
            "Package integrity chưa đạt."
        )


if __name__ == "__main__":
    main()