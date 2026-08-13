import hashlib
import json
import posixpath
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


SOURCE_BACKUP = Path(
    "data/backups/LBG-TUYEN_CLEANUP_BEFORE_MACRO10.xlsm"
)

SAFE_WORKING = Path(
    "data/working/LBG-TUYEN_CLEANUP_SAFE_WORKING.xlsm"
)

TEMP_FILE = Path(
    "data/working/LBG-TUYEN_CLEANUP_SAFE_TEMP.xlsm"
)

MANIFEST_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)

REPORT_FILE = Path(
    "output/reports/macro10_cleanup_safe_retry_v3_result.json"
)


EXPECTED_REMOVE = 46
EXPECTED_KEEP = 24
EXPECTED_BUTTON_BEFORE = 120
EXPECTED_BUTTON_AFTER = 74
EXPECTED_SHEET5_CONTROLS_BEFORE = 119
EXPECTED_SHEET5_CONTROLS_AFTER = 73

APPLY_CHANGES = False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_text(
    archive: zipfile.ZipFile,
    path: str,
) -> str:
    return archive.read(path).decode(
        "utf-8",
        errors="strict",
    )


def numeric_shape_id(
    shape_id: str,
) -> str:
    match = re.search(
        r"(\d+)$",
        shape_id or "",
    )

    if not match:
        raise RuntimeError(
            f"Không lấy được numeric shapeId: {shape_id}"
        )

    return match.group(1)


def relationship_path(
    source_part: str,
) -> str:
    folder = posixpath.dirname(source_part)
    filename = posixpath.basename(source_part)

    return posixpath.join(
        folder,
        "_rels",
        filename + ".rels",
    )


def normalize_target(
    source_part: str,
    target: str,
) -> str:
    if target.startswith("/"):
        return target.lstrip("/")

    return posixpath.normpath(
        posixpath.join(
            posixpath.dirname(source_part),
            target,
        )
    ).lstrip("/")


def worksheet_open_tag(
    text: str,
) -> str:
    match = re.search(
        r"<worksheet\b[^>]*>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "Không tìm thấy thẻ mở <worksheet>."
        )

    return match.group(0)


