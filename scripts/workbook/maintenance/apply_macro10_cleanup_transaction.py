import hashlib
import json
import os
import posixpath
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORKING_FILE = Path(
    "data/working/LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

MANIFEST_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)

PLAN_FILE = Path(
    "output/reports/macro10_cleanup_transaction_plan.json"
)

BACKUP_DIR = Path(
    "data/backups"
)

REPORT_FILE = Path(
    "output/reports/macro10_cleanup_transaction_result.json"
)

TEMP_FILE = Path(
    "data/working/LBG-TUYEN_CLEANUP_TRANSACTION_TEMP.xlsm"
)

APPLY_CHANGES = False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def read_text(
    archive: zipfile.ZipFile,
    path: str,
) -> str:
    try:
        data = archive.read(
            path
        )
    except KeyError:
        return ""

    return data.decode(
        "utf-8",
        errors="replace",
    )


def relationship_path(
    source_part: str,
) -> str:
    folder = posixpath.dirname(
        source_part
    )

    filename = posixpath.basename(
        source_part
    )

    return posixpath.join(
        folder,
        "_rels",
        filename + ".rels",
    )


def remove_vml_shapes(
    text: str,
    target_shape_ids: set[str],
) -> tuple[str, int]:
    removed = 0

    for shape_id in sorted(
        target_shape_ids
    ):
        pattern = re.compile(
            r"<(?:\w+:)?shape\b"
            r'(?=[^>]*\bid\s*=\s*"'
            + re.escape(shape_id)
            + r'")'
            r"[^>]*>"
            r".*?"
            r"</(?:\w+:)?shape>",
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        text, count = pattern.subn(
            "",
            text,
            count=1,
        )

        removed += count

    return text, removed


def remove_worksheet_controls(
    xml_bytes: bytes,
    numeric_shape_ids: set[str],
) -> tuple[bytes, int, set[str]]:
    try:
        root = ET.fromstring(
            xml_bytes
        )
    except ET.ParseError as exc:
        raise RuntimeError(
            "Worksheet XML không parse được."
        ) from exc

    removed = 0
    removed_rids = set()

    relationship_attr = (
        "{http://schemas.openxmlformats.org/"
        "officeDocument/2006/relationships}id"
    )

    for parent in root.iter():
        for child in list(
            parent
        ):
            tag = child.tag.split(
                "}"
            )[-1]

            if tag != "control":
                continue

            shape_id = child.attrib.get(
                "shapeId"
            )

            if shape_id not in (
                numeric_shape_ids
            ):
                continue

            rid = child.attrib.get(
                relationship_attr
            )

            if rid:
                removed_rids.add(
                    rid
                )

            parent.remove(
                child
            )

            removed += 1

    return (
        ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
        ),
        removed,
        removed_rids,
    )


def remove_relationships(
    rels_bytes: bytes,
    target_rids: set[str],
) -> tuple[bytes, int, list[str]]:
    root = ET.fromstring(
        rels_bytes
    )

    removed = 0
    removed_targets = []

    for child in list(
        root
    ):
        rid = child.attrib.get(
            "Id"
        )

        if rid not in target_rids:
            continue

        target = child.attrib.get(
            "Target"
        )

        if target:
            removed_targets.append(
                target
            )

        root.remove(
            child
        )

        removed += 1

    return (
        ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
        ),
        removed,
        removed_targets,
    )


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


def extract_shape_ids(
    text: str,
) -> set[str]:
    return set(
        re.findall(
            r"<(?:\w+:)?shape\b"
            r'[^>]*\bid\s*=\s*"([^"]+)"',
            text,
            flags=re.IGNORECASE,
        )
    )


def count_buttons(
    archive: zipfile.ZipFile,
) -> int:
    total = 0

    for path in archive.namelist():
        if "vmlDrawing" not in path:
            continue

        text = read_text(
            archive,
            path,
        )

        total += len(
            re.findall(
                r'ObjectType\s*=\s*"Button"',
                text,
                flags=re.IGNORECASE,
            )
        )

    return total


