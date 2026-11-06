from io import BytesIO

from docx import Document
import pytest

from portal_v2.ui.docx_formatting_streamlit import (
    _safe_output_name,
    _validate_docx_payload,
)


def _docx_bytes():
    buffer = BytesIO()
    document = Document()
    document.add_paragraph("Giáo án kiểm thử")
    document.save(buffer)
    return buffer.getvalue()


def test_validate_accepts_real_docx():
    _validate_docx_payload(_docx_bytes())


@pytest.mark.parametrize("payload", [b"", b"not-a-docx", b"PK\\x03\\x04broken"])
def test_validate_rejects_invalid_docx(payload):
    with pytest.raises(ValueError):
        _validate_docx_payload(payload)


def test_output_name_is_safe_and_keeps_docx_extension():
    assert _safe_output_name("../../Kế hoạch tuần 10.docx") == "K_ho_ch_tu_n_10_CHUAN_HOA.docx"
