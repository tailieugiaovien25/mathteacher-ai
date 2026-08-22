
from pathlib import Path
import ast


def _source() -> str:
    path = Path(
        "src/portal_v2/ui/"
        "weekly_schedule_streamlit.py"
    )

    return path.read_text(
        encoding="utf-8-sig"
    )


def test_standardized_result_has_preview():
    source = _source()

    assert (
        'build_document_html(\n'
        '            output_bytes'
        in source
        or
        'build_document_html(\n'
        '                output_bytes'
        in source
    )


def test_standardized_result_can_be_saved():
    source = _source()
    tree = ast.parse(source)

    string_values = {
        node.value
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        )
    }

    expected_label = (
        "L\u01b0u v\u00e0o Kho "
        "gi\u00e1o \u00e1n"
    )

    assert (
        expected_label
        in string_values
    )

    assert (
        "content=output_bytes"
        in source
    )



def test_standardized_result_can_be_downloaded():
    source = _source()

    assert (
        'data=output_bytes'
        in source
    )

    assert (
        'file_name=output_name'
        in source
    )


def test_original_upload_is_not_saved_to_library():
    source = _source()

    forbidden = (
        "upload_service.upload(\n"
        "                            content=uploaded_content"
    )

    assert forbidden not in source


def test_final_actions_use_standardized_output_only():
    source = _source()

    result_anchor = (
        "output_name,\n"
        "        output_bytes,\n"
        "        unresolved_fields,"
    )

    assert result_anchor in source

    tail = source.split(
        result_anchor,
        1,
    )[1]

    assert (
        "data=output_bytes"
        in tail
    )

    assert (
        "content=output_bytes"
        in tail
    )
