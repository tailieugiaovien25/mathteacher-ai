from dataclasses import FrozenInstanceError
import inspect

from portal_v2.ui import (
    ADMIN_PAGE_DASHBOARD,
    ADMIN_PAGE_SOURCES,
    ADMIN_PAGE_SYSTEM_HEALTH,
    ADMIN_PAGE_TIME_ALLOCATION,
    ADMIN_PAGE_TRUSTED_DATA,
    ADMIN_PAGE_USERS,
    ADMIN_PORTAL_PAGES,
    AdminPortalPage,
    admin_portal_page_ids,
    admin_portal_page_labels,
    admin_portal_pages,
    resolve_admin_portal_page,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False
    return False


def main():
    print("=" * 72)
    print("WR-001E.2D.1 - ADMIN PORTAL NAVIGATION CONTRACT TEST")
    print("=" * 72)

    pages = admin_portal_pages()
    ids = admin_portal_page_ids()
    labels = admin_portal_page_labels()

    expected_ids = (
        ADMIN_PAGE_DASHBOARD,
        ADMIN_PAGE_TRUSTED_DATA,
        ADMIN_PAGE_TIME_ALLOCATION,
        ADMIN_PAGE_SOURCES,
        ADMIN_PAGE_USERS,
        ADMIN_PAGE_SYSTEM_HEALTH,
    )

    tests = [
        ("APN1 Navigation pages are immutable tuple", isinstance(pages, tuple)),
        ("APN2 Six admin pages registered", len(pages) == 6),
        (
            "APN3 All pages use canonical page contract",
            all(isinstance(page, AdminPortalPage) for page in pages),
        ),
        ("APN4 Page IDs unique", len(ids) == len(set(ids))),
        ("APN5 Page labels unique", len(labels) == len(set(labels))),
        ("APN6 Navigation order deterministic", ids == expected_ids),
        (
            "APN7 Dashboard resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_DASHBOARD).label
            == "Dashboard",
        ),
        (
            "APN8 Trusted Data resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_TRUSTED_DATA).label
            == "Trusted Data",
        ),
        (
            "APN9 Time Allocation resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_TIME_ALLOCATION).label
            == "Time Allocation",
        ),
        (
            "APN10 Sources & Provenance resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_SOURCES).label
            == "Sources & Provenance",
        ),
        (
            "APN11 Users & Permissions resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_USERS).label
            == "Users & Permissions",
        ),
        (
            "APN12 System Health resolved",
            resolve_admin_portal_page(page_id=ADMIN_PAGE_SYSTEM_HEALTH).label
            == "System Health",
        ),
        (
            "APN13 Unknown page blocked",
            expect_error(
                ValueError,
                lambda: resolve_admin_portal_page(page_id="unknown"),
            ),
        ),
        (
            "APN14 Empty page blocked",
            expect_error(
                ValueError,
                lambda: resolve_admin_portal_page(page_id=" "),
            ),
        ),
        (
            "APN15 Page contract immutable",
            expect_error(
                FrozenInstanceError,
                lambda: setattr(pages[0], "label", "Changed"),
            ),
        ),
    ]

    source = inspect.getsource(AdminPortalPage)

    tests.extend(
        [
            (
                "APN16 Navigation contract is Streamlit-independent",
                "streamlit" not in source.lower(),
            ),
            (
                "APN17 Navigation contains no user identity",
                "email" not in source.lower()
                and "user_id" not in source.lower(),
            ),
            (
                "APN18 Canonical registry preserved",
                pages == ADMIN_PORTAL_PAGES,
            ),
        ]
    )

    results = []
    for label, passed in tests:
        results.append(passed)
        print(f"{label}: {'PASS' if passed else 'FAIL'}")

    print()

    if all(results):
        print("RESULT: PASS - ADMIN PORTAL NAVIGATION CONTRACT VERIFIED")
        raise SystemExit(0)

    print("RESULT: FAIL - ADMIN PORTAL NAVIGATION CONTRACT VIOLATED")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
