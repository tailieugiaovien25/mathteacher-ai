from educational_planning_v2.adapters import (
    PPCTPlanItemAdapter,
    PPCTRow,
)


def _expect_exception(exception_type, action):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 72)
    print("WR-001C.8 - PPCT PLAN ITEM ADAPTER CONTRACT TEST")
    print("=" * 72)

    results = []

    adapter = PPCTPlanItemAdapter()

    rows = (
        PPCTRow(
            "Đại6",
            1,
            "Bài 1. Tập hợp",
        ),
        PPCTRow(
            "Đại6",
            2,
            "Bài 2. Cách ghi số tự nhiên",
        ),
        PPCTRow(
            "Đại6",
            5,
            "Bài 5. Phép nhân và phép chia số tự nhiên",
        ),
        PPCTRow(
            "Đại6",
            6,
            "Bài 5. Phép nhân và phép chia số tự nhiên",
        ),
    )

    drafts = adapter.adapt(
        grade=6,
        rows=rows,
    )

    # PPA1
    passed = len(drafts) == 3
    results.append(passed)
    print(
        f"PPA1 Rows adapted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA2
    passed = drafts[2].periods == 2
    results.append(passed)
    print(
        f"PPA2 Multi-period lesson grouped: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA3
    passed = (
        drafts[0].title == "Bài 1. Tập hợp"
        and drafts[1].title == "Bài 2. Cách ghi số tự nhiên"
        and drafts[2].title
        == "Bài 5. Phép nhân và phép chia số tự nhiên"
    )
    results.append(passed)
    print(
        f"PPA3 Source order preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA4
    passed = all(
        draft.curriculum_node_ids == ()
        and draft.canonical_requirement_ids == ()
        for draft in drafts
    )
    results.append(passed)
    print(
        f"PPA4 Canonical IDs not invented: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA5
    normalized = adapter.adapt(
        grade=6,
        rows=(
            PPCTRow(
                "  Đại6  ",
                1,
                "  Bài 1. Tập hợp  ",
            ),
        ),
    )

    passed = (
        normalized[0].title
        == "Bài 1. Tập hợp"
    )
    results.append(passed)
    print(
        f"PPA5 Source text normalized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA6
    passed = _expect_exception(
        TypeError,
        lambda: adapter.adapt(
            grade=6,
            rows=list(rows),
        ),
    )
    results.append(passed)
    print(
        f"PPA6 Non-tuple rows blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA7
    passed = _expect_exception(
        ValueError,
        lambda: adapter.adapt(
            grade=6,
            rows=(
                PPCTRow(
                    "Đại6",
                    1,
                    "   ",
                ),
            ),
        ),
    )
    results.append(passed)
    print(
        f"PPA7 Empty lesson blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # PPA8
    passed = _expect_exception(
        ValueError,
        lambda: adapter.adapt(
            grade=6,
            rows=(
                PPCTRow(
                    "Đại6",
                    0,
                    "Bài 1. Tập hợp",
                ),
            ),
        ),
    )
    results.append(passed)
    print(
        f"PPA8 Invalid period blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "PPCT PLAN ITEM ADAPTER VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "PPCT PLAN ITEM ADAPTER VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
