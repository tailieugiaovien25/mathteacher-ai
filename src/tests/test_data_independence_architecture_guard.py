import tempfile
from pathlib import Path

from architecture_v2.guards import (
    DataIndependenceGuard,
)


def main():
    print("=" * 72)
    print(
        "WR-001D.11E.1 - CONTINUOUS DATA "
        "INDEPENDENCE ARCHITECTURE GUARD TEST"
    )
    print("=" * 72)

    results = []

    src_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    guard = DataIndependenceGuard(
        source_root=src_root,
    )

    # --------------------------------------------------------
    # DIG1 - real protected architecture scan
    # --------------------------------------------------------

    violations = guard.scan()

    passed = (
        len(violations) == 0
    )

    results.append(passed)

    print(
        "DIG1 Protected architecture currently clean: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG2 - physical storage dependency detected
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        protected = (
            root
            / "stable_core"
        )

        protected.mkdir(
            parents=True
        )

        (
            protected
            / "bad.py"
        ).write_text(
            "from openpyxl import load_workbook\n",
            encoding="utf-8",
        )

        test_guard = DataIndependenceGuard(
            source_root=root,
            protected_roots=(
                "stable_core",
            ),
        )

        found = test_guard.scan()

    passed = any(
        item.token == "openpyxl"
        for item in found
    )

    results.append(passed)

    print(
        "DIG2 Physical storage dependency detected: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG3 - concrete textbook dependency detected
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        protected = (
            root
            / "stable_core"
        )

        protected.mkdir(
            parents=True
        )

        (
            protected
            / "bad.py"
        ).write_text(
            'BOOK = "KNTT"\n',
            encoding="utf-8",
        )

        test_guard = DataIndependenceGuard(
            source_root=root,
            protected_roots=(
                "stable_core",
            ),
        )

        found = test_guard.scan()

    passed = any(
        item.token.lower() == "kntt"
        for item in found
    )

    results.append(passed)

    print(
        "DIG3 Concrete textbook dependency detected: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG4 - physical file path detected
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        protected = (
            root
            / "stable_core"
        )

        protected.mkdir(
            parents=True
        )

        (
            protected
            / "bad.py"
        ).write_text(
            'SOURCE = "data/input/file.xlsm"\n',
            encoding="utf-8",
        )

        test_guard = DataIndependenceGuard(
            source_root=root,
            protected_roots=(
                "stable_core",
            ),
        )

        found = test_guard.scan()

    passed = (
        len(found) >= 1
    )

    results.append(passed)

    print(
        "DIG4 Physical source path detected: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG5 - generic reference-driven code accepted
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        protected = (
            root
            / "stable_core"
        )

        protected.mkdir(
            parents=True
        )

        (
            protected
            / "good.py"
        ).write_text(
            (
                "def resolve(provider, query):\n"
                "    return provider.query(query)\n"
            ),
            encoding="utf-8",
        )

        test_guard = DataIndependenceGuard(
            source_root=root,
            protected_roots=(
                "stable_core",
            ),
        )

        found = test_guard.scan()

    passed = (
        found == ()
    )

    results.append(passed)

    print(
        "DIG5 Generic provider-driven code accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG6 - tests excluded from production scan
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        tests_dir = (
            root
            / "stable_core"
            / "tests"
        )

        tests_dir.mkdir(
            parents=True
        )

        (
            tests_dir
            / "fixture.py"
        ).write_text(
            'VALUE = "KNTT"\n',
            encoding="utf-8",
        )

        test_guard = DataIndependenceGuard(
            source_root=root,
            protected_roots=(
                "stable_core",
            ),
        )

        found = test_guard.scan()

    passed = (
        found == ()
    )

    results.append(passed)

    print(
        "DIG6 Test fixtures excluded from production guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # DIG7 - immutable result type
    # --------------------------------------------------------

    if violations:
        print()
        print("CURRENT VIOLATIONS")

        for item in violations:
            print(
                f"{item.file_path}:"
                f"{item.line_number} | "
                f"{item.token!r} | "
                f"{item.line_text.strip()}"
            )

    print()

    if all(results):
        print(
            "RESULT: PASS - CONTINUOUS DATA "
            "INDEPENDENCE ARCHITECTURE GUARD VERIFIED"
        )
    else:
        print(
            "RESULT: REVIEW REQUIRED - "
            "DATA INDEPENDENCE VIOLATIONS EXIST"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
