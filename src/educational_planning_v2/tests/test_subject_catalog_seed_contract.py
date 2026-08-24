from pathlib import Path


def _seed_sql() -> str:
    root = Path(
        __file__
    ).resolve().parents[3]

    path = (
        root
        / "supabase"
        / "migrations"
        / "202608160006_subject_catalog_seed.sql"
    )

    assert path.exists(), (
        "subject catalog seed migration is missing"
    )

    text = path.read_text(
        encoding="utf-8"
    )

    assert "?" not in text
    assert "\ufffd" not in text

    return text


def _u(value: str) -> str:
    return value.encode(
        "ascii"
    ).decode(
        "unicode_escape"
    )


def test_math_subject_exists_and_is_optional():
    sql = _seed_sql()

    assert "'subject-math'" in sql
    assert "'MATH'" in sql
    assert (
        "'" + _u("To\\u00e1n") + "'"
        in sql
    )

    block = sql[
        sql.index("'subject-math'"):
        sql.index("'subject-literature'")
    ]

    assert "'OPTIONAL'" in block
    assert "'ACTIVE'" in block


def test_math_has_exactly_four_canonical_components():
    sql = _seed_sql()

    expected = (
        (
            "component-math-arithmetic",
            "ARITHMETIC",
            _u("S\\u1ed1 h\\u1ecdc"),
        ),
        (
            "component-math-algebra",
            "ALGEBRA",
            _u("\\u0110\\u1ea1i s\\u1ed1"),
        ),
        (
            "component-math-statistics-probability",
            "SXTK",
            "SXTK",
        ),
        (
            "component-math-geometry",
            "GEOMETRY",
            _u("H\\u00ecnh h\\u1ecdc"),
        ),
    )

    for component_id, code, name in expected:
        assert component_id in sql
        assert f"'{code}'" in sql
        assert f"'{name}'" in sql

    ids = (
        "component-math-arithmetic",
        "component-math-algebra",
        "component-math-statistics-probability",
        "component-math-geometry",
    )

    assert sum(
        item in sql
        for item in ids
    ) == 4


def test_natural_science_has_three_components():
    sql = _seed_sql()

    assert "'subject-natural-science'" in sql
    assert (
        "'" + _u(
            "Khoa h\\u1ecdc "
            "t\\u1ef1 nhi\\u00ean"
        ) + "'"
        in sql
    )

    expected = (
        (
            "component-natural-science-physics",
            "PHYSICS",
            _u("V\\u1eadt l\\u00ed"),
        ),
        (
            "component-natural-science-chemistry",
            "CHEMISTRY",
            _u("H\\u00f3a h\\u1ecdc"),
        ),
        (
            "component-natural-science-biology",
            "BIOLOGY",
            _u("Sinh h\\u1ecdc"),
        ),
    )

    for component_id, code, name in expected:
        assert component_id in sql
        assert f"'{code}'" in sql
        assert f"'{name}'" in sql


def test_history_geography_has_two_components():
    sql = _seed_sql()

    assert "'subject-history-geography'" in sql

    subject_name = _u(
        "L\\u1ecbch s\\u1eed "
        "v\\u00e0 "
        "\\u0110\\u1ecba l\\u00ed"
    )

    assert f"'{subject_name}'" in sql

    expected = (
        (
            "component-history-geography-history",
            "HISTORY",
            _u("L\\u1ecbch s\\u1eed"),
        ),
        (
            "component-history-geography-geography",
            "GEOGRAPHY",
            _u("\\u0110\\u1ecba l\\u00ed"),
        ),
    )

    for component_id, code, name in expected:
        assert component_id in sql
        assert f"'{code}'" in sql
        assert f"'{name}'" in sql


def test_art_has_two_components():
    sql = _seed_sql()

    assert "'subject-art'" in sql
    assert (
        "'" + _u(
            "Ngh\\u1ec7 thu\\u1eadt"
        ) + "'"
        in sql
    )

    expected = (
        (
            "component-art-music",
            "MUSIC",
            _u("\\u00c2m nh\\u1ea1c"),
        ),
        (
            "component-art-fine-arts",
            "FINE_ARTS",
            _u("M\\u0129 thu\\u1eadt"),
        ),
    )

    for component_id, code, name in expected:
        assert component_id in sql
        assert f"'{code}'" in sql
        assert f"'{name}'" in sql


