from __future__ import annotations

import streamlit as st


def render_admin_user_registration_review(*, client) -> None:
    st.title("Duyệt đăng ký người dùng")
    st.caption(
        "ADMIN xét duyệt đăng ký. Chỉ khi APPROVED hệ thống mới "
        "kích hoạt quyền TEACHER và tạo/cập nhật hồ sơ giáo viên."
    )

    try:
        response = (
            client.table("portal_user_registrations")
            .select(
                "registration_id,user_id,email,full_name,school_name,"
                "requested_teacher_code,status,submitted_at"
            )
            .eq("status", "PENDING")
            .order("submitted_at", desc=False)
            .execute()
        )
        rows = getattr(response, "data", None) or []
    except Exception as error:
        st.error(f"Không thể đọc danh sách đăng ký: {error}")
        return

    if not rows:
        st.info("Hiện không có đăng ký nào chờ duyệt.")
        return

    for row in rows:
        registration_id = str(row["registration_id"])
        with st.container(border=True):
            st.markdown(f"**{row.get('full_name') or 'Chưa có họ tên'}**")
            st.write(f"Email: {row.get('email') or '—'}")
            st.write(f"Trường: {row.get('school_name') or '—'}")
            st.write(
                f"Mã giáo viên đề nghị: "
                f"{row.get('requested_teacher_code') or '—'}"
            )

            teacher_code = st.text_input(
                "Mã giáo viên",
                value=row.get("requested_teacher_code") or "",
                key=f"registration_teacher_code_{registration_id}",
            )
            full_name = st.text_input(
                "Họ và tên xác nhận",
                value=row.get("full_name") or "",
                key=f"registration_full_name_{registration_id}",
            )
            school_name = st.text_input(
                "Trường/đơn vị",
                value=row.get("school_name") or "",
                key=f"registration_school_name_{registration_id}",
            )
            note = st.text_area(
                "Ghi chú xét duyệt",
                key=f"registration_note_{registration_id}",
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "Phê duyệt",
                    type="primary",
                    key=f"approve_registration_{registration_id}",
                    use_container_width=True,
                ):
                    if not teacher_code.strip():
                        st.error("Cần nhập mã giáo viên trước khi phê duyệt.")
                    elif not full_name.strip():
                        st.error("Cần nhập họ và tên trước khi phê duyệt.")
                    else:
                        try:
                            client.rpc(
                                "review_portal_user_registration",
                                {
                                    "p_registration_id": registration_id,
                                    "p_decision": "APPROVED",
                                    "p_teacher_code": teacher_code.strip(),
                                    "p_full_name": full_name.strip(),
                                    "p_school_name": school_name.strip() or None,
                                    "p_review_note": note.strip() or None,
                                },
                            ).execute()
                            st.success("Đã phê duyệt và kích hoạt tài khoản.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"Không thể phê duyệt: {error}")

            with c2:
                if st.button(
                    "Từ chối",
                    key=f"reject_registration_{registration_id}",
                    use_container_width=True,
                ):
                    try:
                        client.rpc(
                            "review_portal_user_registration",
                            {
                                "p_registration_id": registration_id,
                                "p_decision": "REJECTED",
                                "p_teacher_code": None,
                                "p_full_name": None,
                                "p_school_name": None,
                                "p_review_note": note.strip() or None,
                            },
                        ).execute()
                        st.success("Đã từ chối đăng ký.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Không thể từ chối: {error}")
