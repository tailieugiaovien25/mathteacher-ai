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
    from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import SupabaseLessonPlanGroupingPolicyRepository
    from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
    from lesson_planning_v2.models.lesson_plan_grouping_policy_config import LessonPlanGroupingPolicyConfig
    from portal_v2.context.supabase_canonical_code_repository import SupabaseCanonicalCodeRepository

    st.divider()
    st.subheader("\u0043\u0068\u00ed\u006e\u0068 \u0073\u00e1\u0063\u0068 \u006e\u0068\u00f3\u006d \u0067\u0069\u00e1\u006f \u00e1\u006e")
    st.caption("\u0041\u0044\u004d\u0049\u004e \u0063\u1ea5\u0075 \u0068\u00ec\u006e\u0068 \u004d\u00f4\u006e/\u0050\u0068\u00e2\u006e \u006d\u00f4\u006e \u2192 \u0054\u0068\u0065\u006f PPCT, \u0054\u0068\u0065\u006f \u0062\u00e0\u0069 \u0068\u006f\u1eb7\u0063 \u0054\u0068\u0065\u006f \u0074\u0075\u1ea7\u006e \u0068\u006f\u1eb7\u0063 \u0054\u0068\u0065\u006f \u006b\u0068\u1ed1\u0069. \u004b\u0068\u1ed1\u0069 \u006c\u1edb\u0070 \u006c\u0075\u00f4\u006e \u006c\u00e0 \u0070\u0068\u1ea1\u006d \u0076\u0069 \u0062\u1eaft \u0062\u0075\u1ed9\u0063.")
    policy_repo=SupabaseLessonPlanGroupingPolicyRepository(client)
    code_repo=SupabaseCanonicalCodeRepository(client)
    try:
        configs=policy_repo.list_configs(include_inactive=True)
    except Exception as error:
        st.warning("\u0043\u0068\u01b0\u0061 \u0111\u1ecdc \u0111\u01b0\u1ee3\u0063 \u0063\u1ea5\u0075 \u0068\u00ec\u006e\u0068 \u006e\u0068\u00f3\u006d \u0067\u0069\u00e1\u006f \u00e1\u006e: "+str(error))
        return
    st.dataframe([{"\u004d\u00f4\u006e":x.subject_ref,"\u0050\u0068\u00e2\u006e \u006d\u00f4\u006e":x.component_ref or "\u2014","\u0043\u00e1\u0063\u0068 \u006e\u0068\u00f3\u006d":x.mode.value,"\u0054\u0072\u1ea1\u006e\u0067 \u0074\u0068\u00e1\u0069":"ACTIVE" if x.active else "INACTIVE"} for x in configs],hide_index=True,use_container_width=True)
    subject_items=tuple(code_repo.list_codes(namespace="subject"))
    component_items=tuple(code_repo.list_codes(namespace="component"))
    if not subject_items:
        st.info("\u0043\u0068\u01b0\u0061 \u0063\u00f3 \u006d\u00e3 \u006d\u00f4\u006e ACTIVE \u0074\u0072\u006f\u006e\u0067 \u0042\u1ed9 \u006d\u00e3 Canonical.")
        return
    subjects=tuple(x.code for x in subject_items)
    components=tuple(x.code for x in component_items)
    subject_labels={x.code:f"{x.label} ({x.code})" for x in subject_items}
    component_labels={x.code:f"{x.label} ({x.code})" for x in component_items}
    mode_labels={"\u0054\u0068\u0065\u006f \u0074\u0069\u1ebf\u0074 PPCT":LessonPlanGroupingMode.BY_PERIOD,"\u0054\u0068\u0065\u006f \u0062\u00e0\u0069":LessonPlanGroupingMode.BY_LESSON,"\u0054\u0068\u0065\u006f \u0074\u0075\u1ea7\u006e":LessonPlanGroupingMode.BY_WEEK,"\u0054\u0068\u0065\u006f \u006b\u0068\u1ed1\u0069":LessonPlanGroupingMode.BY_GRADE}
    default_component="\u2014 \u004d\u1eb7\u0063 \u0111\u1ecb\u006e\u0068 \u0063\u1ee7\u0061 \u006d\u00f4\u006e \u2014"
    with st.form("admin_lesson_plan_grouping_policy_form"):
        subject_ref=st.selectbox("\u004d\u00f4\u006e",subjects,format_func=lambda c:subject_labels.get(c,c))
        component_ref=st.selectbox("\u0050\u0068\u00e2\u006e \u006d\u00f4\u006e",(default_component,)+components,format_func=lambda c:component_labels.get(c,c))
        selected_component_code="" if component_ref==default_component else str(component_ref)
        current_config=next((item for item in configs if str(item.subject_ref)==str(subject_ref) and str(item.component_ref or "")==selected_component_code),None)
        mode_options=tuple(mode_labels)
        current_mode=current_config.mode if current_config is not None else LessonPlanGroupingMode.BY_PERIOD
        current_mode_label=next((label for label,mode in mode_labels.items() if mode==current_mode),mode_options[0])
        mode_label=st.selectbox("\u0043\u00e1\u0063\u0068 \u006e\u0068\u00f3\u006d \u0067\u0069\u00e1\u006f \u00e1\u006e",mode_options,index=mode_options.index(current_mode_label))
        active=st.checkbox("\u0110\u0061\u006e\u0067 \u0068\u006f\u1ea1\u0074 \u0111\u1ed9\u006e\u0067",value=(current_config.active if current_config is not None else True))
        save=st.form_submit_button("\u004c\u01b0\u0075 \u0063\u0068\u00ed\u006e\u0068 \u0073\u00e1\u0063\u0068")
    if save:
        component_code="" if component_ref==default_component else str(component_ref)
        try:
            policy_repo.upsert_config(LessonPlanGroupingPolicyConfig(subject_ref=str(subject_ref),component_ref=component_code,mode=mode_labels[mode_label],active=bool(active)))
            st.success("\u0110\u00e3 \u006c\u01b0\u0075 \u0063\u0068\u00ed\u006e\u0068 \u0073\u00e1\u0063\u0068 \u006e\u0068\u00f3\u006d \u0067\u0069\u00e1\u006f \u00e1\u006e.")
            st.rerun()
        except Exception as error:
            st.error("\u004b\u0068\u00f4\u006e\u0067 \u0074\u0068\u1ec3 \u006c\u01b0\u0075 \u0063\u0068\u00ed\u006e\u0068 \u0073\u00e1\u0063\u0068 \u006e\u0068\u00f3\u006d \u0067\u0069\u00e1\u006f \u00e1\u006e: "+str(error))

def render_admin_canonical_code_catalog(st, *, client) -> None:
    _render_admin_canonical_code_catalog_before_grouping_policy(
        st,
        client=client,
    )
    if client is not None:
        _render_admin_lesson_plan_grouping_policy(st, client=client)


def render_admin_lesson_plan_grouping_policy(st, *, client) -> None:
    _render_admin_lesson_plan_grouping_policy(st, client=client)
