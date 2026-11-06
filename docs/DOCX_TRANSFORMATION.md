# DOCX Transformation

The document transformation module provides deterministic Word formatting for teacher
lesson plans. It is content-preserving by default and never overwrites its input file.

## Python API

```python
from mathteacher_ai.document_transformation.docx_transformer import transform_docx

transform_docx("source.docx", "formatted.docx")
```

To populate lesson dates, pass an explicit mapping keyed by period. Dates are never inferred
or invented by the transformer:

```python
date_map = {
    "28": {
        "planning": "06/11/2026",
        "6A1": "10/11/2026",
        "6A2": "10/11/2026",
    }
}
transform_docx("source.docx", "formatted.docx", date_map=date_map)
```

Date labels and values are Times New Roman 14 pt, black, italic and not bold. The 6A2
line is placed on its own paragraph with a paragraph indent. Existing WEEK text is retained.

## Formatting contract

- A4 paper; margins 2 cm top/bottom, 3 cm left, 2 cm right.
- Times New Roman 14 pt, black text.
- Paragraph before/after spacing set to zero and line spacing 1.0.
- Table cell margins compacted; fixed row heights removed; cell content top-aligned.
- Text shading and highlighting removed; page background is not modified.
- Text, table structure and embedded media are integrity-checked. When explicit date data
  is provided, only the date cell content is intentionally replaced.
- The source file is never overwritten; output must be a new path.

Run tests with: `pytest tests/document_transformation -q`.