def get_control_shape_ids(
    worksheet_text: str,
) -> list[str]:
    return re.findall(
        r'<control\b[^>]*\bshapeId="([^"]+)"',
        worksheet_text,
        flags=re.IGNORECASE,
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


def collect_vml_shape_ids(
    archive: zipfile.ZipFile,
) -> set[str]:
    result = set()

    for path in archive.namelist():
        if "vmlDrawing" not in path:
            continue

        text = read_text(
            archive,
            path,
        )

        result.update(
            re.findall(
                r"<(?:\w+:)?shape\b"
                r'[^>]*\bid\s*=\s*"([^"]+)"',
                text,
                flags=re.IGNORECASE,
            )
        )

    return result


def find_vml_target_locations(
    archive: zipfile.ZipFile,
    target_shape_ids: set[str],
) -> dict[str, list[str]]:
    result = {
        shape_id: []
        for shape_id in target_shape_ids
    }

    for path in archive.namelist():
        if "vmlDrawing" not in path:
            continue

        text = read_text(
            archive,
            path,
        )

        for shape_id in target_shape_ids:
            pattern = re.compile(
                r"<(?:\w+:)?shape\b"
                r'(?=[^>]*\bid\s*=\s*"'
                + re.escape(shape_id)
                + r'")',
                flags=re.IGNORECASE,
            )

            if pattern.search(text):
                result[shape_id].append(path)

    return result


def remove_vml_shapes(
    text: str,
    shape_ids: set[str],
) -> tuple[str, int]:
    removed = 0

    for shape_id in sorted(shape_ids):
        pattern = re.compile(
            r"<(?:\w+:)?shape\b"
            r'(?=[^>]*\bid\s*=\s*"'
            + re.escape(shape_id)
            + r'")'
            r"[^>]*>"
            r".*?"
            r"</(?:\w+:)?shape>",
            flags=re.IGNORECASE | re.DOTALL,
        )

        text, count = pattern.subn(
            "",
            text,
            count=1,
        )

        if count != 1:
            raise RuntimeError(
                f"VML shape {shape_id}: "
                f"removed={count}, expected 1."
            )

        removed += 1

    return text, removed


def extract_alternate_content_blocks(
    worksheet_text: str,
) -> list[str]:
    pattern = re.compile(
        r"<(?:\w+:)?AlternateContent\b"
        r".*?"
        r"</(?:\w+:)?AlternateContent>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    return pattern.findall(
        worksheet_text
    )


def extract_control_from_block(
    block: str,
) -> tuple[str | None, str | None]:
    control_match = re.search(
        r"<control\b[^>]*>",
        block,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not control_match:
        return None, None

    control_tag = control_match.group(0)

    shape_match = re.search(
        r'\bshapeId\s*=\s*"([^"]+)"',
        control_tag,
        flags=re.IGNORECASE,
    )

    rid_match = re.search(
        r'\br:id\s*=\s*"([^"]+)"',
        control_tag,
        flags=re.IGNORECASE,
    )

    shape_id = (
        shape_match.group(1)
        if shape_match
        else None
    )

    rid = (
        rid_match.group(1)
        if rid_match
        else None
    )

    return shape_id, rid


def remove_target_alternate_content(
    worksheet_text: str,
    remove_numeric_ids: set[str],
) -> tuple[str, int, set[str]]:
    blocks = extract_alternate_content_blocks(
        worksheet_text
    )

    removed = 0
    removed_rids = set()
    removed_shape_ids = set()

    for block in blocks:
        shape_id, rid = (
            extract_control_from_block(
                block
            )
        )

        if shape_id not in remove_numeric_ids:
            continue

        if not rid:
            raise RuntimeError(
                f"Control shapeId={shape_id} "
                "không có r:id."
            )

        if shape_id in removed_shape_ids:
            raise RuntimeError(
                f"shapeId bị lặp trong worksheet: "
                f"{shape_id}"
            )

        worksheet_text = worksheet_text.replace(
            block,
            "",
            1,
        )

        removed += 1
        removed_rids.add(rid)
        removed_shape_ids.add(shape_id)

    missing = (
        remove_numeric_ids
        - removed_shape_ids
    )

    if missing:
        raise RuntimeError(
            "Không tìm thấy đủ REMOVE "
            "AlternateContent trong worksheet: "
            f"{sorted(missing)[:10]}"
        )

    return (
        worksheet_text,
        removed,
        removed_rids,
    )


def remove_relationships_textually(
    rels_text: str,
    target_rids: set[str],
) -> tuple[str, int, list[str]]:
    pattern = re.compile(
        r"<Relationship\b[^>]*/>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    removed = 0
    removed_targets = []
    found_rids = set()

    for element in pattern.findall(
        rels_text
    ):
        rid_match = re.search(
            r'\bId\s*=\s*"([^"]+)"',
            element,
            flags=re.IGNORECASE,
        )

        if not rid_match:
            continue

        rid = rid_match.group(1)

        if rid not in target_rids:
            continue

        target_match = re.search(
            r'\bTarget\s*=\s*"([^"]+)"',
            element,
            flags=re.IGNORECASE,
        )

        if not target_match:
            raise RuntimeError(
                f"Relationship {rid} "
                "không có Target."
            )

        target = target_match.group(1)

        rels_text = rels_text.replace(
            element,
            "",
            1,
        )

        removed += 1
        found_rids.add(rid)
        removed_targets.append(target)

    missing_rids = (
        target_rids
        - found_rids
    )

    if missing_rids:
        raise RuntimeError(
            "Không tìm thấy relationship: "
            f"{sorted(missing_rids)[:10]}"
        )

    return (
        rels_text,
        removed,
        removed_targets,
    )


def remove_content_type_overrides(
    content_types_text: str,
    delete_parts: set[str],
) -> tuple[str, int]:
    removed = 0

    pattern = re.compile(
        r"<Override\b[^>]*/>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    delete_part_names = {
        "/" + part.lstrip("/")
        for part in delete_parts
    }

    for element in pattern.findall(
        content_types_text
    ):
        part_match = re.search(
            r'\bPartName\s*=\s*"([^"]+)"',
            element,
            flags=re.IGNORECASE,
        )

        if not part_match:
            continue

        part_name = part_match.group(1)

        if part_name not in delete_part_names:
            continue

        content_types_text = (
            content_types_text.replace(
                element,
                "",
                1,
            )
        )

        removed += 1

    return (
        content_types_text,
        removed,
    )


def find_missing_relationship_targets(
    archive: zipfile.ZipFile,
) -> list[dict]:
    names = set(
        archive.namelist()
    )

    missing = []

    for rels_path in names:
        if not rels_path.endswith(
            ".rels"
        ):
            continue

        if rels_path == "_rels/.rels":
            source_part = ""

        elif "/_rels/" in rels_path:
            folder, filename = (
                rels_path.split(
                    "/_rels/",
                    1,
                )
            )

            if not filename.endswith(
                ".rels"
            ):
                continue

            source_part = posixpath.join(
                folder,
                filename[:-5],
            )

        else:
            continue

        try:
            root = ET.fromstring(
                archive.read(
                    rels_path
                )
            )
        except ET.ParseError:
            missing.append(
                {
                    "rels": rels_path,
                    "reason": (
                        "XML_PARSE_ERROR"
                    ),
                }
            )
            continue

        for relationship in root:
            target = (
                relationship.attrib.get(
                    "Target"
                )
            )

            target_mode = (
                relationship.attrib.get(
                    "TargetMode"
                )
            )

            if not target:
                continue

            if target_mode == "External":
                continue

            if source_part == "":
                resolved = target.lstrip("/")
            else:
                resolved = normalize_target(
                    source_part,
                    target,
                )

            if resolved not in names:
                missing.append(
                    {
                        "rels": rels_path,
                        "id": (
                            relationship.attrib.get(
                                "Id"
                            )
                        ),
                        "target": resolved,
                    }
                )

    return missing


def main() -> None:
    print("=" * 72)
    print(
        "M5-XLS-CLEANUP-01F3 - "
        "SAFE MACRO10 CLEANUP RETRY V3"
    )
    print("=" * 72)

    if not APPLY_CHANGES:
        print(
            "APPLY_CHANGES = False; "
            "không tạo hoặc thay đổi working copy."
        )
        return

    if not SOURCE_BACKUP.exists():
        raise FileNotFoundError(
            f"Không tìm thấy backup: "
            f"{SOURCE_BACKUP}"
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

    items = manifest.get(
        "items",
        [],
    )

    keep_items = [
        item
        for item in items
        if item.get("decision")
        == "KEEP"
    ]

    remove_items = [
        item
        for item in items
        if item.get("decision")
        == "REMOVE_CANDIDATE"
    ]

    keep_shape_ids = {
        item["shape_id"]
        for item in keep_items
    }

    remove_shape_ids = {
        item["shape_id"]
        for item in remove_items
    }

    if len(keep_shape_ids) != EXPECTED_KEEP:
        raise RuntimeError(
            "KEEP count không phải 24."
        )

    if len(remove_shape_ids) != EXPECTED_REMOVE:
        raise RuntimeError(
            "REMOVE count không phải 46."
        )

    if keep_shape_ids & remove_shape_ids:
        raise RuntimeError(
            "KEEP và REMOVE bị overlap."
        )

    keep_numeric_ids = {
        numeric_shape_id(shape_id)
        for shape_id in keep_shape_ids
    }

    remove_numeric_ids = {
        numeric_shape_id(shape_id)
        for shape_id in remove_shape_ids
    }

    if SAFE_WORKING.exists():
        SAFE_WORKING.unlink()

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    shutil.copy2(
        SOURCE_BACKUP,
        SAFE_WORKING,
    )

    source_sha256 = sha256_file(
        SAFE_WORKING
    )

    with zipfile.ZipFile(
        SAFE_WORKING,
        "r",
    ) as source_zip:

        names = source_zip.namelist()

        if (
            "xl/vbaProject.bin"
            not in names
        ):
            raise RuntimeError(
                "Không có vbaProject.bin."
            )

        vba_before = source_zip.read(
            "xl/vbaProject.bin"
        )

        vba_sha256_before = (
            sha256_bytes(
                vba_before
            )
        )

        buttons_before = count_buttons(
            source_zip
        )

        if (
            buttons_before
            != EXPECTED_BUTTON_BEFORE
        ):
            raise RuntimeError(
                f"Button before="
                f"{buttons_before}, "
                "expected 120."
            )

        sheet5_original = read_text(
            source_zip,
            "xl/worksheets/sheet5.xml",
        )

        sheet5_open_tag_before = (
            worksheet_open_tag(
                sheet5_original
            )
        )

        sheet5_control_ids_before = (
            get_control_shape_ids(
                sheet5_original
            )
        )

        if (
            len(sheet5_control_ids_before)
            != EXPECTED_SHEET5_CONTROLS_BEFORE
        ):
            raise RuntimeError(
                "sheet5 control count trước "
                f"cleanup={len(sheet5_control_ids_before)}, "
                "expected 119."
            )

        if not remove_numeric_ids.issubset(
            set(sheet5_control_ids_before)
        ):
            raise RuntimeError(
                "REMOVE không ánh xạ đủ vào sheet5."
            )

        if not keep_numeric_ids.issubset(
            set(sheet5_control_ids_before)
        ):
            raise RuntimeError(
                "KEEP không ánh xạ đủ vào sheet5."
            )

        target_locations = (
            find_vml_target_locations(
                source_zip,
                remove_shape_ids,
            )
        )

        missing_vml = [
            shape_id
            for shape_id, paths
            in target_locations.items()
            if len(paths) == 0
        ]

        duplicate_vml = [
            shape_id
            for shape_id, paths
            in target_locations.items()
            if len(paths) > 1
        ]

        if missing_vml:
            raise RuntimeError(
                f"VML target missing: "
                f"{missing_vml[:10]}"
            )

        if duplicate_vml:
            raise RuntimeError(
                f"VML target duplicated: "
                f"{duplicate_vml[:10]}"
            )

        targets_by_vml = defaultdict(
            set
        )

        for shape_id, paths in (
            target_locations.items()
        ):
            targets_by_vml[
                paths[0]
            ].add(
                shape_id
            )

        print()
        print("VML TARGET MAP")

        for path, ids in sorted(
            targets_by_vml.items()
        ):
            print(
                f"- {path}: "
                f"{len(ids)} targets"
            )

        modified_parts = {}
        delete_parts = set()

        vml_removed = 0

        for path, ids in (
            targets_by_vml.items()
        ):
            original_text = read_text(
                source_zip,
                path,
            )

            new_text, count = (
                remove_vml_shapes(
                    original_text,
                    ids,
                )
            )

            modified_parts[
                path
            ] = new_text.encode(
                "utf-8"
            )

            vml_removed += count

        if vml_removed != EXPECTED_REMOVE:
            raise RuntimeError(
                f"VML removed={vml_removed}, "
                "expected 46."
            )

        (
            sheet5_new,
            worksheet_removed,
            removed_rids,
        ) = remove_target_alternate_content(
            sheet5_original,
            remove_numeric_ids,
        )

        if (
            worksheet_removed
            != EXPECTED_REMOVE
        ):
            raise RuntimeError(
                "Worksheet controls removed="
                f"{worksheet_removed}, "
                "expected 46."
            )

        if len(removed_rids) != EXPECTED_REMOVE:
            raise RuntimeError(
                "Worksheet rId count "
                "không phải 46."
            )

        if (
            worksheet_open_tag(
                sheet5_new
            )
            != sheet5_open_tag_before
        ):
            raise RuntimeError(
                "sheet5 namespace/opening tag "
                "đã thay đổi."
            )

        if "<ns0:worksheet" in sheet5_new:
            raise RuntimeError(
                "Phát hiện namespace ns0."
            )

        sheet5_after_ids = (
            get_control_shape_ids(
                sheet5_new
            )
        )

        if (
            len(sheet5_after_ids)
            != EXPECTED_SHEET5_CONTROLS_AFTER
        ):
            raise RuntimeError(
                "sheet5 controls after="
                f"{len(sheet5_after_ids)}, "
                "expected 73."
            )

        sheet5_after_set = set(
            sheet5_after_ids
        )

        if remove_numeric_ids & (
            sheet5_after_set
        ):
            raise RuntimeError(
                "Vẫn còn REMOVE control "
                "trong sheet5."
            )

        if not keep_numeric_ids.issubset(
            sheet5_after_set
        ):
            raise RuntimeError(
                "Có KEEP control bị mất "
                "khỏi sheet5."
            )

        modified_parts[
            "xl/worksheets/sheet5.xml"
        ] = sheet5_new.encode(
            "utf-8"
        )

        sheet5_rels_path = (
            relationship_path(
                "xl/worksheets/sheet5.xml"
            )
        )

        rels_original = read_text(
            source_zip,
            sheet5_rels_path,
        )

        (
            rels_new,
            relationships_removed,
            removed_targets,
        ) = remove_relationships_textually(
            rels_original,
            removed_rids,
        )

        if (
            relationships_removed
            != EXPECTED_REMOVE
        ):
            raise RuntimeError(
                "Relationships removed="
                f"{relationships_removed}, "
                "expected 46."
            )

        modified_parts[
            sheet5_rels_path
        ] = rels_new.encode(
            "utf-8"
        )

        for target in removed_targets:
            part = normalize_target(
                "xl/worksheets/sheet5.xml",
                target,
            )

            if part not in names:
                raise RuntimeError(
                    f"Relationship target "
                    f"không tồn tại: {part}"
                )

            delete_parts.add(part)

        if len(delete_parts) != EXPECTED_REMOVE:
            raise RuntimeError(
                "Unique control/ctrlProp "
                f"parts={len(delete_parts)}, "
                "expected 46."
            )

        content_types_path = (
            "[Content_Types].xml"
        )

        content_types_original = (
            read_text(
                source_zip,
                content_types_path,
            )
        )

        (
            content_types_new,
            content_type_removed,
        ) = remove_content_type_overrides(
            content_types_original,
            delete_parts,
        )

        modified_parts[
            content_types_path
        ] = content_types_new.encode(
            "utf-8"
        )

        print()
        print(
            "CONTENT TYPE OVERRIDES REMOVED:",
            content_type_removed,
        )

        with zipfile.ZipFile(
            TEMP_FILE,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as target_zip:

            for info in (
                source_zip.infolist()
            ):
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

        vba_sha256_after = (
            sha256_bytes(
                vba_after
            )
        )

        if (
            vba_sha256_after
            != vba_sha256_before
        ):
            raise RuntimeError(
                "VBA SHA256 thay đổi."
            )

        buttons_after = count_buttons(
            temp_zip
        )

        if (
            buttons_after
            != EXPECTED_BUTTON_AFTER
        ):
            raise RuntimeError(
                f"Button after="
                f"{buttons_after}, "
                "expected 74."
            )

        remaining_vml_ids = (
            collect_vml_shape_ids(
                temp_zip
            )
        )

        if remove_shape_ids & (
            remaining_vml_ids
        ):
            raise RuntimeError(
                "Vẫn còn REMOVE VML shape."
            )

        if not keep_shape_ids.issubset(
            remaining_vml_ids
        ):
            raise RuntimeError(
                "Có KEEP VML shape bị mất."
            )

        sheet5_temp = read_text(
            temp_zip,
            "xl/worksheets/sheet5.xml",
        )

        if (
            worksheet_open_tag(
                sheet5_temp
            )
            != sheet5_open_tag_before
        ):
            raise RuntimeError(
                "sheet5 opening tag "
                "không được bảo toàn."
            )

        if "<ns0:worksheet" in sheet5_temp:
            raise RuntimeError(
                "sheet5 bị namespace rewrite."
            )

        final_sheet5_ids = set(
            get_control_shape_ids(
                sheet5_temp
            )
        )

        if remove_numeric_ids & (
            final_sheet5_ids
        ):
            raise RuntimeError(
                "REMOVE vẫn còn trong "
                "worksheet."
            )

        if not keep_numeric_ids.issubset(
            final_sheet5_ids
        ):
            raise RuntimeError(
                "KEEP không còn đủ "
                "trong worksheet."
            )

        names_after = set(
            temp_zip.namelist()
        )

        surviving_deleted_parts = (
            delete_parts
            & names_after
        )

        if surviving_deleted_parts:
            raise RuntimeError(
                "Control/ctrlProp part "
                "vẫn còn sau delete."
            )

        missing_rel_targets = (
            find_missing_relationship_targets(
                temp_zip
            )
        )

        if missing_rel_targets:
            raise RuntimeError(
                "Có relationship target "
                "bị mồ côi: "
                f"{missing_rel_targets[:5]}"
            )

        content_types_after = read_text(
            temp_zip,
            "[Content_Types].xml",
        )

        stale_content_types = [
            part
            for part in delete_parts
            if (
                "/" + part
            ) in content_types_after
        ]

        if stale_content_types:
            raise RuntimeError(
                "Còn Content-Type reference "
                "tới part đã xóa."
            )

        control_related_parts = [
            path
            for path in names_after
            if (
                path.startswith(
                    "xl/controls/"
                )
                or path.startswith(
                    "xl/ctrlProps/"
                )
            )
            and not path.endswith(
                ".rels"
            )
        ]

        if len(
            control_related_parts
        ) != 74:
            raise RuntimeError(
                "Control/Prop parts after="
                f"{len(control_related_parts)}, "
                "expected 74."
            )

        with zipfile.ZipFile(
            SOURCE_BACKUP,
            "r",
        ) as baseline_zip:

            for path in (
                baseline_zip.namelist()
            ):
                if "vmlDrawing" not in path:
                    continue

                if path in targets_by_vml:
                    continue

                if (
                    baseline_zip.read(path)
                    != temp_zip.read(path)
                ):
                    raise RuntimeError(
                        "VML không có target "
                        f"bị thay đổi: {path}"
                    )

    shutil.move(
        str(TEMP_FILE),
        str(SAFE_WORKING),
    )

    final_sha256 = sha256_file(
        SAFE_WORKING
    )

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01F3"
        ),
        "source_backup": str(
            SOURCE_BACKUP
        ),
        "safe_working": str(
            SAFE_WORKING
        ),
        "source_sha256": (
            source_sha256
        ),
        "safe_working_sha256": (
            final_sha256
        ),
        "summary": {
            "manifest_keep": 24,
            "manifest_remove": 46,
            "vml_removed": (
                vml_removed
            ),
            "worksheet_controls_removed": (
                worksheet_removed
            ),
            "relationships_removed": (
                relationships_removed
            ),
            "parts_removed": (
                len(delete_parts)
            ),
            "content_type_overrides_removed": (
                content_type_removed
            ),
            "buttons_before": (
                buttons_before
            ),
            "buttons_after": (
                buttons_after
            ),
            "sheet5_controls_before": (
                len(
                    sheet5_control_ids_before
                )
            ),
            "sheet5_controls_after": (
                len(
                    final_sheet5_ids
                )
            ),
            "keep_vml_survived": 24,
            "remove_vml_survived": 0,
            "keep_worksheet_survived": 24,
            "remove_worksheet_survived": 0,
            "control_related_parts_after": (
                len(
                    control_related_parts
                )
            ),
            "missing_relationship_targets": 0,
            "vba_sha256_preserved": True,
            "sheet5_namespace_preserved": True,
            "zip_integrity": "PASS",
        },
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

    print()
    print("=" * 72)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 72)

    print(
        f"Manifest KEEP:              "
        f"{len(keep_shape_ids)}"
    )

    print(
        f"Manifest REMOVE:            "
        f"{len(remove_shape_ids)}"
    )

    print(
        f"VML Shape removed:          "
        f"{vml_removed}"
    )

    print(
        f"Worksheet control removed:  "
        f"{worksheet_removed}"
    )

    print(
        f"Relationships removed:      "
        f"{relationships_removed}"
    )

    print(
        f"Control/Prop parts removed: "
        f"{len(delete_parts)}"
    )

    print()
    print(
        f"Button before:              "
        f"{buttons_before}"
    )

    print(
        f"Button after:               "
        f"{buttons_after}"
    )

    print(
        f"sheet5 controls before:     "
        f"{len(sheet5_control_ids_before)}"
    )

    print(
        f"sheet5 controls after:      "
        f"{len(final_sheet5_ids)}"
    )

    print()
    print(
        "KEEP VML survived:         24/24"
    )

    print(
        "REMOVE VML survived:        0/46"
    )

    print(
        "KEEP Worksheet survived:   24/24"
    )

    print(
        "REMOVE Worksheet survived:  0/46"
    )

    print()
    print(
        "Control/Prop parts after:   "
        f"{len(control_related_parts)}"
    )

    print(
        "Missing relationship target: 0"
    )

    print(
        "VBA SHA256 preserved:       PASS"
    )

    print(
        "sheet5 namespace preserved: PASS"
    )

    print(
        "ZIP integrity:              PASS"
    )

    print()
    print(
        "Safe working copy:"
    )

    print(
        SAFE_WORKING
    )

    print()
    print(
        "Đã tạo báo cáo:"
    )

    print(
        REPORT_FILE
    )

    print()
    print(
        "KẾT QUẢ: "
        "SAFE CLEANUP RETRY V3 ACCEPTED"
    )


if __name__ == "__main__":
    main()
