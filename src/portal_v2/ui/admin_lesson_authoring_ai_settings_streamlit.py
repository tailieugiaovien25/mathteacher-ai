from __future__ import annotations

from typing import Any


_STATE_KEY = "admin_lesson_authoring_ai_settings_v1"

_DEFAULTS = {
    "display_name": "Soạn bài cùng AI",
    "description": (
        "Hỗ trợ giáo viên xây dựng giáo án nhanh với AI dựa trên chương trình, "
        "sách giáo khoa và kho học liệu của hệ thống."
    ),
    "language": "Tiếng Việt",
    "tone": "Trang trọng (dành cho giáo án)",
    "content_length": "Trung bình",
    "suggestion_count": 2,
    "autosave": "Có (mỗi 30 giây)",
    "show_sources": "Có",
    "confirmation_policy": "Hiển thị cảnh báo & yêu cầu xác nhận",
    "ai_scope": "Gợi ý và hỗ trợ biên soạn",
    "competency_source": "Bộ mã Canonical của hệ thống",
    "content_source": "Nội dung dạy học Canonical + học liệu được phép",
    "lesson_structure": "Theo mẫu giáo án ADMIN đang áp dụng",
    "output_format": "Nội dung giáo án có cấu trúc",
    "context_sync": "Đồng bộ từ lịch/PPCT khi có",
    "standardization_handoff": "Cho phép chuyển sang Chuẩn hóa giáo án",
    "advanced_prompt_guard": True,
    "advanced_trace": False,
}


def _settings(st) -> dict[str, Any]:
    current = st.session_state.get(_STATE_KEY)
    if not isinstance(current, dict):
        current = dict(_DEFAULTS)
        st.session_state[_STATE_KEY] = current
    merged = dict(_DEFAULTS)
    merged.update(current)
    return merged


