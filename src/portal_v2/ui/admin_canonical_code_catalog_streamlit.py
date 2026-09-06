from portal_v2.context.supabase_canonical_code_repository import SupabaseCanonicalCodeRepository


def _canonical_code_value(item, field_name: str, default=None):
    if isinstance(item, dict):
        return item.get(field_name, default)
    return getattr(item, field_name, default)

def render_admin_canonical_code_catalog(st, *, client) -> None:
    st.title("Quản trị Bộ mã Canonical")
    st.caption("Management plane cho Bộ mã Canonical; không tạo authority nghiệp vụ thứ hai.")
    if client is None:
        st.warning("Chưa có kết nối dữ liệu.")
        return
    repo=SupabaseCanonicalCodeRepository(client)
    try:
        rows=repo.list_codes()
    except Exception as error:
        st.error(f"Không thể tải Bộ mã Canonical: {error}")
        return
    namespaces=("Tất cả",)+tuple(sorted({str(_canonical_code_value(r, "namespace", "")) for r in rows if _canonical_code_value(r, "namespace")}))
    ns=st.selectbox("Nhóm mã",namespaces,key="admin_canonical_code_namespace_filter")
    status=st.selectbox("Trạng thái",("Tất cả","ACTIVE","INACTIVE"),key="admin_canonical_code_status_filter")
    visible=tuple(r for r in rows if (ns=="Tất cả" or _canonical_code_value(r, "namespace")==ns) and (status=="Tất cả" or _canonical_code_value(r, "status")==status))
    cols=st.columns(3)
    cols[0].metric("Tổng mã",len(rows))
    cols[1].metric("Đang hoạt động",sum(_canonical_code_value(r, "status")=="ACTIVE" for r in rows))
    cols[2].metric("Ngừng sử dụng",sum(_canonical_code_value(r, "status")=="INACTIVE" for r in rows))
    st.dataframe([{"Nhóm":_canonical_code_value(r, "namespace"),"Mã":_canonical_code_value(r, "code"),"Tên":_canonical_code_value(r, "label"),"Trạng thái":_canonical_code_value(r, "status"),"Phiên bản quy tắc":_canonical_code_value(r, "rule_version") or "—"} for r in visible],hide_index=True,use_container_width=True)
    st.info("B6B mở catalog an toàn. Thêm/sửa, ACTIVE/INACTIVE, generation rule và mapping sẽ đi qua service quản trị ở bước kế tiếp; không xóa hay tự đổi ID đã phát hành.")

    st.divider()
    st.subheader("Thêm mã mới")
    with st.form("admin_canonical_code_create_form"):
        new_namespace=st.text_input("Namespace",key="admin_canonical_new_namespace")
        new_code=st.text_input("Mã canonical",key="admin_canonical_new_code")
        new_label=st.text_input("Tên hiển thị",key="admin_canonical_new_label")
        create=st.form_submit_button("Thêm mã")
    if create:
        try:
            from portal_v2.context.canonical_code_catalog import CanonicalCodeDefinition
            repo.save_code(CanonicalCodeDefinition(new_namespace.strip(),new_code.strip(),new_label.strip(),True))
            st.success("Đã thêm mã canonical.")
            st.rerun()
        except Exception as error:
            st.error(f"Không thể thêm mã: {error}")

    if rows:
        st.divider()
        st.subheader("Điều chỉnh vòng đời mã")
        target=st.selectbox("Chọn mã",rows,format_func=lambda r:f'{_canonical_code_value(r, "namespace")} · {_canonical_code_value(r, "code")} — {_canonical_code_value(r, "label")}',key="admin_canonical_lifecycle_target")
        with st.form("admin_canonical_code_lifecycle_form"):
            edit_label=st.text_input("Tên hiển thị",value=str(_canonical_code_value(target, "label") or ""))
            edit_status=st.selectbox("Trạng thái",("ACTIVE","INACTIVE"),index=0 if _canonical_code_value(target, "status")=="ACTIVE" else 1)
            edit_rule=st.text_input("Phiên bản quy tắc",value=str(_canonical_code_value(target, "rule_version") or "1"))
            save=st.form_submit_button("Lưu thay đổi")
        if save:
            try:
                repo.update_code_lifecycle(namespace=str(_canonical_code_value(target, "namespace") or ""),code=str(_canonical_code_value(target, "code") or ""),label=edit_label,status=edit_status,rule_version=edit_rule,metadata=dict(_canonical_code_value(target, "metadata") or {}))
                st.success("Đã cập nhật vòng đời mã. Canonical code/ID không bị thay đổi.")
                st.rerun()
            except Exception as error:
                st.error(f"Không thể cập nhật mã: {error}")

