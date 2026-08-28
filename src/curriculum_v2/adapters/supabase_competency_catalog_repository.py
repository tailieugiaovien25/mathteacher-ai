from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from curriculum_v2.models.competency_catalog import CompetencyFramework, CompetencyIndicator

class SupabaseCompetencyCatalogRepository:
    FRAMEWORK_TABLE="competency_frameworks"
    INDICATOR_TABLE="competency_indicators"
    COMPONENT_TABLE="competency_components"

    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client=client

    @staticmethod
    def _rows(response: Any) -> list[Mapping[str, Any]]:
        data=getattr(response,"data",None)
        if data is None and isinstance(response,Mapping):
            data=response.get("data")
        if data is None:
            return []
        if not isinstance(data,list):
            raise ValueError("Supabase response data must be list")
        return [r for r in data if isinstance(r,Mapping)]

    def list_frameworks(self) -> tuple[CompetencyFramework,...]:
        response=self._client.table(self.FRAMEWORK_TABLE).select("*").order("canonical_code").execute()
        return tuple(CompetencyFramework(
            framework_id=str(r["framework_id"]), canonical_code=str(r["canonical_code"]), framework_name=str(r["framework_name"]),
            framework_type=str(r["framework_type"]), subject_id=r.get("subject_id"), version_label=str(r.get("version_label","1.0")),
            provenance_status=str(r.get("provenance_status","REVIEWED")), status=str(r.get("status","ACTIVE")), metadata=dict(r.get("metadata") or {})
        ) for r in self._rows(response))


    def list_components(self, *, framework_id: str) -> tuple[Mapping[str, Any],...]:
        framework_id=framework_id.strip()
        if not framework_id:
            raise ValueError("framework_id must not be empty")
        response=(
            self._client.table(self.COMPONENT_TABLE)
            .select("component_id,canonical_code,component_name,sequence_number,status")
            .eq("framework_id",framework_id)
            .eq("status","ACTIVE")
            .order("sequence_number")
            .execute()
        )
        return tuple(self._rows(response))

    def list_indicators(self, *, framework_id: str | None=None, status: str | None=None) -> tuple[CompetencyIndicator,...]:
        query=self._client.table(self.INDICATOR_TABLE).select("*")
        if framework_id:
            query=query.eq("framework_id",framework_id.strip())
        if status:
            query=query.eq("status",status.strip().upper())
        response=query.order("canonical_code").execute()
        return tuple(self._indicator(r) for r in self._rows(response))

    def save_indicator(self, *, indicator: CompetencyIndicator) -> CompetencyIndicator:
        if not isinstance(indicator,CompetencyIndicator):
            raise TypeError("indicator must be CompetencyIndicator")
        if not indicator.component_id:
            raise ValueError("component_id is required by the Educational Data Backbone")
        row={
            "indicator_id":indicator.indicator_id,"framework_id":indicator.framework_id,"component_id":indicator.component_id,
            "canonical_code":indicator.canonical_code,"source_code":indicator.source_code,"indicator_name":indicator.indicator_name,
            "indicator_text":indicator.indicator_text,"observable_flag":indicator.observable_flag,"assessable_flag":indicator.assessable_flag,
            "version_label":indicator.version_label,"provenance_status":indicator.provenance_status,"status":indicator.status,"metadata":indicator.metadata,
        }
        response=self._client.table(self.INDICATOR_TABLE).upsert(row,on_conflict="indicator_id").execute()
        rows=self._rows(response)
        return self._indicator(rows[0]) if rows else indicator

    def update_indicator_fields(self, *, indicator_id: str, values: Mapping[str, Any]) -> None:
        allowed={"canonical_code","indicator_name","indicator_text","source_code","status","provenance_status","version_label","replaced_by_indicator_id","metadata"}
        payload={k:v for k,v in values.items() if k in allowed}
        if not payload:
            raise ValueError("no allowed fields to update")
        self._client.table(self.INDICATOR_TABLE).update(payload).eq("indicator_id",indicator_id.strip()).execute()

    @staticmethod
    def _indicator(r: Mapping[str, Any]) -> CompetencyIndicator:
        return CompetencyIndicator(
            indicator_id=str(r["indicator_id"]),framework_id=str(r["framework_id"]),component_id=r.get("component_id"),
            canonical_code=str(r["canonical_code"]),source_code=r.get("source_code"),indicator_name=str(r["indicator_name"]),
            indicator_text=str(r["indicator_text"]),observable_flag=bool(r.get("observable_flag",True)),assessable_flag=bool(r.get("assessable_flag",True)),
            version_label=str(r.get("version_label","1.0")),provenance_status=str(r.get("provenance_status","REVIEWED")),
            status=str(r.get("status","ACTIVE")),metadata=dict(r.get("metadata") or {})
        )
