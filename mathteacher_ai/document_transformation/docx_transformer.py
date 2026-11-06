"""Strict DOCX formatting utilities for MathTeacher AI.

The transformer never overwrites the source. It preserves text, tables and media;
only formatting-only whitespace paragraphs and explicitly supplied date placeholders
may be changed. Use a date_map keyed by teaching period to populate date fields.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import Mapping

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree

_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}\s+\(6A[12]\)$")


def _visible_paragraphs(path: Path) -> list[str]:
    """Read visible paragraph text, including explicit Word line breaks and tabs."""
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    result = []
    for para in root.xpath(".//w:body//w:p", namespaces=_NS):
        parts = []
        for node in para.xpath(".//w:t | .//w:br | .//w:cr | .//w:tab", namespaces=_NS):
            if node.tag == qn("w:t"):
                parts.append(node.text or "")
            elif node.tag in (qn("w:br"), qn("w:cr")):
                parts.append("\\n")
            elif node.tag == qn("w:tab"):
                parts.append("\\t")
        value = "".join(parts)
        if value.strip():
            result.append(value)
    return result

def _expected_without_week_lines(paragraphs: list[str]) -> list[str]:
    """Expected visible text after the explicitly requested WEEK-line removal."""
    expected = []
    for paragraph in paragraphs:
        kept_lines = [
            line for line in paragraph.splitlines()
            if not line.strip().upper().startswith("WEEK:")
        ]
        value = "\n".join(kept_lines).strip()
        if value:
            expected.append(value)
    return expected


def _media_hashes(path: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(path) as archive:
        return sorted(
            (name, hashlib.sha256(archive.read(name)).hexdigest())
            for name in archive.namelist()
            if name.startswith("word/media/")
        )


def _set_run_font(run, *, italic=None, bold=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    props = run._element.get_or_add_rPr()
    fonts = props.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        props.insert(0, fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{key}"), "Times New Roman")
    if italic is not None:
        run.italic = italic
    if bold is not None:
        run.bold = bold


def _compact_paragraph(paragraph):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing = 1.0
    fmt.keep_together = False
    fmt.keep_with_next = False
    for run in paragraph.runs:
        _set_run_font(run)


def _set_cell_margins(cell, top=40, start=70, bottom=40, end=70):
    props = cell._tc.get_or_add_tcPr()
    margins = props.find(qn("w:tcMar"))
    if margins is None:
        margins = OxmlElement("w:tcMar")
        props.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        element = margins.find(qn(f"w:{side}"))
        if element is None:
            element = OxmlElement(f"w:{side}")
            margins.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def _clear_fill_properties(root):
    for tag in ("w:shd", "w:highlight"):
        for element in list(root.iter(qn(tag))):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)


def _replace_date_cell(cell, dates: Mapping[str, str]):
    """Replace date-cell contents; the WEEK line is intentionally omitted."""
    required = {"planning", "6A1", "6A2"}
    if not required.issubset(dates):
        raise ValueError(f"Date entry must include: {', '.join(sorted(required))}")
    for paragraph in list(cell.paragraphs):
        paragraph._element.getparent().remove(paragraph._element)

    lines = [
        (f"Date of planning: {dates['planning']}", 0),
        (f"Date of teaching: {dates['6A1']} (6A1)", 0),
        (f"{dates['6A2']} (6A2)", 0.28),
    ]
    for text, indent in lines:
        paragraph = cell.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(indent) if indent else None
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        _set_run_font(paragraph.add_run(text), italic=True, bold=False)


def _apply_date_map(document, date_map):
    if not date_map:
        return
    for table in document.tables:
        if not table.rows:
            continue
        row = table.rows[0]
        text = " ".join(cell.text for cell in row.cells)
        match = re.search(r"\bPeriod\s*(\d+)\b", text, re.IGNORECASE)
        if match and match.group(1) in date_map:
            _replace_date_cell(row.cells[0], date_map[match.group(1)])




def _remove_week_lines_from_date_cells(document):
    """Remove WEEK lines from lesson header date cells."""
    for table in document.tables:
        if not table.rows:
            continue
        row = table.rows[0]
        row_text = " ".join(cell.text for cell in row.cells)
        if not re.search(r"\bPeriod\s*\d+\b", row_text, re.IGNORECASE):
            continue
        cell = row.cells[0]
        for paragraph in list(cell.paragraphs):
            lines = paragraph.text.splitlines()
            kept = [line for line in lines if not line.strip().upper().startswith("WEEK:")]
            if len(kept) != len(lines):
                if kept and any(line.strip() for line in kept):
                    paragraph.text = "\n".join(kept)
                else:
                    paragraph._element.getparent().remove(paragraph._element)
        if not cell.paragraphs:
            cell.add_paragraph()

def transform_docx(source, output, *, date_map=None):
    """Create a formatted DOCX at output and return its Path.

    date_map example:
      {"28": {"planning": "06/11/2026", "6A1": "10/11/2026", "6A2": "10/11/2026"}}
    """
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source == output or output.exists():
        raise FileExistsError("Output must be a new path; source is never overwritten.")

    original_text = _visible_paragraphs(source)
    original_media = _media_hashes(source)
    document = Document(source)

    for section in document.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)
        section.header_distance = Cm(1)
        section.footer_distance = Cm(1)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:cs"), "Times New Roman")
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0

    for paragraph in document.paragraphs:
        _compact_paragraph(paragraph)

    for table in document.tables:
        table.autofit = False
        for row in table.rows:
            row_props = row._tr.get_or_add_trPr()
            for height in list(row_props.findall(qn("w:trHeight"))):
                row_props.remove(height)
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                _set_cell_margins(cell)
                for paragraph in list(cell.paragraphs):
                    if not paragraph.text.strip() and len(cell.paragraphs) > 1:
                        paragraph._element.getparent().remove(paragraph._element)
                    else:
                        _compact_paragraph(paragraph)

    _apply_date_map(document, date_map)
    _remove_week_lines_from_date_cells(document)

    for section in document.sections:
        for part in (section.header, section.footer):
            for paragraph in part.paragraphs:
                _compact_paragraph(paragraph)
            for table in part.tables:
                for row in table.rows:
                    for cell in row.cells:
                        _set_cell_margins(cell)
                        for paragraph in cell.paragraphs:
                            _compact_paragraph(paragraph)
            _clear_fill_properties(part._element)

    _clear_fill_properties(document.element.body)
    document.save(output)

    if not date_map and _visible_paragraphs(output) != _expected_without_week_lines(original_text):
        output.unlink(missing_ok=True)
        raise RuntimeError("Text integrity check failed; generated output removed.")
    if _media_hashes(output) != original_media:
        output.unlink(missing_ok=True)
        raise RuntimeError("Embedded media integrity check failed; generated output removed.")
    return output