# V58_C5B7D_GROUPING_POLICY_ADMIN
_render_admin_canonical_code_catalog_before_grouping_policy = (
    render_admin_canonical_code_catalog
)


def _render_admin_lesson_plan_grouping_policy(st, *, client) -> None:
    from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import (
        SupabaseLessonPlanGroupingPolicyRepository,
    )
    from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
    from lesson_planning_v2.models.lesson_plan_grouping_policy_config import (
        LessonPlanGroupingPolicyConfig,
    )
    from portal_v2.context.supabase_canonical_code_repository import (
        SupabaseCanonicalCodeRepository,
    )
    from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
        SupabaseSubjectCatalogRepository,
    )
    from educational_planning_v2.models.subject_catalog import CatalogStatus

    st.divider()
    st.subheader("Chính sách nhóm giáo án")
    st.caption(
        "Cách soạn giáo án theo từng Môn/Phân môn. "
        "Cấu hình riêng của Phân môn được ưu tiên; nếu không có thì dùng mặc định của Môn."
    )

    policy_repo = SupabaseLessonPlanGroupingPolicyRepository(client)
    code_repo = SupabaseCanonicalCodeRepository(client)
    subject_repo = SupabaseSubjectCatalogRepository(client=client)

    try:
        configs = policy_repo.list_configs(include_inactive=True)
    except Exception as error:
        st.warning("Chưa đọc được cấu hình nhóm giáo án: " + str(error))
        return

    subject_items = tuple(subject_repo.list_subjects(status=CatalogStatus.ACTIVE))
    component_items = tuple(code_repo.list_codes(namespace="component"))

    subject_name_by_ref = {}
    for item in subject_items:
        subject_id = str(getattr(item, "subject_id", "") or "")
        subject_code = str(getattr(item, "code", "") or "")
        subject_name = str(getattr(item, "name", "") or subject_code or subject_id)
        if subject_id:
            subject_name_by_ref[subject_id] = subject_name
        if subject_code:
            subject_name_by_ref[subject_code] = subject_name

    component_name_by_ref = {}
    for item in component_items:
        code = str(getattr(item, "code", "") or "")
        label = str(getattr(item, "label", "") or code)
        if code:
            component_name_by_ref[code] = label

    mode_display = {
        LessonPlanGroupingMode.BY_PERIOD: "Soạn theo tiết",
        LessonPlanGroupingMode.BY_LESSON: "Soạn theo bài",
        LessonPlanGroupingMode.BY_WEEK: "Soạn theo tuần",
    }

    st.dataframe(
        [
            {
                "Môn": subject_name_by_ref.get(
                    str(item.subject_ref), str(item.subject_ref)
                ),
                "Phạm vi": (
                    "Mặc định của môn"
                    if not str(item.component_ref or "").strip()
                    else component_name_by_ref.get(
                        str(item.component_ref), str(item.component_ref)
                    )
                ),
                "Cách soạn": mode_display.get(item.mode, item.mode.value),
                "Trạng thái": "Đang áp dụng" if item.active else "Ngừng áp dụng",
            }
            for item in configs
        ],
        hide_index=True,
        use_container_width=True,
    )

    if not subject_items:
        st.info("Chưa có môn ACTIVE trong Danh mục môn học canonical.")
        return

    subjects = tuple(item.subject_id for item in subject_items)
    components = tuple(
        str(getattr(item, "code", "") or "")
        for item in component_items
        if str(getattr(item, "code", "") or "").strip()
    )
    subject_labels = {
        item.subject_id: f"{item.name} ({item.code})"
        for item in subject_items
    }
    component_labels = {
        str(getattr(item, "code", "") or ""): (
            f"{getattr(item, 'label', '')} ({getattr(item, 'code', '')})"
        )
        for item in component_items
        if str(getattr(item, "code", "") or "").strip()
    }

    mode_labels = {
        "Soạn theo tiết": LessonPlanGroupingMode.BY_PERIOD,
        "Soạn theo bài": LessonPlanGroupingMode.BY_LESSON,
        "Soạn theo tuần": LessonPlanGroupingMode.BY_WEEK,
    }
    default_component = "— Mặc định của môn —"

    _policy_proof = st.session_state.get(
        "_v58_c5e5d7_grouping_policy_read_after_write"
    )
    if _policy_proof:
        st.success("Đã xác minh lưu cấu hình và đọc lại từ Supabase.")
        st.code(_policy_proof)

    with st.form("admin_lesson_plan_grouping_policy_form"):
        subject_ref = st.selectbox(
            "Môn",
            subjects,
            format_func=lambda value: subject_labels.get(value, value),
        )
        component_ref = st.selectbox(
            "Phạm vi áp dụng",
            (default_component,) + components,
            format_func=lambda value: component_labels.get(value, value),
            help="Mặc định của môn áp dụng khi không có cấu hình riêng cho Phân môn.",
        )
        selected_component_code = (
            "" if component_ref == default_component else str(component_ref)
        )
        current_config = next(
            (
                item
                for item in configs
                if str(item.subject_ref) == str(subject_ref)
                and str(item.component_ref or "") == selected_component_code
            ),
            None,
        )

        mode_options = tuple(mode_labels)
        current_mode = (
            current_config.mode
            if current_config is not None
            else LessonPlanGroupingMode.BY_PERIOD
        )
        current_mode_label = next(
            (
                label
                for label, mode in mode_labels.items()
                if mode == current_mode
            ),
            mode_options[0],
        )
        mode_label = st.selectbox(
            "Cách soạn giáo án",
            mode_options,
            index=mode_options.index(current_mode_label),
            help=(
                "Soạn theo tiết: mỗi tiết PPCT là một nhóm giáo án. "
                "Soạn theo bài: các tiết cùng bài được gom chung. "
                "Soạn theo tuần: các tiết trong tuần được gom theo chính sách hiện có."
            ),
        )
        active = st.checkbox(
            "Áp dụng cấu hình này",
            value=(current_config.active if current_config is not None else True),
        )
        save = st.form_submit_button("Lưu cách soạn giáo án")

    if save:
        component_code = (
            "" if component_ref == default_component else str(component_ref)
        )
        try:
            policy_repo.upsert_config(
                LessonPlanGroupingPolicyConfig(
                    subject_ref=str(subject_ref),
                    component_ref=component_code,
                    mode=mode_labels[mode_label],
                    active=bool(active),
                )
            )
            _read_back = tuple(
                policy_repo.list_configs(include_inactive=True) or ()
            )
            _verified_policy = next(
                (
                    item
                    for item in _read_back
                    if str(item.subject_ref) == str(subject_ref)
                    and str(item.component_ref or "") == component_code
                ),
                None,
            )
            if _verified_policy is None:
                raise RuntimeError("READ_AFTER_WRITE_POLICY_NOT_FOUND")
            st.session_state[
                "_v58_c5e5d7_grouping_policy_read_after_write"
            ] = (
                f"subject_ref={_verified_policy.subject_ref!r}\n"
                f"component_ref={_verified_policy.component_ref!r}\n"
                f"mode={getattr(_verified_policy.mode, 'value', _verified_policy.mode)!r}\n"
                f"active={bool(_verified_policy.active)!r}\n"
                f"source={getattr(_verified_policy, 'source', None)!r}\n"
                f"version={getattr(_verified_policy, 'version', None)!r}"
            )
            st.success("Đã lưu cách soạn giáo án.")
            st.rerun()
        except Exception as error:
            st.error("Không thể lưu cách soạn giáo án: " + str(error))


def render_admin_canonical_code_catalog(st, *, client) -> None:
    _render_admin_canonical_code_catalog_before_grouping_policy(
        st,
        client=client,
    )
    if client is not None:
        _render_admin_lesson_plan_grouping_policy(st, client=client)


def render_admin_lesson_plan_grouping_policy(st, *, client) -> None:
    _render_admin_lesson_plan_grouping_policy(st, client=client)
