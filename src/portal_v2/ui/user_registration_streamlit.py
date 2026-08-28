from __future__ import annotations

import streamlit as st


def render_user_registration(*, client) -> None:
    st.subheader("Đăng ký tài khoản")

    email = st.text_input(
        "Email",
        key="registration_email",
        placeholder="tenban@example.com",
    )
    password = st.text_input(
        "Mật khẩu",
        type="password",
        key="registration_password",
        help="Mật khẩu phải có ít nhất 6 ký tự.",
    )
    password2 = st.text_input(
        "Xác nhận mật khẩu",
        type="password",
        key="registration_password_confirm",
    )
    full_name = st.text_input("Họ và tên", key="registration_full_name")
    school_name = st.text_input(
        "Trường/đơn vị công tác",
        key="registration_school_name",
    )
    teacher_code = st.text_input(
        "Mã giáo viên (nếu có)",
        key="registration_teacher_code",
    )

    st.caption(
        "Sau khi đăng ký và xác thực email, tài khoản sẽ ở trạng thái "
        "chờ ADMIN xét duyệt. Người đăng ký không tự cấp quyền truy cập."
    )

    if st.button("Gửi đăng ký", type="primary", use_container_width=True):
        email = email.strip()

        if not email:
            st.error("Email không được để trống.")
            return
        if len(password) < 6:
            st.error("Mật khẩu phải có ít nhất 6 ký tự.")
            return
        if password != password2:
            st.error("Mật khẩu xác nhận chưa khớp.")
            return
        if not full_name.strip():
            st.error("Họ và tên không được để trống.")
            return

        try:
            response = client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name.strip(),
                            "school_name": school_name.strip(),
                            "requested_teacher_code": teacher_code.strip(),
                        }
                    },
                }
            )
            user = getattr(response, "user", None)
            session = getattr(response, "session", None)

            if user is None:
                raise RuntimeError("Supabase không trả về tài khoản đăng ký hợp lệ.")

            if session is None:
                st.success(
                    "Đăng ký Auth thành công. Hãy kiểm tra email để xác thực, "
                    "sau đó đăng nhập để hoàn tất yêu cầu chờ ADMIN duyệt."
                )
                return

            client.rpc(
                "create_or_refresh_own_portal_registration",
                {
                    "p_full_name": full_name.strip(),
                    "p_school_name": school_name.strip() or None,
                    "p_requested_teacher_code": teacher_code.strip() or None,
                },
            ).execute()
            st.success("Đã gửi đăng ký. Tài khoản đang chờ ADMIN xét duyệt.")
        except Exception as error:
            st.error(f"Không thể đăng ký tài khoản: {error}")


def render_registration_credentials() -> None:
    st.text_input(
        "Email đăng ký",
        key="registration_email",
    )
    st.text_input(
        "Mật khẩu",
        type="password",
        key="registration_password",
    )
    st.text_input(
        "Nhập lại mật khẩu",
        type="password",
        key="registration_password_confirm",
    )
