"""Teacher owned classroom stages linked to lesson activities."""

from uuid import uuid4

TOOL_LABELS = {"QUESTION_STAGE": "Trình chiếu câu hỏi", "LUCKY_WHEEL": "Vòng quay may mắn", "GAMESHOW": "Gameshow"}
ACTIVITIES = {"MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG"}


def validate_tool(tool):
    if not isinstance(tool, dict) or set(tool) != {"id", "activity", "kind", "session_id", "title"}:
        raise ValueError("Thẻ công cụ không hợp lệ.")
    if tool["kind"] not in TOOL_LABELS or tool["activity"] not in ACTIVITIES:
        raise ValueError("Loại công cụ hoặc hoạt động không hợp lệ.")
    for key, limit in (("id", 80), ("session_id", 80), ("title", 200)):
        if not isinstance(tool[key], str) or not tool[key] or len(tool[key]) > limit:
            raise ValueError("Thông tin thẻ công cụ không hợp lệ.")
    return tool


def add_tool(draft, *, activity, kind, session_id, title):
    tools = draft.setdefault("classroom_tools", [])
    if len(tools) >= 40:
        raise ValueError("Bài giảng chỉ nhận tối đa 40 thẻ công cụ.")
    tool = validate_tool({"id": str(uuid4()), "activity": activity, "kind": kind,
                          "session_id": session_id, "title": title})
    tools.append(tool)
    return tool


def owned_sessions(client, user_id):
    return (client.table("teacher_classroom_sessions")
            .select("session_id,title,status,class_id")
            .eq("teacher_user_id", user_id).limit(50).execute().data or [])


def build_owned_stage(client, user_id, tool):
    """Recheck ownership and approval at launch, never trust imported draft IDs."""
    validate_tool(tool)
    from portal_v2.ui.teacher_classroom_streamlit import (
        _question_bank, _detail, build_offline_presentation,
    )
    sessions = (client.table("teacher_classroom_sessions")
                .select("session_id,title")
                .eq("teacher_user_id", user_id).eq("session_id", tool["session_id"])
                .limit(1).execute().data or [])
    if not sessions:
        raise ValueError("Buổi học không còn thuộc tài khoản giáo viên này.")
    entries = (client.table("teacher_classroom_questions")
               .select("position,question_version_id")
               .eq("session_id", tool["session_id"]).order("position").limit(100).execute().data or [])
    bank = {str(row["question_version_id"]): row for row in _question_bank(client, user_id)}
    slides = []
    for entry in entries:
        version = str(entry["question_version_id"])
        row = bank.get(version)
        if not row or row["item"].get("lifecycle_status") != "ACTIVE" or row["item"].get("subject_code") != "MATH" or int(row["item"].get("grade_level", 0)) not in (6, 7, 8, 9):
            raise ValueError("Buổi học có câu hỏi không còn được duyệt hoặc không thuộc Toán 6–9.")
        slides.append((row, _detail(client, version)))
    if not slides:
        raise ValueError("Buổi học chưa có câu hỏi được duyệt.")
    title = sessions[0]["title"]
    if tool["kind"] == "LUCKY_WHEEL":
        from portal_v2.ui.classroom_lucky_wheel import build_offline_wheel
        return build_offline_wheel(title, slides, session_id=tool["session_id"])
    if tool["kind"] == "GAMESHOW":
        from portal_v2.ui.classroom_gameshow_core import build_offline_gameshow
        return build_offline_gameshow(title, slides, session_id=tool["session_id"])
    return build_offline_presentation(title, slides)


def render_classroom_tools(st, draft, client, user_id, activity):
    with st.container():
        st.caption("Dùng buổi học đã chuẩn bị ở Lớp học ôn tập. Câu hỏi được kiểm tra lại khi mở sân khấu.")
        try:
            sessions = owned_sessions(client, user_id)
        except Exception as exc:
            st.warning(f"Chưa đọc được buổi học: {exc}")
            return
        if sessions:
            chosen = st.selectbox("Buổi học có câu hỏi đã duyệt", sessions,
                                  format_func=lambda row: row["title"] + " · " + str(row.get("class_id") or ""),
                                  key="lesson_tool_session")
            kind = st.selectbox("Công cụ", list(TOOL_LABELS), format_func=TOOL_LABELS.get,
                                key="lesson_tool_kind")
            if st.button("Thêm công cụ vào hoạt động này", key="lesson_tool_add"):
                try:
                    add_tool(draft, activity=activity, kind=kind,
                             session_id=str(chosen["session_id"]), title=chosen["title"])
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("Chưa có buổi học. Vào Lớp học ôn tập để tạo và chọn câu hỏi đã duyệt.")
    for tool in list(draft.get("classroom_tools", [])):
        if tool["activity"] != activity:
            continue
        with st.expander(f"{TOOL_LABELS[tool['kind']]} · {tool['title']}", expanded=False):
            if st.button("Mở sân khấu", key="lesson_tool_open_" + tool["id"]):
                try:
                    st.session_state["lesson_tool_stage"] = (tool["id"], build_owned_stage(client, user_id, tool))
                except Exception as exc:
                    st.error(f"Chưa mở được sân khấu: {exc}")
            stage = st.session_state.get("lesson_tool_stage")
            if stage and stage[0] == tool["id"]:
                st.download_button("Tải sân khấu HTML", stage[1], file_name="san-khau-lop-hoc.html",
                                   mime="text/html", key="lesson_tool_download_" + tool["id"])
                st.components.v1.html(stage[1].decode("utf-8"), height=800, scrolling=True)
            if st.button("Bỏ công cụ khỏi hoạt động", key="lesson_tool_remove_" + tool["id"]):
                draft["classroom_tools"].remove(tool)
                st.session_state.pop("lesson_tool_stage", None)
                st.rerun()
