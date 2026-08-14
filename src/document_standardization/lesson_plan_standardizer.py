"""Standardize lesson-plan DOCX formatting without changing its content."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from lxml import etree


@dataclass(frozen=True)
class DocumentInventory:
    paragraphs: int
    tables: int
    table_cells: int
    inline_shapes: int
    sections: int
    omml_equations: int
    equation_paragraphs: int
    ole_objects: int
    drawings: int
    images: int
    fonts: dict[str, int] = field(default_factory=dict)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _package_counts(path: Path) -> dict[str, int]:
    counts = Counter()
    with zipfile.ZipFile(path) as archive:
        counts["images"] = sum(name.startswith("word/media/") for name in archive.namelist())
        for name in archive.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            xml = archive.read(name)
            counts["omml_equations"] += xml.count(b"<m:oMath>")
            counts["equation_paragraphs"] += xml.count(b"<m:oMathPara")
            counts["ole_objects"] += xml.count(b"<o:OLEObject")
            counts["drawings"] += xml.count(b"<w:drawing")
    return dict(counts)


def inventory(path: Path) -> DocumentInventory:
    document = Document(path)
    fonts = Counter()
    table_cells = 0
    paragraphs = list(document.paragraphs)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                table_cells += 1
                paragraphs.extend(cell.paragraphs)
    for paragraph in paragraphs:
        for run in paragraph.runs:
            if run.font.name:
                fonts[run.font.name] += 1
    package = _package_counts(path)
    return DocumentInventory(
        paragraphs=len(paragraphs), tables=len(document.tables), table_cells=table_cells,
        inline_shapes=len(document.inline_shapes), sections=len(document.sections),
        omml_equations=package.get("omml_equations", 0),
        equation_paragraphs=package.get("equation_paragraphs", 0),
        ole_objects=package.get("ole_objects", 0), drawings=package.get("drawings", 0),
        images=package.get("images", 0), fonts=dict(sorted(fonts.items())),
    )


class LessonPlanWordStandardizer:
    """Apply deterministic formatting rules to a copy of a DOCX file."""

    def __init__(self, profile: dict[str, object]):
        self.profile = deepcopy(profile)

    @classmethod
    def from_json(cls, path: Path) -> "LessonPlanWordStandardizer":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def standardize(self, source: Path, output: Path, report_path: Path) -> dict[str, object]:
        source = source.resolve()
        output = output.resolve()
        if source == output:
            raise ValueError("Không được ghi đè tệp Word gốc.")
        if source.suffix.lower() != ".docx" or output.suffix.lower() != ".docx":
            raise ValueError("Công cụ V1 chỉ xử lý tệp .docx.")

        before = inventory(source)
        source_hash = _sha256(source)
        document = Document(source)
        changes = Counter()
        self._normalize_sections(document, changes)
        self._normalize_styles(document)
        self._normalize_paragraphs(document, changes)
        self._normalize_tables(document, changes)
        self._normalize_headers_and_footers(document, changes)

        output.parent.mkdir(parents=True, exist_ok=True)
        document.save(output)
        if self.profile.get("equations", {}).get("mode") == "force_times":
            changes["omml_runs_forced_to_times"] = self._force_omml_font(
                output,
                self.profile["equations"].get("text_font", "Times New Roman"),
                self.profile["body"]["size_pt"],
            )
        after = inventory(output)
        self._validate_integrity(before, after)

        report = {
            "result": "completed_with_review" if before.omml_equations or before.ole_objects else "completed",
            "source": str(source), "output": str(output), "source_sha256": source_hash,
            "source_preserved": _sha256(source) == source_hash,
            "profile_name": self.profile.get("profile_name", "lesson-plan-default"),
            "before": asdict(before), "after": asdict(after), "changes": dict(changes),
            "equations": {
                "mode": self.profile.get("equations", {}).get("mode", "safe"),
                "plain_text_font": self.profile.get("equations", {}).get("text_font", "Times New Roman"),
                "omml_preserved": before.omml_equations,
                "omml_runs_forced_to_times": changes.get("omml_runs_forced_to_times", 0),
                "legacy_or_embedded_requires_review": before.ole_objects,
            },
            "warnings": self._warnings(before),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report

    def _normalize_sections(self, document, changes):
        page = self.profile["page"]
        for section in document.sections:
            section.orientation = WD_ORIENT.PORTRAIT
            section.page_width, section.page_height = Cm(21), Cm(29.7)
            section.left_margin = Cm(page["margin_left_cm"])
            section.right_margin = Cm(page["margin_right_cm"])
            section.top_margin = Cm(page["margin_top_cm"])
            section.bottom_margin = Cm(page["margin_bottom_cm"])
            changes["sections_normalized"] += 1

    def _normalize_styles(self, document):
        body = self.profile["body"]
        style = document.styles["Normal"]
        style.font.name = body["font"]
        style.font.size = Pt(body["size_pt"])
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), body["font"])

    @staticmethod
    def _clear_header_or_footer(container):
        element = container._element
        for child in list(element):
            element.remove(child)
        element.append(OxmlElement("w:p"))

    def _normalize_headers_and_footers(self, document, changes):
        profile = self.profile.get("header_footer", {})
        if not profile.get("remove_existing", False):
            return

        body = self.profile["body"]
        for section in document.sections:
            headers = (section.header, section.first_page_header, section.even_page_header)
            footers = (section.footer, section.first_page_footer, section.even_page_footer)
            for header in headers:
                header.is_linked_to_previous = False
                self._clear_header_or_footer(header)
                changes["headers_cleared"] += 1
            for footer in footers:
                footer.is_linked_to_previous = False
                self._clear_header_or_footer(footer)
                changes["footers_cleared"] += 1

            if profile.get("page_number", True):
                for footer in footers:
                    paragraph = footer.paragraphs[0]
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = paragraph.add_run()
                    run.font.name = body["font"]
                    run.font.size = Pt(body["size_pt"])
                    fonts = run._element.get_or_add_rPr().rFonts
                    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                        fonts.set(qn(f"w:{key}"), body["font"])
                    field_begin = OxmlElement("w:fldChar")
                    field_begin.set(qn("w:fldCharType"), "begin")
                    instruction = OxmlElement("w:instrText")
                    instruction.set(qn("xml:space"), "preserve")
                    instruction.text = " PAGE "
                    field_end = OxmlElement("w:fldChar")
                    field_end.set(qn("w:fldCharType"), "end")
                    run._r.extend((field_begin, instruction, field_end))
                    changes["automatic_page_numbers_added"] += 1

        settings = document.settings._element
        update_fields = settings.find(qn("w:updateFields"))
        if update_fields is None:
            update_fields = OxmlElement("w:updateFields")
            settings.append(update_fields)
        update_fields.set(qn("w:val"), "true")

    def _paragraph_kind(self, text: str) -> str:
        stripped = " ".join(text.split())
        if re.match(r"^(BÀI|CHỦ ĐỀ)\b", stripped, re.I): return "title"
        if re.match(r"^[IVX]+\.\s+", stripped): return "heading_1"
        if re.match(r"^Hoạt động\s+\d+", stripped, re.I): return "activity"
        if re.match(r"^\d+\.\s+", stripped): return "heading_2"
        return "body"

    def _all_paragraphs(self, document):
        yield from document.paragraphs
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from cell.paragraphs

    def _normalize_paragraphs(self, document, changes):
        body = self.profile["body"]
        for paragraph in self._all_paragraphs(document):
            kind = self._paragraph_kind(paragraph.text)
            in_table = paragraph._p.getparent().tag == qn("w:tc")
            size = self.profile["table"]["size_pt"] if in_table else body["size_pt"]
            for run in paragraph.runs:
                run.font.name = body["font"]
                run.font.size = Pt(size)
                fonts = run._element.get_or_add_rPr().rFonts
                for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                    fonts.set(qn(f"w:{key}"), body["font"])
            fmt = paragraph.paragraph_format
            fmt.line_spacing = body["line_spacing"]
            fmt.space_before = Pt(0)
            fmt.space_after = Pt(0)
            if kind == "body" and paragraph.text.strip():
                paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            elif kind == "title":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs: run.bold = True; run.font.size = Pt(self.profile["title"]["size_pt"])
            elif kind in {"heading_1", "heading_2", "activity"}:
                for run in paragraph.runs: run.bold = True
            changes[f"paragraph_{kind}"] += 1

    def _normalize_tables(self, document, changes):
        table_profile = self.profile["table"]
        section = document.sections[0]
        usable_dxa = round((section.page_width - section.left_margin - section.right_margin) / 635)
        for table in document.tables:
            table.autofit = False
            grid_columns = list(table._tbl.tblGrid.gridCol_lst)
            original_widths = [int(column.get(qn("w:w")) or 0) for column in grid_columns]
            original_total = sum(original_widths)
            if original_total > usable_dxa and original_total:
                scale = usable_dxa / original_total
                widths = [round(width * scale) for width in original_widths]
                widths[-1] += usable_dxa - sum(widths)
                changes["tables_scaled_to_page"] += 1
            else:
                widths = original_widths
            for column, width in zip(grid_columns, widths):
                column.set(qn("w:w"), str(width))
            table_width = table._tbl.tblPr.first_child_found_in("w:tblW")
            if table_width is not None and widths:
                table_width.set(qn("w:w"), str(sum(widths)))
                table_width.set(qn("w:type"), "dxa")
            for row_index, row in enumerate(table.rows):
                row_pr = row._tr.get_or_add_trPr()
                existing_no_split = row_pr.find(qn("w:cantSplit"))
                if existing_no_split is not None:
                    row_pr.remove(existing_no_split)
                if row_index == 0 and len(table.rows) > 1:
                    row_pr.append(OxmlElement("w:cantSplit"))
                    header = OxmlElement("w:tblHeader"); header.set(qn("w:val"), "true"); row_pr.append(header)
                for cell_index, cell in enumerate(row.cells):
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    if cell_index < len(widths):
                        cell_width = cell._tc.get_or_add_tcPr().get_or_add_tcW()
                        cell_width.set(qn("w:w"), str(widths[cell_index]))
                        cell_width.set(qn("w:type"), "dxa")
                    if row_index == 0 and len(table.rows) > 1:
                        for paragraph in cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            paragraph.paragraph_format.keep_with_next = True
                            for run in paragraph.runs: run.bold = True; run.font.size = Pt(table_profile["size_pt"])
            changes["tables_normalized"] += 1

    @staticmethod
    def _force_omml_font(path: Path, font: str, size_pt: int) -> int:
        """Set editable OMML runs to normal text font while preserving math structures."""
        math_ns = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        word_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        forced = 0
        handle, temporary_name = tempfile.mkstemp(suffix=".docx", dir=path.parent)
        os.close(handle)
        try:
            with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
                temporary_name, "w", zipfile.ZIP_DEFLATED
            ) as target:
                for item in source.infolist():
                    data = source.read(item.filename)
                    if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                        root = etree.fromstring(data)
                        if item.filename == "word/settings.xml":
                            for node in root.xpath(".//m:mathPr/m:mathFont", namespaces={"m": math_ns}):
                                node.set(f"{{{math_ns}}}val", font)
                        for math_run in root.xpath(".//m:r", namespaces={"m": math_ns}):
                            math_properties = math_run.find(f"{{{math_ns}}}rPr")
                            if math_properties is None:
                                math_properties = etree.Element(f"{{{math_ns}}}rPr")
                                math_run.insert(0, math_properties)
                            if math_properties.find(f"{{{math_ns}}}nor") is None:
                                math_properties.append(etree.Element(f"{{{math_ns}}}nor"))
                            word_properties = math_run.find(f"{{{word_ns}}}rPr")
                            if word_properties is None:
                                word_properties = etree.Element(f"{{{word_ns}}}rPr")
                                math_run.insert(1, word_properties)
                            fonts = word_properties.find(f"{{{word_ns}}}rFonts")
                            if fonts is None:
                                fonts = etree.Element(f"{{{word_ns}}}rFonts")
                                word_properties.insert(0, fonts)
                            for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                                fonts.set(f"{{{word_ns}}}{key}", font)
                            for tag in ("sz", "szCs"):
                                size = word_properties.find(f"{{{word_ns}}}{tag}")
                                if size is None:
                                    size = etree.Element(f"{{{word_ns}}}{tag}")
                                    word_properties.append(size)
                                size.set(f"{{{word_ns}}}val", str(round(size_pt * 2)))
                            forced += 1
                        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                    target.writestr(item, data)
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        return forced

    @staticmethod
    def _validate_integrity(before, after):
        for name in ("tables", "table_cells", "inline_shapes", "sections", "omml_equations", "ole_objects", "images"):
            if getattr(before, name) != getattr(after, name):
                raise ValueError(f"Kiểm tra toàn vẹn thất bại: số lượng {name} đã thay đổi.")

    @staticmethod
    def _warnings(before):
        warnings = []
        if before.omml_equations:
            warnings.append(
                f"Giữ nguyên cấu trúc của {before.omml_equations} công thức Word; cần kiểm tra trực quan font và ký hiệu."
            )
        if before.ole_objects:
            warnings.append(f"Có {before.ole_objects} đối tượng OLE/MathType/Equation cũ cần kiểm tra thủ công.")
        return warnings
