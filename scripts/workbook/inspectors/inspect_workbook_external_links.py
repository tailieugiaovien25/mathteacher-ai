import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORKBOOK = Path(
    r"data\working\LBG-TUYEN_CLEANUP_SAFE_WORKING.xlsm"
)


def normalize_target(source_part, target):
    if target.startswith("/"):
        return target.lstrip("/")

    return posixpath.normpath(
        posixpath.join(
            posixpath.dirname(source_part),
            target,
        )
    ).lstrip("/")


def main():
    print("=" * 76)
    print(
        "M5-XLS-DIAG-03 - "
        "EXTERNAL LINKS / CONNECTIONS / QUERIES INVENTORY"
    )
    print("=" * 76)

    print("Chế độ: READ ONLY")
    print("Workbook KHÔNG bị thay đổi.")
    print()

    if not WORKBOOK.exists():
        raise FileNotFoundError(
            f"Không tìm thấy workbook: {WORKBOOK}"
        )

    with zipfile.ZipFile(
        WORKBOOK,
        "r",
    ) as z:

        names = set(
            z.namelist()
        )

        # ====================================================
        # 1. External link parts
        # ====================================================

        external_link_parts = sorted(
            name
            for name in names
            if name.startswith(
                "xl/externalLinks/"
            )
            and not name.endswith(
                ".rels"
            )
        )

        print("=" * 76)
        print("EXTERNAL LINK PARTS")
        print("=" * 76)

        print(
            "External link parts:",
            len(external_link_parts),
        )

        for path in external_link_parts:
            print(
                "-",
                path,
            )

        # ====================================================
        # 2. Connections
        # ====================================================

        connection_parts = sorted(
            name
            for name in names
            if (
                name == "xl/connections.xml"
                or
                name.startswith(
                    "xl/connections/"
                )
            )
        )

        print()
        print("=" * 76)
        print("CONNECTION PARTS")
        print("=" * 76)

        print(
            "Connection parts:",
            len(connection_parts),
        )

        for path in connection_parts:
            print(
                "-",
                path,
            )

        if "xl/connections.xml" in names:
            text = z.read(
                "xl/connections.xml"
            ).decode(
                "utf-8",
                errors="replace",
            )

            connection_tags = re.findall(
                r"<connection\b",
                text,
                flags=re.IGNORECASE,
            )

            print(
                "Connection records:",
                len(connection_tags),
            )

        # ====================================================
        # 3. Query tables
        # ====================================================

        query_parts = sorted(
            name
            for name in names
            if name.startswith(
                "xl/queryTables/"
            )
            and not name.endswith(
                ".rels"
            )
        )

        print()
        print("=" * 76)
        print("QUERY TABLE PARTS")
        print("=" * 76)

        print(
            "Query table parts:",
            len(query_parts),
        )

        for path in query_parts:
            print(
                "-",
                path,
            )

        # ====================================================
        # 4. Power Query / mashup related
        # ====================================================

        mashup_parts = sorted(
            name
            for name in names
            if (
                "mashup" in name.lower()
                or
                "customxml" in name.lower()
                or
                "queries" in name.lower()
            )
        )

        print()
        print("=" * 76)
        print("MASHUP / CUSTOM XML / QUERY RELATED")
        print("=" * 76)

        print(
            "Related parts:",
            len(mashup_parts),
        )

        for path in mashup_parts[:100]:
            print(
                "-",
                path,
            )

        # ====================================================
        # 5. External relationships
        # ====================================================

        external_relationships = []

        for rels_path in sorted(
            name
            for name in names
            if name.endswith(
                ".rels"
            )
        ):
            try:
                root = ET.fromstring(
                    z.read(
                        rels_path
                    )
                )
            except ET.ParseError:
                continue

            for relationship in root:
                target_mode = (
                    relationship.attrib.get(
                        "TargetMode"
                    )
                )

                if (
                    target_mode
                    != "External"
                ):
                    continue

                external_relationships.append(
                    {
                        "rels": rels_path,
                        "id": (
                            relationship.attrib.get(
                                "Id"
                            )
                        ),
                        "type": (
                            relationship.attrib.get(
                                "Type"
                            )
                        ),
                        "target": (
                            relationship.attrib.get(
                                "Target"
                            )
                        ),
                    }
                )

        print()
        print("=" * 76)
        print("EXTERNAL RELATIONSHIPS")
        print("=" * 76)

        print(
            "External relationships:",
            len(external_relationships),
        )

        for item in external_relationships:
            print(
                "-",
                item,
            )

        # ====================================================
        # 6. Workbook formula strings with external book refs
        # ====================================================

        external_formula_refs = []

        pattern = re.compile(
            r"\[[^\]]+\]",
            flags=re.IGNORECASE,
        )

        worksheet_parts = sorted(
            name
            for name in names
            if name.startswith(
                "xl/worksheets/"
            )
            and name.endswith(
                ".xml"
            )
        )

        for path in worksheet_parts:
            text = z.read(
                path
            ).decode(
                "utf-8",
                errors="replace",
            )

            for match in pattern.finditer(
                text
            ):
                snippet_start = max(
                    0,
                    match.start() - 80,
                )

                snippet_end = min(
                    len(text),
                    match.end() + 120,
                )

                snippet = text[
                    snippet_start:
                    snippet_end
                ]

                external_formula_refs.append(
                    {
                        "part": path,
                        "token": (
                            match.group(0)
                        ),
                        "snippet": snippet,
                    }
                )

                if (
                    len(
                        external_formula_refs
                    )
                    >= 100
                ):
                    break

            if (
                len(
                    external_formula_refs
                )
                >= 100
            ):
                break

        print()
        print("=" * 76)
        print("EXTERNAL FORMULA TOKENS")
        print("=" * 76)

        print(
            "Detected tokens:",
            len(external_formula_refs),
        )

        for item in external_formula_refs[:30]:
            print(
                "-",
                item[
                    "part"
                ],
                item[
                    "token"
                ],
            )

        # ====================================================
        # FINAL
        # ====================================================

        print()
        print("=" * 76)

        total_external_signal = (
            len(external_link_parts)
            + len(connection_parts)
            + len(query_parts)
            + len(external_relationships)
            + len(external_formula_refs)
        )

        if total_external_signal == 0:
            print(
                "RESULT: "
                "NO EXTERNAL LINK / CONNECTION SIGNAL DETECTED"
            )
        else:
            print(
                "RESULT: "
                "EXTERNAL LINK / CONNECTION SIGNAL DETECTED"
            )

        print("=" * 76)

        print()
        print(
            "Workbook KHÔNG bị thay đổi."
        )


if __name__ == "__main__":
    main()