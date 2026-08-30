from __future__ import annotations

from portal_v2.context.canonical_code_catalog import CanonicalCodeDefinition


class SupabaseCanonicalCodeRepository:
    TABLE = "canonical_code_registry"

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _from_row(row):
        return CanonicalCodeDefinition(
            namespace=str(row["namespace"]),
            code=str(row["code"]),
            label=str(row["label"]),
            active=str(row.get("status", "ACTIVE")).upper() == "ACTIVE",
            rule_version=(
                str(row["rule_version"])
                if row.get("rule_version") is not None
                else None
            ),
            metadata=dict(row.get("metadata") or {}),
        )

    def list_codes(self, *, namespace=None, include_inactive=False):
        query=self.client.table(self.TABLE).select("namespace,code,label,status,rule_version,metadata")
        if namespace is not None:
            query=query.eq("namespace",namespace)
        if not include_inactive:
            query=query.eq("status","ACTIVE")
        response=query.order("namespace").order("code").execute()
        return tuple(self._from_row(row) for row in (response.data or ()))

    def update_code_lifecycle(self, *, namespace: str, code: str, label: str, status: str, rule_version: str | None = None, metadata: dict | None = None) -> None:
        normalized_status = str(status).strip().upper()
        if normalized_status not in {"ACTIVE", "INACTIVE"}:
            raise ValueError("canonical code status must be ACTIVE or INACTIVE")
        payload = {"label": str(label).strip(), "status": normalized_status, "rule_version": (str(rule_version).strip() or None) if rule_version is not None else None, "metadata": metadata or {}}
        if not payload["label"]:
            raise ValueError("canonical code label is required")
        self.client.table(self.TABLE).update(payload).eq("namespace", str(namespace).strip()).eq("code", str(code).strip()).execute()

    def get_code(self, *, namespace, code):
        response=(self.client.table(self.TABLE)
            .select("namespace,code,label,status,rule_version,metadata")
            .eq("namespace",namespace).eq("code",code)
            .limit(1).execute())
        rows=response.data or ()
        return self._from_row(rows[0]) if rows else None

    def save_code(self, definition):
        payload={
            "namespace":definition.namespace,
            "code":definition.code,
            "label":definition.label,
            "status":"ACTIVE" if definition.active else "INACTIVE",
        }
        response=(self.client.table(self.TABLE)
            .upsert(payload,on_conflict="namespace,code")
            .execute())
        rows=response.data or ()
        return self._from_row(rows[0]) if rows else definition
