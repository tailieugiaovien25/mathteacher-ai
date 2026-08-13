import json
import re
import zipfile
from pathlib import Path


WORKING_FILE = Path(
    "data/working/LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

MANIFEST_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)

OUTPUT_FILE = Path(
    "output/reports/macro10_cleanup_dryrun.json"
)


def read_text_safe(
    archive: zipfile.ZipFile,
    path: str,
) -> str:
    try:
        content = archive.read(path)
    except KeyError:
        return ""

    return content.decode(
        "utf-8",
        errors="replace",
    )


def extract_shape_ids_from_vml(
    text: str,
) -> set[str]:
    """Lấy toàn bộ shape id trong VML."""

    pattern = re.compile(
        r"<(?:\w+:)?shape\b"
        r"(?P<attrs>[^>]*)>",
        flags=re.IGNORECASE,
    )

    shape_ids = set()

    for match in pattern.finditer(text):
        attrs = match.group(
            "attrs"
        )

        id_match = re.search(
            r'\bid\s*=\s*"([^"]+)"',
            attrs,
            flags=re.IGNORECASE,
        )

        if id_match:
            shape_ids.add(
                id_match.group(1)
            )

    return shape_ids


def main() -> None:
    if not WORKING_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy working workbook: "
            f"{WORKING_FILE}"
        )

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy manifest: "
            f"{MANIFEST_FILE}"
        )

    manifest = json.loads(
        MANIFEST_FILE.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    remove_items = [
        item
        for item in manifest.get(
            "items",
            [],
        )
        if item.get(
            "decision"
        )
        == "REMOVE_CANDIDATE"
    ]

    target_shape_ids = {
        item.get(
            "shape_id"
        )
        for item in remove_items
        if item.get(
            "shape_id"
        )
    }

    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01C1 - "
        "MACRO10 CLEANUP TARGET DRY-RUN"
    )
    print("=" * 72)

    print(
        "Chế độ: DRY RUN / READ ONLY"
    )

    print(
        "Workbook sẽ KHÔNG bị thay đổi."
    )

    all_vml_shape_ids = set()

    vml_report = []

    with zipfile.ZipFile(
        WORKING_FILE,
        "r",
    ) as archive:
        archive.testzip_result = (
            archive.testzip()
        )

        vml_paths = sorted(
            path
            for path in archive.namelist()
            if "vmlDrawing"
            in path
        )

        for path in vml_paths:
            text = read_text_safe(
                archive,
                path,
            )

            shape_ids = (
                extract_shape_ids_from_vml(
                    text
                )
            )

            all_vml_shape_ids.update(
                shape_ids
            )

            matched = sorted(
                shape_ids
                & target_shape_ids
            )

            vml_report.append(
                {
                    "vml_path": path,
                    "shape_count": len(
                        shape_ids
                    ),
                    "matched_target_count": len(
                        matched
                    ),
                    "matched_shape_ids": (
                        matched
                    ),
                }
            )

        has_vba = (
            "xl/vbaProject.bin"
            in archive.namelist()
        )

        vba_size = None

        if has_vba:
            vba_size = len(
                archive.read(
                    "xl/vbaProject.bin"
                )
            )

    matched_targets = (
        target_shape_ids
        & all_vml_shape_ids
    )

    missing_targets = (
        target_shape_ids
        - all_vml_shape_ids
    )

    extra_match_count = (
        len(matched_targets)
        - len(target_shape_ids)
    )

    target_count = len(
        target_shape_ids
    )

    matched_count = len(
        matched_targets
    )

    validation_pass = (
        target_count == 46
        and matched_count == 46
        and len(missing_targets) == 0
        and extra_match_count == 0
        and has_vba
    )

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01C1"
        ),
        "mode": (
            "DRY_RUN_READ_ONLY"
        ),
        "workbook_modified": False,

        "working_file": str(
            WORKING_FILE
        ),

        "summary": {
            "target_remove_count": (
                target_count
            ),
            "matched_target_count": (
                matched_count
            ),
            "missing_target_count": (
                len(
                    missing_targets
                )
            ),
            "extra_match_count": (
                extra_match_count
            ),
            "vml_shape_count_total": (
                len(
                    all_vml_shape_ids
                )
            ),
            "vba_present": (
                has_vba
            ),
            "vba_size_bytes": (
                vba_size
            ),
            "dryrun_pass": (
                validation_pass
            ),
        },

        "missing_targets": sorted(
            missing_targets
        ),

        "vml_report": (
            vml_report
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

    print(
        "\nKẾT QUẢ TỔNG HỢP"
    )

    print(
        f"Target REMOVE_CANDIDATE: "
        f"{target_count}"
    )

    print(
        f"Matched trong VML: "
        f"{matched_count}"
    )

    print(
        f"Missing target: "
        f"{len(missing_targets)}"
    )

    print(
        f"Extra match: "
        f"{extra_match_count}"
    )

    print(
        f"Tổng Shape ID trong VML: "
        f"{len(all_vml_shape_ids)}"
    )

    print(
        "VBA project tồn tại: "
        f"{'YES' if has_vba else 'NO'}"
    )

    if vba_size is not None:
        print(
            f"vbaProject.bin size: "
            f"{vba_size} bytes"
        )

    print(
        "\nPHÂN BỔ TARGET THEO VML"
    )

    for item in vml_report:
        if (
            item[
                "matched_target_count"
            ]
            > 0
        ):
            print(
                f"- {item['vml_path']} | "
                f"Targets="
                f"{item['matched_target_count']}"
            )

    if missing_targets:
        print(
            "\nSHAPE ID KHÔNG TÌM THẤY"
        )

        for shape_id in sorted(
            missing_targets
        ):
            print(
                f"- {shape_id}"
            )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        OUTPUT_FILE
    )

    if validation_pass:
        print(
            "\nKẾT QUẢ: "
            "CLEANUP TARGETS DRY-RUN ACCEPTED"
        )
    else:
        print(
            "\nKẾT QUẢ: "
            "CLEANUP TARGETS DRY-RUN FAILED"
        )

        raise RuntimeError(
            "Không được thực hiện cleanup "
            "vì target chưa ánh xạ chính xác."
        )


if __name__ == "__main__":
    main()