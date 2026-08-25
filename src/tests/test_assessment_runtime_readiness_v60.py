from __future__ import annotations

from pathlib import Path

from assessment_generation_v2.services import (
    AssessmentRuntimeReadinessCheck,
    AssessmentRuntimeReadinessReport,
    SupabaseAssessmentRuntimeReadinessService,
)
from portal_v2.ui.admin_assessment_runtime_readiness_streamlit import (
    render_admin_assessment_runtime_readiness,
)


class Response:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []

    def select(self, columns):
        self.client.calls.append(("select", self.table_name, columns))
        return self

    def eq(self, field_name, value):
        self.filters.append((field_name, value))
        self.client.calls.append(("eq", self.table_name, field_name, value))
        return self

    def limit(self, value):
        self.client.calls.append(("limit", self.table_name, value))
        return self

    def execute(self):
        if self.table_name in self.client.failed_tables:
            raise RuntimeError("relation does not exist")
        return Response(self.client.table_rows.get(self.table_name, []))


class RpcQuery:
    def __init__(self, client, function_name):
        self.client = client
        self.function_name = function_name

    def execute(self):
        if self.function_name in self.client.failed_rpcs:
            raise RuntimeError("function does not exist")
        return Response(False)


class Bucket:
    def __init__(self, client):
        self.client = client

    def list(self, *, path, options):
        if self.client.storage_fails:
            raise RuntimeError("bucket not found")
        self.client.calls.append(("storage_list", path, options))
        return []


class Storage:
    def __init__(self, client):
        self.client = client

    def from_(self, bucket_name):
        self.client.calls.append(("bucket", bucket_name))
        return Bucket(self.client)


class Client:
    def __init__(self, *, populated=True):
        self.calls = []
        self.failed_tables = set()
        self.failed_rpcs = set()
        self.storage_fails = False
        self.storage = Storage(self)
        self.table_rows = {
            table_name: ([{"id": "value"}] if populated else [])
            for _, _, table_name, _ in (
                SupabaseAssessmentRuntimeReadinessService.TABLE_PROBES
            )
        }

    def table(self, table_name):
        return Query(self, table_name)

    def rpc(self, function_name, parameters):
        self.calls.append(("rpc", function_name, parameters))
        return RpcQuery(self, function_name)


def test_readiness_report_is_operational_when_contracts_and_data_exist() -> None:
    report = SupabaseAssessmentRuntimeReadinessService(
        client=Client(populated=True)
    ).inspect()

    assert len(report.checks) == 15
    assert report.passed_count == 15
    assert report.warning_count == 0
    assert report.blocked_count == 0
    assert report.is_operational is True


def test_empty_business_data_is_warning_not_schema_failure() -> None:
    report = SupabaseAssessmentRuntimeReadinessService(
        client=Client(populated=False)
    ).inspect()

    assert report.blocked_count == 0
    assert report.warning_count == 4
    assert report.passed_count == 11
    assert report.is_operational is False


def test_missing_table_is_reported_as_blocked() -> None:
    client = Client()
    client.failed_tables.add("assessment_exam_snapshots")

    report = SupabaseAssessmentRuntimeReadinessService(
        client=client
    ).inspect()

    assert report.blocked_count == 2
    assert any(
        item.check_code == "schema_snapshots"
        and item.status == "BLOCKED"
        for item in report.checks
    )


def test_missing_hash_rpc_is_reported_as_blocked() -> None:
    client = Client()
    client.failed_rpcs.add("assessment_exam_snapshot_hash_matches")

    report = SupabaseAssessmentRuntimeReadinessService(
        client=client
    ).inspect()

    assert any(
        item.check_code == "rpc_snapshot_hash"
        and item.status == "BLOCKED"
        for item in report.checks
    )


def test_missing_private_bucket_is_reported_as_blocked() -> None:
    client = Client()
    client.storage_fails = True

    report = SupabaseAssessmentRuntimeReadinessService(
        client=client
    ).inspect()

    assert any(
        item.check_code == "storage_template_assets"
        and item.status == "BLOCKED"
        for item in report.checks
    )


def test_diagnostics_use_only_read_operations() -> None:
    source = Path(
        "src/assessment_generation_v2/services/"
        "assessment_runtime_readiness_service.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        ".insert(",
        ".update(",
        ".delete(",
        ".upsert(",
        "apply_migration",
    ):
        assert forbidden not in source


class Metric:
    def __init__(self, parent):
        self.parent = parent

    def metric(self, label, value):
        self.parent.metrics.append((label, value))


class FakeStreamlit:
    def __init__(self):
        self.messages = []
        self.metrics = []
        self.frames = []

    def title(self, value):
        self.messages.append(("title", value))

    def subheader(self, value):
        self.messages.append(("subheader", value))

    def caption(self, value):
        self.messages.append(("caption", value))

    def warning(self, value):
        self.messages.append(("warning", value))

    def error(self, value):
        self.messages.append(("error", value))

    def success(self, value):
        self.messages.append(("success", value))

    def info(self, value):
        self.messages.append(("info", value))

    def columns(self, count):
        return tuple(Metric(self) for _ in range(count))

    def dataframe(self, value, **kwargs):
        self.frames.append((value, kwargs))


class ReportService:
    def __init__(self, status):
        self.status = status

    def inspect(self):
        return AssessmentRuntimeReadinessReport(
            checks=(
                AssessmentRuntimeReadinessCheck(
                    "sample",
                    "Kiểm tra mẫu",
                    self.status,
                    "Chi tiết kiểm tra.",
                ),
            )
        )


def test_admin_page_renders_blocked_guidance() -> None:
    st = FakeStreamlit()

    render_admin_assessment_runtime_readiness(
        st,
        client=object(),
        service=ReportService("BLOCKED"),
    )

    assert ("Bị chặn", 1) in st.metrics
    assert any(kind == "error" for kind, _ in st.messages)
    assert st.frames[0][0][0]["Trạng thái"] == "Bị chặn"


def test_admin_page_renders_operational_success() -> None:
    st = FakeStreamlit()

    render_admin_assessment_runtime_readiness(
        st,
        client=object(),
        service=ReportService("PASS"),
    )

    assert any(kind == "success" for kind, _ in st.messages)


def test_system_health_is_wired_to_assessment_diagnostics() -> None:
    source = Path("src/portal_v2/ui/admin_shell.py").read_text(
        encoding="utf-8-sig"
    )

    assert "render_admin_assessment_runtime_readiness(" in source
    assert "page.page_id == ADMIN_PAGE_SYSTEM_HEALTH" in source


def test_template_catalog_uses_real_schema_column() -> None:
    source = Path(
        "src/portal_v2/ui/assessment_document_export_streamlit.py"
    ).read_text(encoding="utf-8")

    assert "template_code,template_name,authority_scope" in source
    assert '.order("template_name")' in source
    assert 'row.get("display_name")' not in source
