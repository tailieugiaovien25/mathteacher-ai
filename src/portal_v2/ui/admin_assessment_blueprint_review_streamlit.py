"""Authenticated blueprint submission and independent admin review."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _rows(response: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in (getattr(response, "data", None) or [])
            if isinstance(row, Mapping)]


def _review_action(
    *, reviewer_user_id: str, owner_user_id: str, status: str,
    setting_status: str, setting_locked: bool,
) -> str:
    if status == "DRAFT" and owner_user_id == reviewer_user_id:
        if setting_status != "APPROVED" or not setting_locked:
            return "SETTING_REQUIRED"
        return "SUBMIT"
    if status == "PENDING_REVIEW":
        return "ADMIN_REVIEW"
    return "READ_ONLY"


def render_admin_assessment_blueprint_review(
    st: Any, *, client: Any, reviewer_user_id: str
) -> None:
    st.subheader("Gửi duyệt và duyệt ma trận")
    if client is None:
        st.warning("Chưa có kết nối dữ liệu ma trận.")
        return
    try:
        versions = _rows(client.table("assessment_blueprint_versions")
                         .select("blueprint_version_id,blueprint_id,blueprint_name,review_status,setting_version_id,total_score,locked_at")
                         .order("created_at", desc=True).limit(50).execute())
        if not versions:
            st.info("Chưa có ma trận để gửi duyệt.")
            return
        labels = {f"{v['blueprint_name']} · {v['review_status']} · {str(v['blueprint_version_id'])[:8]}": v
                  for v in versions}
        version = labels[st.selectbox("Ma trận cần theo dõi", tuple(labels),
                                      key="admin_blueprint_review_select")]
        blueprint = _rows(client.table("assessment_blueprints")
                          .select("owner_user_id,blueprint_code")
                          .eq("blueprint_id", version["blueprint_id"]).execute())
        setting = (_rows(client.table("assessment_exam_setting_versions")
                         .select("review_status,locked_at,assessment_exam_setting_sets!inner(owner_user_id)")
                         .eq("setting_version_id", version["setting_version_id"]).execute())
                   if version.get("setting_version_id") else [])
        if len(blueprint) != 1:
            raise ValueError("Không xác định được chủ sở hữu ma trận")
        setting_status = setting[0]["review_status"] if len(setting) == 1 else "MISSING"
        owner = str(blueprint[0]["owner_user_id"])
        status = str(version["review_status"])
        action = _review_action(
            reviewer_user_id=reviewer_user_id, owner_user_id=owner,
            status=status, setting_status=setting_status,
            setting_locked=bool(setting and setting[0].get("locked_at")),
        )
    except Exception as error:
        st.error(f"Không tải được trạng thái ma trận: {error}")
        return
    st.write({"Mã ma trận": blueprint[0]["blueprint_code"],
              "Trạng thái ma trận": status, "Thiết đặt liên kết": setting_status,
              "Chủ sở hữu": owner, "Tổng điểm": version["total_score"]})
    if action == "SETTING_REQUIRED":
        st.info("Cần duyệt và khóa thiết đặt liên kết trước khi gửi ma trận đi duyệt.")
        setting_set = setting[0].get("assessment_exam_setting_sets") if setting else None
        if isinstance(setting_set, list):
            setting_set = setting_set[0] if len(setting_set) == 1 else None
        setting_owner = str(setting_set.get("owner_user_id")) if isinstance(setting_set, Mapping) else ""
        if (setting_status == "DRAFT" and owner == reviewer_user_id
                and setting_owner == reviewer_user_id):
            if st.button("Gửi thiết đặt liên kết đi duyệt", key="admin_blueprint_submit_setting"):
                try:
                    client.rpc("submit_assessment_exam_setting_for_review", {
                        "target_setting_version_id": version["setting_version_id"]
                    }).execute()
                except Exception as error:
                    st.error(f"Không thể gửi duyệt thiết đặt: {error}")
                else:
                    st.success("Đã gửi thiết đặt cho ADMIN duyệt.")
                    st.rerun()
        elif setting_status == "DRAFT":
            st.caption("Chủ sở hữu thiết đặt cần gửi hồ sơ đi duyệt.")
        return
    if action == "READ_ONLY":
        st.info("Trạng thái hiện tại không cho phép gửi hoặc ghi quyết định duyệt.")
        return
    if action == "SUBMIT":
        if st.button("Gửi ma trận đi duyệt", key="admin_blueprint_submit"):
            try:
                client.rpc("submit_assessment_blueprint_for_review", {
                    "target_blueprint_version_id": version["blueprint_version_id"]
                }).execute()
            except Exception as error:
                st.error(f"Không thể gửi duyệt ma trận: {error}")
            else:
                st.success("Đã gửi ma trận đi duyệt.")
                st.rerun()
        return
    decision = st.selectbox("Quyết định ma trận", ("APPROVED", "REVISION_REQUIRED", "REJECTED"),
                            key="admin_blueprint_review_decision")
    note = st.text_area("Nhận xét duyệt ma trận", key="admin_blueprint_review_note")
    if st.button("Ghi quyết định duyệt ma trận", key="admin_blueprint_review_save",
                 disabled=decision != "APPROVED" and not note.strip()):
        try:
            client.table("assessment_blueprint_reviews").insert({
                "blueprint_version_id": version["blueprint_version_id"],
                "reviewer_user_id": reviewer_user_id,
                "decision": decision,
                "review_note": note.strip() or "Đã kiểm tra ma trận và YCCĐ trong phiên quản trị.",
                "checklist": {"matrix_and_specification_checked": True},
            }).execute()
        except Exception as error:
            st.error(f"Không thể duyệt ma trận: {error}")
        else:
            st.success("Đã ghi quyết định duyệt ma trận.")
            st.rerun()
