import json
import posixpath
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


WORKING_FILE = Path(
    "data/working/LBG-TUYEN_CLEANUP_WORKING.xlsm"
)

MANIFEST_FILE = Path(
    "output/reports/macro10_button_cleanup_manifest.json"
)

OUTPUT_FILE = Path(
    "output/reports/macro10_cleanup_transaction_plan.json"
)


# ============================================================
# XML namespaces
# ============================================================

REL_NS = {
    "pkg": (
        "http://schemas.openxmlformats.org/"
        "package/2006/relationships"
    )
}


# ============================================================
# BASIC HELPERS
# ============================================================

def read_bytes(
    archive: zipfile.ZipFile,
    path: str,
) -> bytes:
    try:
        return archive.read(path)
    except KeyError:
        return b""


def read_text(
    archive: zipfile.ZipFile,
    path: str,
) -> str:
    data = read_bytes(
        archive,
        path,
    )

    if not data:
        return ""

    return data.decode(
        "utf-8",
        errors="replace",
    )


def normalize_rel_target(
    source_part: str,
    target: str,
) -> str:
    """Resolve relationship target thành package path."""

    if target.startswith("/"):
        return target.lstrip("/")

    source_dir = posixpath.dirname(
        source_part
    )

    resolved = posixpath.normpath(
        posixpath.join(
            source_dir,
            target,
        )
    )

    return resolved.lstrip("/")


def relationship_path(
    source_part: str,
) -> str:
    """Từ xl/worksheets/sheet1.xml
    -> xl/worksheets/_rels/sheet1.xml.rels
    """

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


def read_relationships(
    archive: zipfile.ZipFile,
    source_part: str,
) -> dict[str, dict]:
    rel_path = relationship_path(
        source_part
    )

    data = read_bytes(
        archive,
        rel_path,
    )

    if not data:
        return {}

    try:
        root = ET.fromstring(
            data
        )
    except ET.ParseError:
        return {}

    result = {}

    for rel in root:
        rel_id = rel.attrib.get(
            "Id"
        )

        target = rel.attrib.get(
            "Target"
        )

        rel_type = rel.attrib.get(
            "Type"
        )

        target_mode = rel.attrib.get(
            "TargetMode"
        )

        if not rel_id or not target:
            continue

        if target_mode == "External":
            resolved = target
        else:
            resolved = normalize_rel_target(
                source_part,
                target,
            )

        result[rel_id] = {
            "target": resolved,
            "type": rel_type,
            "target_mode": target_mode,
            "rels_path": rel_path,
        }

    return result


def shape_numeric_id(
    shape_id: str,
) -> str | None:
    """_x0000_s3581145 -> 3581145"""

    match = re.search(
        r"(\d+)$",
        shape_id or "",
    )

    if not match:
        return None

    return match.group(1)


# ============================================================
# VML
# ============================================================

def find_shape_vml_occurrences(
    archive: zipfile.ZipFile,
    shape_id: str,
) -> list[str]:
    occurrences = []

    for path in archive.namelist():
        if "vmlDrawing" not in path:
            continue

        text = read_text(
            archive,
            path,
        )

        pattern = re.compile(
            rf'\bid\s*=\s*"{re.escape(shape_id)}"',
            flags=re.IGNORECASE,
        )

        if pattern.search(text):
            occurrences.append(
                path
            )

    return occurrences


# ============================================================
# WORKSHEET CONTROL REFERENCES
# ============================================================

