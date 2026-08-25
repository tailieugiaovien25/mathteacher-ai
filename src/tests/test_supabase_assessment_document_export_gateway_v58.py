from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from assessment_generation_v2.adapters import (
    AssessmentDocumentExportGatewayError,
    SupabaseAssessmentDocumentExportGateway,
)


EXAM_VERSION_ID = "11111111-1111-4111-8111-111111111111"
VARIANT_ID = "22222222-2222-4222-8222-222222222222"
OWNER_ID = "33333333-3333-4333-8333-333333333333"
SNAPSHOT_ID = "44444444-4444-4444-8444-444444444444"
TEMPLATE_VERSION_ID = "55555555-5555-4555-8555-555555555555"
PACKAGE_IDS = {
    "STUDENT_EXAM": "66666666-6666-4666-8666-666666666661",
    "ANSWER_KEY": "66666666-6666-4666-8666-666666666662",
    "SCORING_GUIDE": "66666666-6666-4666-8666-666666666663",
}


@dataclass
class FakeResponse:
    data: object


class FakeQuery:
    def __init__(self, client, table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.operations: list[tuple] = []

    def select(self, columns: str):
        self.operations.append(("select", columns))
        return self

    def eq(self, field: str, value: object):
        self.operations.append(("eq", field, value))
        return self

    def order(self, field: str, **options):
        self.operations.append(("order", field, options))
        return self

    def limit(self, value: int):
        self.operations.append(("limit", value))
        return self

    def execute(self):
        self.client.query_calls.append(
            (self.table_name, tuple(self.operations))
        )
        return FakeResponse(self.client.table_data[self.table_name])


class FakeRpc:
    def __init__(self, client, name: str, arguments: dict) -> None:
        self.client = client
        self.name = name
        self.arguments = arguments

    def execute(self):
        self.client.rpc_calls.append((self.name, self.arguments))
        key = (
            self.name,
            tuple(sorted(self.arguments.items())),
        )
        return FakeResponse(self.client.rpc_data[key])


class FakeBucket:
    def __init__(self, storage, bucket_name: str) -> None:
        self.storage = storage
        self.bucket_name = bucket_name

    def download(self, path: str):
        self.storage.download_calls.append((self.bucket_name, path))
        return self.storage.files[(self.bucket_name, path)]


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[tuple[str, str], object] = {}
        self.download_calls: list[tuple[str, str]] = []

    def from_(self, bucket_name: str):
        return FakeBucket(self, bucket_name)


class FakeClient:
    def __init__(self) -> None:
        self.table_data = {
            "assessment_exam_variants": [_variant_row()],
            "assessment_exam_export_packages": _package_rows(),
            "assessment_document_template_versions": [
                _template_row()
            ],
        }
        self.rpc_data = {
            (
                "assessment_exam_snapshot_hash_matches",
                (("target_snapshot_id", SNAPSHOT_ID),),
            ): True,
            **{
                (
                    "assessment_exam_export_package_hash_matches",
                    (("target_export_package_id", package_id),),
                ): True
                for package_id in PACKAGE_IDS.values()
            },
        }
        self.query_calls: list[tuple] = []
        self.rpc_calls: list[tuple[str, dict]] = []
        self.storage = FakeStorage()

    def table(self, table_name: str):
        return FakeQuery(self, table_name)

    def rpc(self, name: str, arguments: dict):
        return FakeRpc(self, name, arguments)


def _variant_row() -> dict[str, object]:
    return {
        "variant_id": VARIANT_ID,
        "variant_status": "LOCKED",
        "assessment_exam_snapshots": {
            "snapshot_id": SNAPSHOT_ID,
            "exam_version_id": EXAM_VERSION_ID,
            "snapshot_document": {
                "snapshot_schema_version": 2,
            },
            "snapshot_hash": "a" * 64,
            "assessment_exam_versions": {
                "assessment_exams": {
                    "owner_user_id": OWNER_ID,
                }
            },
        },
    }


def _package_rows() -> list[dict[str, object]]:
    return [
        {
            "export_package_id": PACKAGE_IDS[package_type],
            "package_type": package_type,
            "package_payload": {
                "package_type": package_type,
                "payload": package_type.lower(),
            },
            "package_hash": character * 64,
            "package_status": "LOCKED",
            "created_at": f"2026-08-25T00:00:0{index}Z",
        }
        for index, (package_type, character) in enumerate(
            (
                ("STUDENT_EXAM", "b"),
                ("ANSWER_KEY", "c"),
                ("SCORING_GUIDE", "d"),
            ),
            start=1,
        )
    ]


def _template_row() -> dict[str, object]:
    return {
        "template_version_id": TEMPLATE_VERSION_ID,
        "version_number": 3,
        "review_status": "APPROVED",
        "global_layout_schema": {"paper_size": "A4"},
        "global_style_schema": {
            "font_family": "Times New Roman",
            "font_size": 12,
        },
        "assessment_document_template_sets": {
            "template_code": "PHONG-MAU-2026",
            "lifecycle_status": "ACTIVE",
            "current_version_number": 3,
        },
        "assessment_document_template_definitions": [
            {
                "document_type_code": "MATRIX",
                "renderer_code": "DOCX_JSON_V1",
                "supported_formats": ["DOCX"],
                "layout_schema": {"page_orientation": "LANDSCAPE"},
                "style_schema": {"table_font_size": 10},
                "binding_schema": {"rows": "matrix"},
                "section_schema": [
                    {
                        "section_code": "MATRIX",
                        "section_type": "TABLE",
                        "bindings": ["rows"],
                    }
                ],
                "template_asset_path": None,
                "template_asset_hash": None,
                "sort_order": 1,
            }
        ],
    }


def _gateway(client=None, **changes):
    return SupabaseAssessmentDocumentExportGateway(
        client=client or FakeClient(),
        user_id=OWNER_ID,
        **changes,
    )


def test_loads_verified_published_source_and_three_payloads() -> None:
    client = FakeClient()
    source = _gateway(client).load_published_render_source(
        exam_version_id=EXAM_VERSION_ID,
        variant_id=VARIANT_ID,
    )

    assert source is not None
    assert source.hash_verified is True
    assert source.owner_user_id == OWNER_ID
    assert source.student_exam_payload["payload"] == "student_exam"
    assert source.answer_key_payload["payload"] == "answer_key"
    assert source.scoring_guide_payload["payload"] == "scoring_guide"
    assert len(client.rpc_calls) == 4


def test_source_query_requires_locked_variant_and_exam_version() -> None:
    client = FakeClient()
    _gateway(client).load_published_render_source(
        exam_version_id=EXAM_VERSION_ID,
        variant_id=VARIANT_ID,
    )
    operations = client.query_calls[0][1]

    assert ("eq", "variant_status", "LOCKED") in operations
    assert (
        "eq",
        "assessment_exam_snapshots.exam_version_id",
        EXAM_VERSION_ID,
    ) in operations


def test_empty_variant_lookup_returns_none() -> None:
    client = FakeClient()
    client.table_data["assessment_exam_variants"] = []

    assert _gateway(client).load_published_render_source(
        exam_version_id=EXAM_VERSION_ID,
        variant_id=VARIANT_ID,
    ) is None
    assert not client.rpc_calls


def test_owner_mismatch_stops_before_hash_and_payload_reads() -> None:
    client = FakeClient()
    row = _variant_row()
    row["assessment_exam_snapshots"]["assessment_exam_versions"][
        "assessment_exams"
    ]["owner_user_id"] = "99999999-9999-4999-8999-999999999999"
    client.table_data["assessment_exam_variants"] = [row]

    with pytest.raises(PermissionError, match="owned"):
        _gateway(client).load_published_render_source(
            exam_version_id=EXAM_VERSION_ID,
            variant_id=VARIANT_ID,
        )

    assert not client.rpc_calls
    assert len(client.query_calls) == 1


def test_missing_required_package_is_rejected() -> None:
    client = FakeClient()
    client.table_data["assessment_exam_export_packages"] = (
        _package_rows()[:-1]
    )

    with pytest.raises(
        AssessmentDocumentExportGatewayError,
        match="SCORING_GUIDE",
    ):
        _gateway(client).load_published_render_source(
            exam_version_id=EXAM_VERSION_ID,
            variant_id=VARIANT_ID,
        )


def test_invalid_package_hash_is_rejected() -> None:
    client = FakeClient()
    key = (
        "assessment_exam_export_package_hash_matches",
        (("target_export_package_id", PACKAGE_IDS["ANSWER_KEY"]),),
    )
    client.rpc_data[key] = False

    with pytest.raises(
        AssessmentDocumentExportGatewayError,
        match="ANSWER_KEY",
    ):
        _gateway(client).load_published_render_source(
            exam_version_id=EXAM_VERSION_ID,
            variant_id=VARIANT_ID,
        )


def test_finds_current_approved_active_docx_template() -> None:
    client = FakeClient()
    template = _gateway(client).find_active_template(
        template_set_code="phong-mau-2026",
        document_type="matrix",
    )

    assert template is not None
    assert template.template_version_id == TEMPLATE_VERSION_ID
    assert template.review_status == "APPROVED"
    assert template.lifecycle_status == "ACTIVE"
    assert template.definition.layout_schema["paper_size"] == "A4"
    assert template.definition.layout_schema["page_orientation"] == (
        "LANDSCAPE"
    )
    assert template.definition.style_schema["font_size"] == 12
    assert template.definition.style_schema["table_font_size"] == 10


def test_non_current_template_version_is_not_selected() -> None:
    client = FakeClient()
    row = _template_row()
    row["version_number"] = 2
    client.table_data["assessment_document_template_versions"] = [row]

    assert _gateway(client).find_active_template(
        template_set_code="PHONG-MAU-2026",
        document_type="MATRIX",
    ) is None


def test_template_without_docx_support_is_rejected() -> None:
    client = FakeClient()
    row = _template_row()
    row["assessment_document_template_definitions"][0][
        "supported_formats"
    ] = ["PDF"]
    client.table_data["assessment_document_template_versions"] = [row]

    with pytest.raises(
        AssessmentDocumentExportGatewayError,
        match="DOCX",
    ):
        _gateway(client).find_active_template(
            template_set_code="PHONG-MAU-2026",
            document_type="MATRIX",
        )


def test_downloads_asset_from_private_configured_bucket() -> None:
    client = FakeClient()
    path = f"{TEMPLATE_VERSION_ID}/matrix.docx"
    client.storage.files[
        ("assessment-document-templates", path)
    ] = b"PK-template"

    content = _gateway(client).load_template_asset(asset_path=path)

    assert content == b"PK-template"
    assert client.storage.download_calls == [
        ("assessment-document-templates", path)
    ]


@pytest.mark.parametrize(
    "path",
    (
        "../secret.docx",
        "/absolute/template.docx",
        "folder\\template.docx",
    ),
)
def test_rejects_unsafe_asset_paths(path: str) -> None:
    with pytest.raises(
        AssessmentDocumentExportGatewayError,
        match="unsafe",
    ):
        _gateway().load_template_asset(asset_path=path)


def test_rejects_oversized_asset() -> None:
    client = FakeClient()
    path = f"{TEMPLATE_VERSION_ID}/matrix.docx"
    client.storage.files[
        ("assessment-document-templates", path)
    ] = b"x" * 1025

    with pytest.raises(
        AssessmentDocumentExportGatewayError,
        match="size",
    ):
        _gateway(
            client,
            maximum_asset_bytes=1024,
        ).load_template_asset(asset_path=path)


def test_adapter_has_no_governance_mutation_methods() -> None:
    source = Path(
        "src/assessment_generation_v2/adapters/"
        "supabase_assessment_document_export_gateway.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "def approve_",
        "def publish_",
        "def create_snapshot",
        "def activate_",
        "service_role",
    ):
        assert forbidden not in source


def test_private_storage_migration_has_governed_policies() -> None:
    text = Path(
        "supabase/migrations/"
        "202608250020_assessment_document_template_assets.sql"
    ).read_text(encoding="utf-8")

    assert "'assessment-document-templates'" in text
    assert "false," in text
    assert "26214400" in text
    assert "assessment_template_assets_select_visible" in text
    assert "assessment_document_template_set_is_visible" in text
    assert "assessment_template_asset_is_editable" in text
    assert "template_set.owner_user_id = auth.uid()" in text
    assert "current_user_is_portal_admin" in text
    assert "'DRAFT'" in text
    assert "'REVISION_REQUIRED'" in text
    assert "'APPROVED'" not in text[
        text.index("assessment_template_assets_insert_editable") :
        text.index("assessment_template_assets_update_editable")
    ]
