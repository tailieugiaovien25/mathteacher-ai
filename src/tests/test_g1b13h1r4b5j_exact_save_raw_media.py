from io import BytesIO
from pathlib import Path
import zipfile

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part

from lesson_planning_v2.services.lesson_plan_merge_service import LessonPlanMergeService

ROOT = Path(__file__).resolve().parents[2]
AUTHORING = ROOT / "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py"
MERGE = ROOT / "src/lesson_planning_v2/services/lesson_plan_merge_service.py"

def _text(path):
    return path.read_text(encoding="utf-8-sig")

def test_top_save_uses_existing_callback_contract():
    text = _text(AUTHORING)
    assert "G1B_13H1R4B5J_TOP_SAVE_RUNTIME_WIRING" in text
    assert "disabled=(save_handler is None or not standardized_content or audit_blocks_save)" in text
    assert "artifact_file_name=(" in text
    assert "artifact_content=standardized_content" in text

def test_raw_image_part_copy_preserves_unsupported_media_bytes():
    source = Document()
    target = Document()
    raw = b"NOT-A-PYTHON-DOCX-DECODABLE-IMAGE"
    part = Part(
        PackURI("/word/media/image77.emf"),
        "image/x-emf",
        raw,
        source.part.package,
    )
    rid = source.part.relate_to(part, RT.IMAGE)

    service = LessonPlanMergeService()
    new_rid = service._copy_relationship(
        source_document=source,
        target_document=target,
        relationship_id=rid,
    )

    copied = target.part.rels[new_rid].target_part
    assert copied.blob == raw
    assert copied.content_type == "image/x-emf"

    output = BytesIO()
    target.save(output)
    with zipfile.ZipFile(BytesIO(output.getvalue())) as archive:
        media = [
            name for name in archive.namelist()
            if name.startswith("word/media/")
        ]
        assert media
        assert any(archive.read(name) == raw for name in media)

def test_image_branch_no_longer_calls_get_or_add_image():
    text = _text(MERGE)
    start = text.index("G1B_13H1R4B5J_RAW_OPC_IMAGE_PART_COPY")
    nearby = text[start-200:start+1300]
    assert "image_part.blob" in nearby
    assert "package.next_partname(" in nearby
    assert "target_document.part.relate_to(" in nearby
    assert "get_or_add_image" not in nearby