def main() -> None:
    if not APPLY_CHANGES:
        print(
            "APPLY_CHANGES = False; "
            "không thay đổi workbook."
        )
        return

    if not WORKING_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy working file: "
            f"{WORKING_FILE}"
        )

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy manifest: "
            f"{MANIFEST_FILE}"
        )

    if not PLAN_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy transaction plan: "
            f"{PLAN_FILE}"
        )

    manifest = json.loads(
        MANIFEST_FILE.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    plan = json.loads(
        PLAN_FILE.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    if not plan.get(
        "summary",
        {},
    ).get(
        "transaction_plan_valid"
    ):
        raise RuntimeError(
            "Transaction plan chưa VALIDATED."
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

    keep_items = [
        item
        for item in manifest.get(
            "items",
            [],
        )
        if item.get(
            "decision"
        )
        == "KEEP"
    ]

    remove_shape_ids = {
        item["shape_id"]
        for item in remove_items
    }

    keep_shape_ids = {
        item["shape_id"]
        for item in keep_items
    }

    if len(
        remove_shape_ids
    ) != 46:
        raise RuntimeError(
            "Expected 46 REMOVE_CANDIDATE."
        )

    numeric_remove_ids = {
        re.search(
            r"(\d+)$",
            shape_id,
        ).group(1)
        for shape_id in remove_shape_ids
    }

    working_hash_before = (
        sha256_file(
            WORKING_FILE
        )
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_before = (
        BACKUP_DIR
        / "LBG-TUYEN_CLEANUP_BEFORE_MACRO10.xlsm"
    )

    if not backup_before.exists():
        shutil.copy2(
            WORKING_FILE,
            backup_before,
        )

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    # ========================================================
    # READ ORIGINAL PACKAGE
    # ========================================================

    with zipfile.ZipFile(
        WORKING_FILE,
        "r",
    ) as source_zip:
        names = source_zip.namelist()

        if (
            "xl/vbaProject.bin"
            not in names
        ):
            raise RuntimeError(
                "Không tìm thấy vbaProject.bin."
            )

        vba_before = source_zip.read(
            "xl/vbaProject.bin"
        )

        vba_hash_before = sha256_bytes(
            vba_before
        )

        buttons_before = count_buttons(
            source_zip
        )

        modified_parts = {}

        delete_parts = set()

        vml_removed_total = 0

        worksheet_removed_total = 0

        relationship_removed_total = 0

        resolved_control_parts = set()

        # ----------------------------------------------------
        # 1. VML
        # ----------------------------------------------------

        for path in names:
            if "vmlDrawing" not in path:
                continue

            original_text = read_text(
                source_zip,
                path,
            )

            new_text, removed = (
                remove_vml_shapes(
                    original_text,
                    remove_shape_ids,
                )
            )

            if removed:
                modified_parts[
                    path
                ] = new_text.encode(
                    "utf-8"
                )

                vml_removed_total += (
                    removed
                )

        # ----------------------------------------------------
        # 2. WORKSHEET CONTROL + RELATIONSHIPS
        # ----------------------------------------------------

        for worksheet_path in names:
            if not (
                worksheet_path.startswith(
                    "xl/worksheets/"
                )
                and worksheet_path.endswith(
                    ".xml"
                )
            ):
                continue

            xml_bytes = source_zip.read(
                worksheet_path
            )

            (
                new_xml,
                removed_count,
                removed_rids,
            ) = remove_worksheet_controls(
                xml_bytes,
                numeric_remove_ids,
            )

            if removed_count == 0:
                continue

            modified_parts[
                worksheet_path
            ] = new_xml

            worksheet_removed_total += (
                removed_count
            )

            rels_path = (
                relationship_path(
                    worksheet_path
                )
            )

            if (
                rels_path
                not in names
            ):
                raise RuntimeError(
                    f"Thiếu rels: {rels_path}"
                )

            rels_bytes = source_zip.read(
                rels_path
            )

            (
                new_rels,
                rel_removed,
                removed_targets,
            ) = remove_relationships(
                rels_bytes,
                removed_rids,
            )

            if rel_removed != len(
                removed_rids
            ):
                raise RuntimeError(
                    "Số relationship xóa "
                    "không khớp control."
                )

            modified_parts[
                rels_path
            ] = new_rels

            relationship_removed_total += (
                rel_removed
            )

            for target in (
                removed_targets
            ):
                control_part = (
                    normalize_target(
                        worksheet_path,
                        target,
                    )
                )

                resolved_control_parts.add(
                    control_part
                )

                delete_parts.add(
                    control_part
                )

        if len(
            resolved_control_parts
        ) != 46:
            raise RuntimeError(
                "Không resolve đúng 46 "
                "control parts."
            )

        # ----------------------------------------------------
        # FAIL CLOSED BEFORE WRITING TEMP
        # ----------------------------------------------------

        if vml_removed_total != 46:
            raise RuntimeError(
                f"VML removed = "
                f"{vml_removed_total}, "
                "expected 46."
            )

        if (
            worksheet_removed_total
            != 46
        ):
            raise RuntimeError(
                f"Worksheet controls removed = "
                f"{worksheet_removed_total}, "
                "expected 46."
            )

        if (
            relationship_removed_total
            != 46
        ):
            raise RuntimeError(
                f"Relationships removed = "
                f"{relationship_removed_total}, "
                "expected 46."
            )

        # ----------------------------------------------------
        # WRITE TEMP PACKAGE
        # ----------------------------------------------------

        with zipfile.ZipFile(
            TEMP_FILE,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as target_zip:
            for info in source_zip.infolist():
                path = info.filename

                if path in delete_parts:
                    continue

                if path in modified_parts:
                    data = modified_parts[
                        path
                    ]
                else:
                    data = source_zip.read(
                        path
                    )

                target_zip.writestr(
                    info,
                    data,
                )

    # ========================================================
    # VALIDATE TEMP
    # ========================================================

    with zipfile.ZipFile(
        TEMP_FILE,
        "r",
    ) as temp_zip:
        bad_entry = temp_zip.testzip()

        if bad_entry is not None:
            raise RuntimeError(
                f"ZIP integrity FAIL: "
                f"{bad_entry}"
            )

        if (
            "xl/vbaProject.bin"
            not in temp_zip.namelist()
        ):
            raise RuntimeError(
                "TEMP mất vbaProject.bin."
            )

        vba_after = temp_zip.read(
            "xl/vbaProject.bin"
        )

        vba_hash_after = (
            sha256_bytes(
                vba_after
            )
        )

        if (
            vba_hash_after
            != vba_hash_before
        ):
            raise RuntimeError(
                "VBA SHA256 thay đổi."
            )

        buttons_after = (
            count_buttons(
                temp_zip
            )
        )

        if buttons_before != 120:
            raise RuntimeError(
                f"Button baseline không phải 120: "
                f"{buttons_before}"
            )

        if buttons_after != 74:
            raise RuntimeError(
                f"Button sau cleanup không phải 74: "
                f"{buttons_after}"
            )

        remaining_shape_ids = set()

        for path in temp_zip.namelist():
            if "vmlDrawing" not in path:
                continue

            remaining_shape_ids.update(
                extract_shape_ids(
                    read_text(
                        temp_zip,
                        path,
                    )
                )
            )

        remove_survivors = (
            remove_shape_ids
            & remaining_shape_ids
        )

        missing_keep = (
            keep_shape_ids
            - remaining_shape_ids
        )

        if remove_survivors:
            raise RuntimeError(
                "Vẫn còn REMOVE shape sau cleanup."
            )

        if missing_keep:
            raise RuntimeError(
                "Có KEEP shape bị mất."
            )

    # ========================================================
    # ACCEPT TRANSACTION
    # ========================================================

    shutil.move(
        str(TEMP_FILE),
        str(WORKING_FILE),
    )

    working_hash_after = (
        sha256_file(
            WORKING_FILE
        )
    )

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01C2B"
        ),
        "working_file": str(
            WORKING_FILE
        ),
        "backup_before": str(
            backup_before
        ),
        "summary": {
            "vml_removed": (
                vml_removed_total
            ),
            "worksheet_controls_removed": (
                worksheet_removed_total
            ),
            "relationships_removed": (
                relationship_removed_total
            ),
            "control_parts_removed": (
                len(
                    resolved_control_parts
                )
            ),
            "buttons_before": (
                buttons_before
            ),
            "buttons_after": (
                buttons_after
            ),
            "keep_survived": (
                len(
                    keep_shape_ids
                )
            ),
            "remove_survived": (
                0
            ),
            "zip_integrity": (
                "PASS"
            ),
            "vba_sha256_preserved": (
                True
            ),
        },
        "hashes": {
            "working_before": (
                working_hash_before
            ),
            "working_after": (
                working_hash_after
            ),
            "vba_before": (
                vba_hash_before
            ),
            "vba_after": (
                vba_hash_after
            ),
        },
        "transaction_accepted": (
            True
        ),
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01C2B - "
        "MACRO10 CLEANUP TRANSACTION"
    )
    print("=" * 72)

    print(
        "VML Shape removed: "
        f"{vml_removed_total}"
    )

    print(
        "Worksheet control removed: "
        f"{worksheet_removed_total}"
    )

    print(
        "Relationship removed: "
        f"{relationship_removed_total}"
    )

    print(
        "Control parts removed: "
        f"{len(resolved_control_parts)}"
    )

    print(
        "\nBUTTON COUNTS"
    )

    print(
        f"Before: {buttons_before}"
    )

    print(
        f"After:  {buttons_after}"
    )

    print(
        "\nKEEP / REMOVE CHECK"
    )

    print(
        f"KEEP survived: "
        f"{len(keep_shape_ids)}/"
        f"{len(keep_shape_ids)}"
    )

    print(
        "REMOVE survived: 0/46"
    )

    print(
        "\nZIP integrity: PASS"
    )

    print(
        "VBA SHA256 preserved: PASS"
    )

    print(
        "\nBackup trước cleanup:"
    )

    print(
        backup_before
    )

    print(
        "\nĐã tạo báo cáo:"
    )

    print(
        REPORT_FILE
    )

    print(
        "\nKẾT QUẢ: "
        "CLEANUP TRANSACTION ACCEPTED"
    )


if __name__ == "__main__":
    main()
