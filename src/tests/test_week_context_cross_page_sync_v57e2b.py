from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"src/portal_v2/ui/weekly_schedule_streamlit.py"

def src(name):
    text=SOURCE.read_text(encoding="utf-8-sig"); tree=ast.parse(text); lines=text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node,ast.FunctionDef) and node.name==name:
            return "\n".join(lines[node.lineno-1:node.end_lineno])
    raise AssertionError(name)

def test_lbg_week_change_publishes_active_and_standardization_week():
    s = src("_autosave_lbg_filter_context")
    assert "_emit_canonical_week_change(" in s
    assert 'source_control="system_weekly_week_number"' in s
    assert "_STANDARDIZATION_WEEK_KEY] = selected_week" not in s

def test_standardization_week_change_publishes_active_and_lbg_week():
    s = src("_sync_standardization_week_to_lbg")
    assert "_emit_canonical_week_change(" in s
    assert "source_control=_STANDARDIZATION_WEEK_KEY" in s
    assert '"system_weekly_week_number"' not in s

def test_standardization_resolves_active_week_before_lbg_mirror():
    s = src("render_weekly_schedule_workspace")
    authority = s.index("V57-F2C5G_CANONICAL_WEEK_AUTHORITY")
    context = s.index("get_canonical_context(", authority)
    projection = s.index("_STANDARDIZATION_WEEK_KEY", context)
    assert authority < context < projection

def test_callbacks_do_not_write_database():
    s=src("_autosave_lbg_filter_context")+src("_sync_standardization_week_to_lbg")
    assert ".save(" not in s and ".upsert(" not in s and ".insert(" not in s
