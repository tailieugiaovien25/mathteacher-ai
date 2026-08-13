import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


WORKBOOK = Path(
    r"data\working\LBG-TUYEN_CLEANUP_SAFE_WORKING.xlsm"
)


def main():
    print("=" * 76)
    print(
        "M5-XLS-DIAG-05 - "
        "LuuBG FORMULA LOAD INVENTORY"
    )
    print("=" * 76)

    print("Chế độ: READ ONLY")
    print("Workbook KHÔNG bị thay đổi.")
    print()

    with zipfile.ZipFile(
        WORKBOOK,
        "r",
    ) as z:

        # ----------------------------------------------------
        # 1. Map worksheet XML -> sheet name
        # ----------------------------------------------------

        workbook_xml = ET.fromstring(
            z.read(
                "xl/workbook.xml"
            )
        )

        rels_xml = ET.fromstring(
            z.read(
                "xl/_rels/workbook.xml.rels"
            )
        )

        rel_targets = {}

        for rel in rels_xml:
            rel_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target")

            if rel_id and target:
                rel_targets[
                    rel_id
                ] = target

        namespaces = {
            "main": (
                "http://schemas.openxmlformats.org/"
                "spreadsheetml/2006/main"
            ),
            "r": (
                "http://schemas.openxmlformats.org/"
                "officeDocument/2006/relationships"
            ),
        }

        sheet_map = {}

        sheets = workbook_xml.find(
            "main:sheets",
            namespaces,
        )

        for sheet in sheets:

            name = sheet.attrib.get(
                "name"
            )

            rid = sheet.attrib.get(
                "{"
                + namespaces["r"]
                + "}id"
            )

            target = rel_targets.get(
                rid
            )

            if not target:
                continue

            if target.startswith("/"):
                part = target.lstrip("/")
            else:
                part = (
                    "xl/"
                    + target.lstrip("/")
                )

            part = part.replace(
                "xl/xl/",
                "xl/",
            )

            sheet_map[
                part
            ] = name

        print("WORKSHEET MAP")
        print("-" * 76)

        for part, name in sorted(
            sheet_map.items()
        ):
            print(
                f"{part} => {name}"
            )

        # ----------------------------------------------------
        # 2. Tìm part của LuuBG
        # ----------------------------------------------------

        luubg_part = None

        for part, name in (
            sheet_map.items()
        ):
            if name == "LuuBG":
                luubg_part = part
                break

        if not luubg_part:
            raise RuntimeError(
                "Không xác định được sheet LuuBG."
            )

        print()
        print(
            "LuuBG part:",
            luubg_part,
        )

        # ----------------------------------------------------
        # 3. Đọc XML của LuuBG
        # ----------------------------------------------------

        text = z.read(
            luubg_part
        ).decode(
            "utf-8",
            errors="replace",
        )

        formula_matches = re.findall(
            r"<f(?:\s[^>]*)?>(.*?)</f>",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        total_formulas = len(
            formula_matches
        )

        tkb_q_refs = 0

        function_counts = Counter()

        for formula in formula_matches:

            if (
                "TKB-Q!" in formula
                or "'TKB-Q'!" in formula
            ):
                tkb_q_refs += 1

            functions = re.findall(
                r"\b([A-Z][A-Z0-9_.]*)\s*\(",
                formula,
                flags=re.IGNORECASE,
            )

            for function_name in functions:
                function_counts[
                    function_name.upper()
                ] += 1

        print()
        print("=" * 76)
        print("LuuBG FORMULA LOAD")
        print("=" * 76)

        print(
            "Total LuuBG formulas:",
            total_formulas,
        )

        print(
            "Formulas referencing TKB-Q:",
            tkb_q_refs,
        )

        print()
        print(
            "TOP 20 FUNCTIONS:"
        )

        for name, count in (
            function_counts.most_common(
                20
            )
        ):
            print(
                f"- {name}: {count}"
            )

        print()
        print("=" * 76)
        print(
            "KẾT QUẢ: "
            "LuuBG FORMULA LOAD INVENTORY COMPLETE"
        )
        print("=" * 76)

        print()
        print(
            "Workbook KHÔNG bị thay đổi."
        )


if __name__ == "__main__":
    main()