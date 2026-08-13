import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WRITE_CAPABLE_SCRIPTS = (
    "scripts/workbook/maintenance/import_first_real_yccd_safe.py",
    "scripts/workbook/maintenance/import_first_real_yccd_period_map_safe.py",
)

WORKBOOK_MAINTENANCE_DEFAULTS = (
    (
        "scripts/workbook/maintenance/apply_macro10_cleanup_transaction.py",
        "APPLY_CHANGES",
    ),
    (
        "scripts/workbook/maintenance/apply_macro10_cleanup_transaction_safe.py",
        "APPLY_CHANGES",
    ),
    (
        "scripts/workbook/maintenance/prepare_workbook_cleanup.py",
        "CREATE_COPIES",
    ),
)


def configured_dry_run(script_path):
    source = (PROJECT_ROOT / script_path).read_text(encoding="utf-8-sig")
    module = ast.parse(source, filename=script_path)

    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "DRY_RUN"
            for target in statement.targets
        ):
            continue
        return ast.literal_eval(statement.value)

    raise AssertionError(f"DRY_RUN is not declared in {script_path}")


def configured_flag(script_path, flag_name):
    source = (PROJECT_ROOT / script_path).read_text(encoding="utf-8-sig")
    module = ast.parse(source, filename=script_path)

    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == flag_name
            for target in statement.targets
        ):
            continue
        return ast.literal_eval(statement.value)

    raise AssertionError(f"{flag_name} is not declared in {script_path}")


@pytest.mark.parametrize("script_path", WRITE_CAPABLE_SCRIPTS)
def test_write_capable_scripts_are_safe_by_default(script_path):
    assert configured_dry_run(script_path) is True


@pytest.mark.parametrize(
    ("script_path", "flag_name"),
    WORKBOOK_MAINTENANCE_DEFAULTS,
)
def test_workbook_maintenance_requires_explicit_opt_in(
    script_path,
    flag_name,
):
    assert configured_flag(script_path, flag_name) is False
