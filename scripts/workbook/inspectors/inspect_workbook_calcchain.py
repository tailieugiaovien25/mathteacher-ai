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
        "M5-XLS-DIAG-04 - "
        "CALCCHAIN / FORMULA DEPENDENCY INVENTORY"
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

        calcchain_path = (
            "xl/calcChain.xml"
        )

        print("=" * 76)
        print("CALCCHAIN PART")
        print("=" * 76)

        if calcchain_path not in names:
            print(
                "calcChain.xml: NOT PRESENT"
            )

            calcchain_count = 0

        else:
            data = z.read(
                calcchain_path
            )

            print(
                "calcChain.xml: PRESENT"
            )

            print(
                "calcChain size:",
                len(data),
            )

            try:
                root = ET.fromstring(
                    data
                )

                calcchain_count = len(
                    list(root)
                )

                print(
                    "calcChain entries:",
                    calcchain_count,
                )

            except ET.ParseError as exc:
                print(
                    "calcChain XML PARSE: FAIL"
                )

                print(
                    "Error:",
                    exc,
                )

                calcchain_count = -1

        # ====================================================
        # Đếm công thức thực tế trong worksheet XML
        # ====================================================

        print()
        print("=" * 76)
        print("FORMULA INVENTORY")
        print("=" * 76)

        worksheet_parts = sorted(
            name
            for name in names
            if (
                name.startswith(
                    "xl/worksheets/sheet"
                )
                and name.endswith(
                    ".xml"
                )
            )
        )

        formula_counts = Counter()

        total_formulas = 0

        for path in worksheet_parts:

            text = z.read(
                path
            ).decode(
                "utf-8",
                errors="replace",
            )

            count = len(
                re.findall(
                    r"<f(?:\s[^>]*)?>",
                    text,
                    flags=re.IGNORECASE,
                )
            )

            formula_counts[
                path
            ] = count

            total_formulas += count

        print(
            "Worksheet parts:",
            len(worksheet_parts),
        )

        print(
            "Total formula cells:",
            total_formulas,
        )

        print()
        print(
            "FORMULAS BY WORKSHEET PART:"
        )

        for path, count in (
            formula_counts.most_common()
        ):
            if count == 0:
                continue

            print(
                f"- {path}: {count}"
            )

        # ====================================================
        # Workbook relationships tới calcChain
        # ====================================================

        print()
        print("=" * 76)
        print("CALCCHAIN RELATIONSHIPS")
        print("=" * 76)

        workbook_rels = (
            "xl/_rels/workbook.xml.rels"
        )

        calcchain_rel_count = 0

        if workbook_rels in names:

            text = z.read(
                workbook_rels
            ).decode(
                "utf-8",
                errors="replace",
            )

            matches = re.findall(
                r"<Relationship\b[^>]*"
                r"calcChain"
                r"[^>]*/>",
                text,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )

            calcchain_rel_count = len(
                matches
            )

        print(
            "calcChain relationship count:",
            calcchain_rel_count,
        )

        # ====================================================
        # Final
        # ====================================================

        print()
        print("=" * 76)
        print("SUMMARY")
        print("=" * 76)

        print(
            "Formula cells:",
            total_formulas,
        )

        print(
            "calcChain entries:",
            calcchain_count,
        )

        print(
            "calcChain relationship:",
            calcchain_rel_count,
        )

        print()

        if calcchain_count == -1:
            print(
                "RESULT: FAIL - "
                "CALCCHAIN XML INVALID"
            )

        elif calcchain_path not in names:
            print(
                "RESULT: INFO - "
                "NO CALCCHAIN PRESENT"
            )

        elif (
            calcchain_count == 0
            and total_formulas > 0
        ):
            print(
                "RESULT: REVIEW - "
                "EMPTY CALCCHAIN WITH FORMULAS"
            )

        else:
            print(
                "RESULT: CALCCHAIN INVENTORY COMPLETE"
            )

        print()
        print(
            "Workbook KHÔNG bị thay đổi."
        )


if __name__ == "__main__":
    main()