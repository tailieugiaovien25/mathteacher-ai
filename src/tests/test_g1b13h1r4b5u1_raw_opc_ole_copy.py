from types import SimpleNamespace

from lesson_planning_v2.services.lesson_plan_merge_service import (
    LessonPlanMergeService,
)


OLE_RELTYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/"
    "relationships/oleObject"
)


class _FakePackage:
    def __init__(self):
        self.requested = []

    def next_partname(self, template):
        self.requested.append(template)
        return "/word/embeddings/oleObject77.bin"


class _FakeTargetDocumentPart:
    def __init__(self):
        self.package = _FakePackage()
        self.calls = []

    def relate_to(self, target, reltype, is_external=False):
        self.calls.append((target, reltype, is_external))
        return "rId99"


def test_raw_opc_ole_relationship_is_copied_without_decoding():
    source_ole_part = SimpleNamespace(
        partname="/word/embeddings/oleObject2.bin",
        content_type="application/vnd.openxmlformats-officedocument.oleObject",
        blob=b"RAW-OLE-PAYLOAD",
    )
    source_relationship = SimpleNamespace(
        reltype=OLE_RELTYPE,
        is_external=False,
        target_part=source_ole_part,
    )
    source_document = SimpleNamespace(
        part=SimpleNamespace(rels={"rId8": source_relationship})
    )
    target_part = _FakeTargetDocumentPart()
    target_document = SimpleNamespace(part=target_part)

    service = object.__new__(LessonPlanMergeService)
    new_rid = service._copy_relationship(
        source_document=source_document,
        target_document=target_document,
        relationship_id="rId8",
    )

    assert new_rid == "rId99"
    assert target_part.package.requested == [
        "/word/embeddings/oleObject%d.bin"
    ]
    assert len(target_part.calls) == 1
    copied_part, reltype, is_external = target_part.calls[0]
    assert reltype == OLE_RELTYPE
    assert is_external is False
    assert str(copied_part.partname) == "/word/embeddings/oleObject77.bin"
    assert copied_part.content_type == (
        "application/vnd.openxmlformats-officedocument.oleObject"
    )
    assert copied_part.blob == b"RAW-OLE-PAYLOAD"


def test_unrelated_embedded_relationship_is_still_rejected():
    unsupported = SimpleNamespace(
        reltype="urn:test:unsupported",
        is_external=False,
    )
    source_document = SimpleNamespace(
        part=SimpleNamespace(rels={"rIdX": unsupported})
    )
    target_document = SimpleNamespace(part=_FakeTargetDocumentPart())

    service = object.__new__(LessonPlanMergeService)

    try:
        service._copy_relationship(
            source_document=source_document,
            target_document=target_document,
            relationship_id="rIdX",
        )
    except Exception as error:
        assert type(error).__name__ == "LessonPlanMergeError"
        assert "Unsupported embedded DOCX relationship type" in str(error)
    else:
        raise AssertionError("Unsupported relationship must remain rejected")


def test_patch_is_narrow_and_preserves_existing_image_branch():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "src/lesson_planning_v2/services/lesson_plan_merge_service.py"
    )
    text = source.read_text(encoding="utf-8-sig")
    assert "G1B_13H1R4B5J_RAW_OPC_IMAGE_PART_COPY" in text
    assert "G1B_13H1R4B5U1_RAW_OPC_OLE_PART_COPY" in text
    assert "relationship.reltype == RT.IMAGE" in text
    assert "relationship.reltype == RT.HYPERLINK" in text
