from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from portal_v2.ui.assessment_document_export_streamlit import (
    ActiveTemplateSetOption,
    PublishedExamVariantOption,
    SupabaseAssessmentExportCatalog,
    render_assessment_document_export_page,
)


USER_ID = "11111111-1111-4111-8111-111111111111"
EXAM_VERSION_ID = "22222222-2222-4222-8222-222222222222"
VARIANT_ID = "33333333-3333-4333-8333-333333333333"


class Response:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table

    def select(self, value):
        self.client.calls.append((self.table, "select", value))
        return self

    def eq(self, field, value):
        self.client.calls.append((self.table, "eq", field, value))
        return self

    def order(self, field, **kwargs):
        self.client.calls.append((self.table, "order", field, kwargs))
        return self

    def execute(self):
        return Response(self.client.rows[self.table])


class Client:
    def __init__(self):
        self.calls = []
        self.rows = {
            "assessment_exam_variants": [
                {
                    "variant_id": VARIANT_ID,
                    "variant_code": "101",
                    "variant_status": "LOCKED",
                    "assessment_exam_snapshots": {
                        "exam_version_id": EXAM_VERSION_ID,
                        "assessment_exam_versions": {
                            "exam_title": "Đề giữa học kỳ I",
                            "assessment_exams": {
                                "exam_code": "TOAN6-GHK1",
                                "owner_user_id": USER_ID,
                            },
                        },
                    },
                }
            ],
            "assessment_document_template_sets": [
                {
                    "template_code": "PHONG-DIEN-BIEN",
                    "template_name": "Mẫu Phòng GDĐT",
                    "authority_scope": "DISTRICT",
                    "lifecycle_status": "ACTIVE",
                    "current_version_number": 2,
                    "assessment_document_template_versions": [
                        {
                            "version_number": 2,
                            "review_status": "APPROVED",
                        }
                    ],
                }
            ],
        }

    def table(self, name):
        return Query(self, name)


def test_catalog_lists_only_user_locked_variants() -> None:
    client = Client()

    options = SupabaseAssessmentExportCatalog(
        client=client,
        user_id=USER_ID,
    ).list_published_variants()

    assert options == (
        PublishedExamVariantOption(
            exam_version_id=EXAM_VERSION_ID,
            variant_id=VARIANT_ID,
            exam_code="TOAN6-GHK1",
            exam_title="Đề giữa học kỳ I",
            variant_code="101",
        ),
    )
    assert (
        "assessment_exam_variants",
        "eq",
        "variant_status",
        "LOCKED",
    ) in client.calls
    assert any(
        call[1:3] == ("eq", "assessment_exam_snapshots."
            "assessment_exam_versions.assessment_exams.owner_user_id")
        and call[3] == USER_ID
        for call in client.calls
    )


def test_catalog_lists_current_approved_template_set() -> None:
    options = SupabaseAssessmentExportCatalog(
        client=Client(),
        user_id=USER_ID,
    ).list_active_template_sets()

    assert options == (
        ActiveTemplateSetOption(
            template_set_code="PHONG-DIEN-BIEN",
            display_name="Mẫu Phòng GDĐT",
            authority_scope="DISTRICT",
        ),
    )


class Catalog:
    def list_published_variants(self):
        return (
            PublishedExamVariantOption(
                exam_version_id=EXAM_VERSION_ID,
                variant_id=VARIANT_ID,
                exam_code="TOAN6-GHK1",
                exam_title="Đề giữa học kỳ I",
                variant_code="101",
            ),
        )

    def list_active_template_sets(self):
        return (
            ActiveTemplateSetOption(
                template_set_code="PHONG-DIEN-BIEN",
                display_name="Mẫu Phòng GDĐT",
                authority_scope="DISTRICT",
            ),
        )


@dataclass
class FormContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamlit:
    def __init__(self, *, submitted=True, document_labels=None):
        self.session_state = {}
        self.submitted = submitted
        self.document_labels = document_labels
        self.messages = []
        self.downloads = []

    def title(self, value):
        self.messages.append(("title", value))

    def caption(self, value):
        self.messages.append(("caption", value))

    def info(self, value):
        self.messages.append(("info", value))

    def warning(self, value):
        self.messages.append(("warning", value))

    def error(self, value):
        self.messages.append(("error", value))

    def success(self, value):
        self.messages.append(("success", value))

    def form(self, key):
        return FormContext()

    def selectbox(self, label, options):
        return options[0]

    def multiselect(self, label, options, default):
        return tuple(default) if self.document_labels is None else self.document_labels

    def text_input(self, label, value, max_chars):
        return value

    def form_submit_button(self, *args, **kwargs):
        return self.submitted

    def download_button(self, label, **kwargs):
        self.downloads.append((label, kwargs))


class Service:
    def __init__(self):
        self.requests = []

    def export(self, *, request):
        self.requests.append(request)
        return SimpleNamespace(
            bundle_content=b"PK-bundle",
            bundle_filename="bo-de-kiem-tra.zip",
            bundle_hash="a" * 64,
            documents=(1, 2, 3, 4, 5),
        )


def test_page_exports_and_exposes_download() -> None:
    st = FakeStreamlit()
    service = Service()

    render_assessment_document_export_page(
        st=st,
        client=object(),
        user_id=USER_ID,
        catalog=Catalog(),
        service_factory=lambda **kwargs: service,
    )

    assert len(service.requests) == 1
    request = service.requests[0]
    assert request.owner_user_id == USER_ID
    assert request.template_set_code == "PHONG-DIEN-BIEN"
    assert len(request.document_types) == 5
    assert st.downloads[0][1]["mime"] == "application/zip"
    assert st.downloads[0][1]["data"] == b"PK-bundle"


def test_page_rejects_empty_document_selection() -> None:
    st = FakeStreamlit(document_labels=())
    service = Service()

    render_assessment_document_export_page(
        st=st,
        client=object(),
        user_id=USER_ID,
        catalog=Catalog(),
        service_factory=lambda **kwargs: service,
    )

    assert service.requests == []
    assert any(
        kind == "error" and "ít nhất một" in message
        for kind, message in st.messages
    )


def test_page_has_no_governance_actions() -> None:
    text = Path(
        "src/portal_v2/ui/assessment_document_export_streamlit.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "approve_exam",
        "publish_exam",
        "activate_assessment",
        "create_snapshot",
    ):
        assert forbidden not in text


def test_teacher_portal_exposes_export_page() -> None:
    text = Path("scripts/teacher_portal/app.py").read_text(
        encoding="utf-8-sig"
    )

    assert "'Xu\\u1ea5t \\u0111\\u1ec1 ki\\u1ec3m tra'" in text
    assert 'selected == "Xuất đề kiểm tra"' in text
    assert "render_assessment_document_export_page(" in text