def test_component_subject_links_are_canonical():
    sql = _seed_sql()

    expected_links = {
        "component-math-arithmetic":
            "subject-math",
        "component-math-algebra":
            "subject-math",
        "component-math-statistics-probability":
            "subject-math",
        "component-math-geometry":
            "subject-math",

        "component-natural-science-physics":
            "subject-natural-science",
        "component-natural-science-chemistry":
            "subject-natural-science",
        "component-natural-science-biology":
            "subject-natural-science",

        "component-history-geography-history":
            "subject-history-geography",
        "component-history-geography-geography":
            "subject-history-geography",

        "component-art-music":
            "subject-art",
        "component-art-fine-arts":
            "subject-art",
    }

    for component_id, subject_id in (
        expected_links.items()
    ):
        start = sql.index(
            f"'{component_id}'"
        )

        fragment = sql[
            start:start + 300
        ]

        assert f"'{subject_id}'" in fragment


def test_none_policy_subjects_exist():
    sql = _seed_sql()

    none_subjects = (
        "subject-literature",
        "subject-foreign-language-1",
        "subject-civic-education",
        "subject-technology",
        "subject-informatics",
        "subject-physical-education",
        "subject-experiential-activities",
        "subject-local-education",
    )

    for subject_id in none_subjects:
        assert f"'{subject_id}'" in sql


def test_component_bearing_subjects_are_optional():
    sql = _seed_sql()

    subject_order = (
        "subject-math",
        "subject-literature",
        "subject-foreign-language-1",
        "subject-civic-education",
        "subject-natural-science",
        "subject-history-geography",
        "subject-technology",
        "subject-informatics",
        "subject-physical-education",
        "subject-art",
        "subject-experiential-activities",
        "subject-local-education",
    )

    expected = (
        "subject-math",
        "subject-natural-science",
        "subject-history-geography",
        "subject-art",
    )

    for subject_id in expected:
        index = subject_order.index(
            subject_id
        )

        start = sql.index(
            f"'{subject_id}'"
        )

        if index + 1 < len(subject_order):
            end = sql.index(
                f"'{subject_order[index + 1]}'",
                start,
            )
        else:
            end = sql.index(
                "on conflict",
                start,
            )

        assert (
            "'OPTIONAL'"
            in sql[start:end]
        )


def test_seed_is_idempotent():
    sql = _seed_sql().lower()

    assert (
        sql.count(
            "on conflict (\n"
            "    subject_id\n"
            ")\n"
            "do update set"
        )
        >= 1
    )

    assert (
        sql.count(
            "on conflict (\n"
            "    component_id\n"
            ")\n"
            "do update set"
        )
        >= 4
    )


def test_seed_uses_stable_machine_identifiers():
    sql = _seed_sql()

    stable_codes = (
        "MATH",
        "NATURAL_SCIENCE",
        "HISTORY_GEOGRAPHY",
        "ART",
        "ARITHMETIC",
        "ALGEBRA",
        "SXTK",
        "GEOMETRY",
        "PHYSICS",
        "CHEMISTRY",
        "BIOLOGY",
        "HISTORY",
        "GEOGRAPHY",
        "MUSIC",
        "FINE_ARTS",
    )

    for code in stable_codes:
        assert f"'{code}'" in sql


def test_seed_has_no_unicode_corruption():
    sql = _seed_sql()

    assert "?" not in sql
    assert "\ufffd" not in sql

    expected_names = (
        _u("To\\u00e1n"),
        _u("S\\u1ed1 h\\u1ecdc"),
        _u("\\u0110\\u1ea1i s\\u1ed1"),
        "SXTK",
        _u("H\\u00ecnh h\\u1ecdc"),
        _u(
            "Khoa h\\u1ecdc "
            "t\\u1ef1 nhi\\u00ean"
        ),
        _u("V\\u1eadt l\\u00ed"),
        _u("H\\u00f3a h\\u1ecdc"),
        _u("Sinh h\\u1ecdc"),
        _u(
            "L\\u1ecbch s\\u1eed "
            "v\\u00e0 "
            "\\u0110\\u1ecba l\\u00ed"
        ),
        _u("L\\u1ecbch s\\u1eed"),
        _u("\\u0110\\u1ecba l\\u00ed"),
        _u("Ngh\\u1ec7 thu\\u1eadt"),
        _u("\\u00c2m nh\\u1ea1c"),
        _u("M\\u0129 thu\\u1eadt"),
    )

    for name in expected_names:
        assert name in sql