def find_control_refs_in_worksheets(
    archive: zipfile.ZipFile,
    numeric_shape_id: str,
) -> list[dict]:
    """Tìm <control shapeId="..." r:id="...">."""

    results = []

    shape_pattern = re.compile(
        rf'\bshapeId\s*=\s*"{re.escape(numeric_shape_id)}"',
        flags=re.IGNORECASE,
    )

    rid_pattern = re.compile(
        r'(?:r:)?id\s*=\s*"(rId\d+)"',
        flags=re.IGNORECASE,
    )

    # Một control element thường ngắn.
    element_pattern = re.compile(
        r"<(?:\w+:)?control\b[^>]*>",
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    for path in archive.namelist():
        if not (
            path.startswith(
                "xl/worksheets/"
            )
            and path.endswith(
                ".xml"
            )
        ):
            continue

        text = read_text(
            archive,
            path,
        )

        if numeric_shape_id not in text:
            continue

        relationships = read_relationships(
            archive,
            path,
        )

        for match in element_pattern.finditer(
            text
        ):
            element = match.group(0)

            if not shape_pattern.search(
                element
            ):
                continue

            rid_match = rid_pattern.search(
                element
            )

            rel_id = (
                rid_match.group(1)
                if rid_match
                else None
            )

            rel_info = (
                relationships.get(
                    rel_id
                )
                if rel_id
                else None
            )

            results.append(
                {
                    "worksheet_part": path,
                    "shape_id": (
                        numeric_shape_id
                    ),
                    "relationship_id": (
                        rel_id
                    ),
                    "relationship_found": (
                        rel_info is not None
                    ),
                    "control_part": (
                        rel_info.get(
                            "target"
                        )
                        if rel_info
                        else None
                    ),
                    "relationship_type": (
                        rel_info.get(
                            "type"
                        )
                        if rel_info
                        else None
                    ),
                    "element_preview": (
                        element[:500]
                    ),
                }
            )

    return results


# ============================================================
# CONTROL PART DEPENDENCIES
# ============================================================

def get_control_dependencies(
    archive: zipfile.ZipFile,
    control_part: str,
) -> list[dict]:
    """Lấy relationship đi ra từ control*.xml."""

    if not control_part:
        return []

    rels = read_relationships(
        archive,
        control_part,
    )

    dependencies = []

    for rel_id, info in rels.items():
        dependencies.append(
            {
                "relationship_id": (
                    rel_id
                ),
                "target": info.get(
                    "target"
                ),
                "type": info.get(
                    "type"
                ),
                "target_mode": (
                    info.get(
                        "target_mode"
                    )
                ),
                "rels_path": (
                    info.get(
                        "rels_path"
                    )
                ),
            }
        )

    return dependencies


# ============================================================
# PACKAGE REFERENCE SEARCH
# ============================================================

def search_package_references(
    archive: zipfile.ZipFile,
    token: str,
    exclude_parts: set[str] | None = None,
) -> list[str]:
    """Tìm token trong XML/rels/VML package parts."""

    if not token:
        return []

    exclude_parts = (
        exclude_parts
        or set()
    )

    found = []

    for path in archive.namelist():
        if path in exclude_parts:
            continue

        if not (
            path.endswith(".xml")
            or path.endswith(".rels")
            or "vmlDrawing" in path
        ):
            continue

        text = read_text(
            archive,
            path,
        )

        if token in text:
            found.append(
                path
            )

    return found


# ============================================================
# MAIN
# ============================================================

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
        item.get(
            "shape_id"
        )
        for item in remove_items
        if item.get(
            "shape_id"
        )
    }

    keep_shape_ids = {
        item.get(
            "shape_id"
        )
        for item in keep_items
        if item.get(
            "shape_id"
        )
    }

    print("=" * 72)

    print(
        "M5-XLS-CLEANUP-01C2A - "
        "MACRO10 CLEANUP TRANSACTION SIMULATOR"
    )

    print("=" * 72)

    print(
        "Chế độ: SIMULATE / READ ONLY"
    )

    print(
        "Workbook sẽ KHÔNG bị thay đổi."
    )

    target_records = []

    unique_control_parts = set()

    unique_dependency_parts = set()

    unique_control_rels_parts = set()

    errors = []

    warnings = []

    with zipfile.ZipFile(
        WORKING_FILE,
        "r",
    ) as archive:

        bad_zip_entry = archive.testzip()

        has_vba = (
            "xl/vbaProject.bin"
            in archive.namelist()
        )

        vba_size = (
            len(
                archive.read(
                    "xl/vbaProject.bin"
                )
            )
            if has_vba
            else None
        )

        # ----------------------------------------------------
        # TARGET REMOVE SHAPES
        # ----------------------------------------------------

        for shape_id in sorted(
            remove_shape_ids
        ):
            numeric_id = (
                shape_numeric_id(
                    shape_id
                )
            )

            vml_occurrences = (
                find_shape_vml_occurrences(
                    archive,
                    shape_id,
                )
            )

            control_refs = []

            if numeric_id:
                control_refs = (
                    find_control_refs_in_worksheets(
                        archive,
                        numeric_id,
                    )
                )

            mapped_control_parts = sorted(
                {
                    ref.get(
                        "control_part"
                    )
                    for ref in control_refs
                    if ref.get(
                        "control_part"
                    )
                }
            )

            dependencies = []

            for control_part in (
                mapped_control_parts
            ):
                unique_control_parts.add(
                    control_part
                )

                rel_path = (
                    relationship_path(
                        control_part
                    )
                )

                if rel_path in archive.namelist():
                    unique_control_rels_parts.add(
                        rel_path
                    )

                part_dependencies = (
                    get_control_dependencies(
                        archive,
                        control_part,
                    )
                )

                dependencies.extend(
                    part_dependencies
                )

                for dependency in (
                    part_dependencies
                ):
                    target = dependency.get(
                        "target"
                    )

                    if target:
                        unique_dependency_parts.add(
                            target
                        )

            record = {
                "shape_id": (
                    shape_id
                ),
                "numeric_shape_id": (
                    numeric_id
                ),
                "vml_occurrences": (
                    vml_occurrences
                ),
                "control_refs": (
                    control_refs
                ),
                "control_parts": (
                    mapped_control_parts
                ),
                "dependencies": (
                    dependencies
                ),
            }

            target_records.append(
                record
            )

            # Fail-closed checks
            if len(vml_occurrences) != 1:
                errors.append(
                    {
                        "shape_id": (
                            shape_id
                        ),
                        "reason": (
                            "VML_OCCURRENCE_NOT_EQUAL_1"
                        ),
                        "count": (
                            len(
                                vml_occurrences
                            )
                        ),
                    }
                )

            if not numeric_id:
                errors.append(
                    {
                        "shape_id": (
                            shape_id
                        ),
                        "reason": (
                            "NUMERIC_SHAPE_ID_NOT_FOUND"
                        ),
                    }
                )

            if len(control_refs) == 0:
                warnings.append(
                    {
                        "shape_id": (
                            shape_id
                        ),
                        "reason": (
                            "NO_WORKSHEET_CONTROL_REF_FOUND"
                        ),
                    }
                )

            for ref in control_refs:
                if (
                    ref.get(
                        "relationship_id"
                    )
                    and not ref.get(
                        "relationship_found"
                    )
                ):
                    errors.append(
                        {
                            "shape_id": (
                                shape_id
                            ),
                            "reason": (
                                "CONTROL_RELATIONSHIP_NOT_RESOLVED"
                            ),
                            "worksheet": (
                                ref.get(
                                    "worksheet_part"
                                )
                            ),
                            "relationship_id": (
                                ref.get(
                                    "relationship_id"
                                )
                            ),
                        }
                    )

        # ----------------------------------------------------
        # CHECK KEEP SHAPES
        # Không được dùng chung control part với target xóa.
        # ----------------------------------------------------

        keep_control_parts = set()

        for shape_id in sorted(
            keep_shape_ids
        ):
            numeric_id = (
                shape_numeric_id(
                    shape_id
                )
            )

            if not numeric_id:
                continue

            refs = (
                find_control_refs_in_worksheets(
                    archive,
                    numeric_id,
                )
            )

            for ref in refs:
                control_part = ref.get(
                    "control_part"
                )

                if control_part:
                    keep_control_parts.add(
                        control_part
                    )

        shared_control_parts = sorted(
            unique_control_parts
            & keep_control_parts
        )

        if shared_control_parts:
            errors.append(
                {
                    "reason": (
                        "REMOVE_AND_KEEP_SHARE_CONTROL_PART"
                    ),
                    "control_parts": (
                        shared_control_parts
                    ),
                }
            )

        # ----------------------------------------------------
        # Dependency existence
        # ----------------------------------------------------

        missing_dependency_parts = sorted(
            part
            for part in unique_dependency_parts
            if (
                part not in archive.namelist()
                and not part.startswith(
                    "http:"
                )
                and not part.startswith(
                    "https:"
                )
            )
        )

        if missing_dependency_parts:
            errors.append(
                {
                    "reason": (
                        "DEPENDENCY_PART_NOT_FOUND"
                    ),
                    "parts": (
                        missing_dependency_parts
                    ),
                }
            )

        # ----------------------------------------------------
        # Check dependencies referenced elsewhere
        # ----------------------------------------------------

        shared_dependency_refs = []

        for dependency_part in sorted(
            unique_dependency_parts
        ):
            basename = posixpath.basename(
                dependency_part
            )

            refs = search_package_references(
                archive,
                basename,
            )

            # Chỉ báo cáo để xem.
            shared_dependency_refs.append(
                {
                    "dependency_part": (
                        dependency_part
                    ),
                    "reference_parts": (
                        refs
                    ),
                }
            )

    # ========================================================
    # COUNTS
    # ========================================================

    targets_with_control_ref = sum(
        1
        for record in target_records
        if record[
            "control_refs"
        ]
    )

    targets_without_control_ref = (
        len(target_records)
        - targets_with_control_ref
    )

    exact_vml_targets = sum(
        1
        for record in target_records
        if len(
            record[
                "vml_occurrences"
            ]
        ) == 1
    )

    plan_valid = (
        len(remove_shape_ids) == 46
        and exact_vml_targets == 46
        and len(errors) == 0
        and bad_zip_entry is None
        and has_vba
    )

    # ========================================================
    # REPORT
    # ========================================================

    report = {
        "operation": (
            "M5-XLS-CLEANUP-01C2A"
        ),
        "mode": (
            "SIMULATE_READ_ONLY"
        ),
        "workbook_modified": False,

        "working_file": str(
            WORKING_FILE
        ),

        "summary": {
            "target_shape_count": (
                len(
                    remove_shape_ids
                )
            ),
            "exact_vml_target_count": (
                exact_vml_targets
            ),
            "target_with_control_ref": (
                targets_with_control_ref
            ),
            "target_without_control_ref": (
                targets_without_control_ref
            ),
            "unique_control_parts": (
                len(
                    unique_control_parts
                )
            ),
            "unique_control_relationship_parts": (
                len(
                    unique_control_rels_parts
                )
            ),
            "unique_dependency_parts": (
                len(
                    unique_dependency_parts
                )
            ),
            "shared_keep_remove_control_parts": (
                len(
                    shared_control_parts
                )
            ),
            "error_count": (
                len(errors)
            ),
            "warning_count": (
                len(warnings)
            ),
            "zip_integrity_ok": (
                bad_zip_entry is None
            ),
            "vba_present": (
                has_vba
            ),
            "vba_size_bytes": (
                vba_size
            ),
            "transaction_plan_valid": (
                plan_valid
            ),
        },

        "target_records": (
            target_records
        ),

        "control_parts": sorted(
            unique_control_parts
        ),

        "control_relationship_parts": sorted(
            unique_control_rels_parts
        ),

        "dependency_parts": sorted(
            unique_dependency_parts
        ),

        "shared_dependency_references": (
            shared_dependency_refs
        ),

        "errors": (
            errors
        ),

        "warnings": (
            warnings
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

    # ========================================================
    # TERMINAL
    # ========================================================

    print(
        "\nKẾT QUẢ TỔNG HỢP"
    )

    print(
        "VML Shape cần loại: "
        f"{len(remove_shape_ids)}"
    )

    print(
        "VML Shape ánh xạ chính xác: "
        f"{exact_vml_targets}"
    )

    print(
        "Target có Worksheet control ref: "
        f"{targets_with_control_ref}"
    )

    print(
        "Target chưa thấy control ref: "
        f"{targets_without_control_ref}"
    )

    print(
        "Control parts liên quan: "
        f"{len(unique_control_parts)}"
    )

    print(
        "Control .rels parts liên quan: "
        f"{len(unique_control_rels_parts)}"
    )

    print(
        "Dependency/ctrlProp parts liên quan: "
        f"{len(unique_dependency_parts)}"
    )

    print(
        "Control part dùng chung KEEP/REMOVE: "
        f"{len(shared_control_parts)}"
    )

    print(
        "Errors: "
        f"{len(errors)}"
    )

    print(
        "Warnings: "
        f"{len(warnings)}"
    )

    print(
        "ZIP integrity: "
        f"{'PASS' if bad_zip_entry is None else 'FAIL'}"
    )

    print(
        "VBA project: "
        f"{'PASS' if has_vba else 'FAIL'}"
    )

    if vba_size is not None:
        print(
            "vbaProject.bin size: "
            f"{vba_size} bytes"
        )

    if warnings:
        print(
            "\nCẢNH BÁO ĐẦU TIÊN"
        )

        for warning in warnings[:20]:
            print(
                f"- {warning}"
            )

    if errors:
        print(
            "\nLỖI TRANSACTION PLAN"
        )

        for error in errors[:30]:
            print(
                f"- {error}"
            )

    print(
        "\nĐã tạo transaction plan:"
    )

    print(
        OUTPUT_FILE
    )

    if plan_valid:
        print(
            "\nKẾT QUẢ: "
            "TRANSACTION PLAN VALIDATED"
        )
    else:
        print(
            "\nKẾT QUẢ: "
            "TRANSACTION PLAN NOT VALIDATED"
        )

        raise RuntimeError(
            "Không được ghi workbook. "
            "Transaction plan chưa đủ an toàn."
        )


if __name__ == "__main__":
    main()