def render_admin_lesson_authoring_ai_settings(st, *, client=None) -> None:
    del client
    current = _settings(st)

    st.subheader("Cài đặt công cụ Soạn bài cùng AI")
    st.caption(
        "ADMIN thiết lập các tùy chọn mặc định và chính sách dùng chung khi "
        "giáo viên sử dụng công cụ Soạn bài cùng AI."
    )
    st.info(
        "Các thiết lập tại đây áp dụng cho USER khi soạn bài cùng AI. "
        "Nội dung AI sinh ra là gợi ý để giáo viên xem xét và chịu trách nhiệm "
        "cuối cùng trước khi lưu hoặc chuẩn hóa."
    )

    st.markdown("### Danh sách chức năng cài đặt")
    st.caption("Chọn nhóm chức năng cần thiết lập cho công cụ Soạn bài cùng AI.")

    (
        general_tab,
        ai_content_tab,
        format_tab,
        integration_tab,
        advanced_tab,
    ) = st.tabs(
        [
            "1. Thông tin chung",
            "2. AI & Nội dung",
            "3. Định dạng & Trình bày",
            "4. Tích hợp & Dữ liệu",
            "5. Nâng cao",
        ]
    )

    with st.form("admin_lesson_authoring_ai_settings_form"):
        with general_tab:
            st.markdown("### 1. Thông tin chung")
            st.caption(
                "Thiết lập các thông tin và tùy chọn chung khi giáo viên sử dụng "
                "công cụ Soạn bài cùng AI."
            )
            col1, col2 = st.columns(2)
            with col1:
                display_name = st.text_input(
                    "Tên công cụ hiển thị",
                    value=str(current["display_name"]),
                )
                language = st.selectbox(
                    "Ngôn ngữ mặc định",
                    ["Tiếng Việt", "Tiếng Anh"],
                    index=["Tiếng Việt", "Tiếng Anh"].index(
                        str(current["language"])
                        if str(current["language"]) in ["Tiếng Việt", "Tiếng Anh"]
                        else "Tiếng Việt"
                    ),
                )
                content_length_options = ["Ngắn gọn", "Trung bình", "Chi tiết"]
                content_length = st.selectbox(
                    "Độ dài mặc định mỗi mục nội dung",
                    content_length_options,
                    index=content_length_options.index(
                        str(current["content_length"])
                        if str(current["content_length"]) in content_length_options
                        else "Trung bình"
                    ),
                )
                autosave_options = [
                    "Không",
                    "Có (mỗi 30 giây)",
                    "Có (mỗi 60 giây)",
                ]
                autosave = st.selectbox(
                    "Tự động lưu bản nháp",
                    autosave_options,
                    index=autosave_options.index(
                        str(current["autosave"])
                        if str(current["autosave"]) in autosave_options
                        else "Có (mỗi 30 giây)"
                    ),
                )
            with col2:
                description = st.text_area(
                    "Mô tả công cụ (hiển thị cho USER)",
                    value=str(current["description"]),
                    height=100,
                )
                tone_options = [
                    "Trang trọng (dành cho giáo án)",
                    "Ngắn gọn, rõ ràng",
                    "Sư phạm, gợi mở",
                ]
                tone = st.selectbox(
                    "Giọng điệu mặc định khi sinh nội dung",
                    tone_options,
                    index=tone_options.index(
                        str(current["tone"])
                        if str(current["tone"]) in tone_options
                        else "Trang trọng (dành cho giáo án)"
                    ),
                )
                suggestion_count = st.number_input(
                    "Số lượng gợi ý phương án mặc định",
                    min_value=1,
                    max_value=5,
                    value=int(current["suggestion_count"]),
                    step=1,
                )
                show_source_options = ["Có", "Không"]
                show_sources = st.selectbox(
                    "Hiển thị gợi ý nguồn tham khảo",
                    show_source_options,
                    index=show_source_options.index(
                        str(current["show_sources"])
                        if str(current["show_sources"]) in show_source_options
                        else "Có"
                    ),
                )

            confirmation_options = [
                "Hiển thị cảnh báo & yêu cầu xác nhận",
                "Chỉ hiển thị cảnh báo",
                "Không hiển thị cảnh báo",
            ]
            confirmation_policy = st.radio(
                "Chính sách xác nhận khi dùng AI",
                confirmation_options,
                index=confirmation_options.index(
                    str(current["confirmation_policy"])
                    if str(current["confirmation_policy"]) in confirmation_options
                    else confirmation_options[0]
                ),
            )

        with ai_content_tab:
            st.markdown("### 2. AI & Nội dung")
            st.caption(
                "Quy định phạm vi AI được hỗ trợ và nguồn nội dung mà AI được phép sử dụng."
            )
            ai_scope_options = [
                "Gợi ý và hỗ trợ biên soạn",
                "Sinh bản nháp hoàn chỉnh để giáo viên rà soát",
                "Chỉ gợi ý từng mục theo yêu cầu",
            ]
            ai_scope = st.selectbox(
                "Phạm vi hỗ trợ của AI",
                ai_scope_options,
                index=ai_scope_options.index(
                    str(current["ai_scope"])
                    if str(current["ai_scope"]) in ai_scope_options
                    else ai_scope_options[0]
                ),
            )
            competency_source = st.selectbox(
                "Nguồn năng lực/phẩm chất",
                [
                    "Bộ mã Canonical của hệ thống",
                    "Theo nội dung bài học đang chọn",
                ],
                index=0,
            )
            content_source = st.selectbox(
                "Nguồn nội dung",
                [
                    "Nội dung dạy học Canonical + học liệu được phép",
                    "Chỉ nội dung dạy học Canonical",
                    "Chỉ dữ liệu người dùng cung cấp",
                ],
                index=0,
            )

        with format_tab:
            st.markdown("### 3. Định dạng & Trình bày")
            st.caption(
                "Thiết lập cấu trúc đầu ra trước khi chuyển sang bước Chuẩn hóa giáo án."
            )
            lesson_structure = st.selectbox(
                "Cấu trúc giáo án",
                [
                    "Theo mẫu giáo án ADMIN đang áp dụng",
                    "Theo cấu trúc bài soạn hiện tại",
                ],
                index=0,
            )
            output_format = st.selectbox(
                "Dạng nội dung đầu ra",
                [
                    "Nội dung giáo án có cấu trúc",
                    "Bản nháp văn bản tự do",
                ],
                index=0,
            )

        with integration_tab:
            st.markdown("### 4. Tích hợp & Dữ liệu")
            st.caption(
                "Quản lý các luồng đồng bộ dữ liệu vào/ra của công cụ Soạn bài cùng AI."
            )
            context_sync = st.selectbox(
                "Đồng bộ ngữ cảnh",
                [
                    "Đồng bộ từ lịch/PPCT khi có",
                    "Chỉ dùng ngữ cảnh giáo viên chọn thủ công",
                ],
                index=0,
            )
            standardization_handoff = st.selectbox(
                "Chuyển sang Chuẩn hóa giáo án",
                ["Cho phép chuyển sang Chuẩn hóa giáo án", "Không cho phép"],
                index=0,
            )

        with advanced_tab:
            st.markdown("### 5. Nâng cao")
            st.caption(
                "Các thiết lập kỹ thuật chỉ dành cho ADMIN; không hiển thị trong luồng USER."
            )
            advanced_prompt_guard = st.checkbox(
                "Bật lớp kiểm soát prompt/chỉ dẫn hệ thống",
                value=bool(current["advanced_prompt_guard"]),
            )
            advanced_trace = st.checkbox(
                "Ghi dấu chẩn đoán nội bộ khi sinh nội dung AI",
                value=bool(current["advanced_trace"]),
            )

        st.divider()
        preview_col, action_col = st.columns([2, 1])
        with preview_col:
            st.markdown("#### 👁 Xem trước hiển thị cho USER")
            st.write("✓ Tên công cụ:", display_name)
            st.write("✓ Ngôn ngữ:", language)
            st.write("✓ Giọng điệu:", tone)
            st.write("✓ Gợi ý phương án:", int(suggestion_count))
            st.write("✓ Tự động lưu:", autosave)
            st.write("✓ Hiển thị gợi ý nguồn:", show_sources)
            st.write("✓ Chính sách xác nhận:", confirmation_policy)

        with action_col:
            restore_default = st.form_submit_button(
                "↶ Khôi phục mặc định",
                use_container_width=True,
            )
            save_settings = st.form_submit_button(
                "💾 Lưu thiết lập",
                type="primary",
                use_container_width=True,
            )

    if restore_default:
        st.session_state[_STATE_KEY] = dict(_DEFAULTS)
        st.success("Đã khôi phục thiết lập mặc định của công cụ Soạn bài cùng AI.")
        st.rerun()

    if save_settings:
        st.session_state[_STATE_KEY] = {
            "display_name": display_name.strip() or _DEFAULTS["display_name"],
            "description": description.strip(),
            "language": language,
            "tone": tone,
            "content_length": content_length,
            "suggestion_count": int(suggestion_count),
            "autosave": autosave,
            "show_sources": show_sources,
            "confirmation_policy": confirmation_policy,
            "ai_scope": ai_scope,
            "competency_source": competency_source,
            "content_source": content_source,
            "lesson_structure": lesson_structure,
            "output_format": output_format,
            "context_sync": context_sync,
            "standardization_handoff": standardization_handoff,
            "advanced_prompt_guard": bool(advanced_prompt_guard),
            "advanced_trace": bool(advanced_trace),
        }
        st.success(
            "Đã lưu thiết lập Soạn bài cùng AI cho phiên làm việc hiện tại. "
            "Bước tiếp theo sẽ nối cấu hình này vào kho ADMIN và runtime USER."
        )
