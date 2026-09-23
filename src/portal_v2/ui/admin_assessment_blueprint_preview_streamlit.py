"""Read-only governed matrix/specification preview for an assessment blueprint."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from assessment_generation_v2.services.assessment_auto_blueprint_planner import (
    AutoBlueprintError,
    plan_blueprint,
)
from assessment_generation_v2.services.assessment_blueprint_document_generator import (
    BlueprintDocumentError,
    generate_blueprint_documents,
)


def _data(query: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in (query.execute().data or [])]


def render_blueprint_documents_preview(st: Any, *, client: Any) -> None:
    st.subheader("Ma trận và bản đặc tả tự sinh từ dữ liệu")
    st.caption("Bản xem trước từ ma trận, YCCĐ và thiết đặt đã lưu. AI chỉ nhận yêu cầu đã phân bổ; câu hỏi sinh ra cần duyệt riêng.")
    try:
        versions = _data(client.table("assessment_blueprint_versions")
                         .select("blueprint_version_id,blueprint_name,review_status,setting_version_id,total_score")
                         .order("created_at", desc=True).limit(30))
        if not versions:
            st.info("Chưa có ma trận đã lưu để xem trước.")
            return
        labels = {f"{row['blueprint_name']} · {row['review_status']} · {str(row['blueprint_version_id'])[:8]}": row
                  for row in versions}
        selected = labels[st.selectbox("Chọn ma trận", tuple(labels), key="admin_blueprint_preview_select")]
        version_id = selected["blueprint_version_id"]
        if not selected.get("setting_version_id"):
            raise BlueprintDocumentError("Ma trận chưa gắn với thiết đặt đề")
        setting = _data(client.table("assessment_exam_setting_versions")
                        .select("requirement_codes,total_score,subject_code,grade_level,profile_code")
                        .eq("setting_version_id", selected["setting_version_id"]))
        if len(setting) != 1:
            raise BlueprintDocumentError("Không đọc được phạm vi của thiết đặt")
        cells = _data(client.table("assessment_blueprint_cells").select(
            "sequence_number,topic_code,section_code,question_type_code,"
            "cognitive_level_code,question_count,response_count,target_score")
            .eq("blueprint_version_id", version_id).order("sequence_number"))
        links = _data(client.table("assessment_blueprint_requirement_links").select(
            "requirement_code,target_question_count,target_score")
            .eq("blueprint_version_id", version_id).order("sequence_number"))
        codes = [str(row["requirement_code"]) for row in links]
        if not codes or not set(codes) <= set(setting[0]["requirement_codes"] or []):
            raise BlueprintDocumentError("YCCĐ ma trận nằm ngoài thiết đặt")
        requirements = _data(client.table("assessment_learning_requirements").select(
            "requirement_code,topic_code,requirement_text,status,metadata,grade_level")
            .in_("requirement_code", codes))
        if any(int(row["grade_level"]) != int(setting[0]["grade_level"]) for row in requirements):
            raise BlueprintDocumentError("YCCĐ thuộc khối lớp khác")
        scope_topics = frozenset(str(row["topic_code"]) for row in requirements)
        result = generate_blueprint_documents(
            cells=cells, links=links,
            requirements={str(row["requirement_code"]): row for row in requirements},
            selected_topic_codes=scope_topics,
            selected_requirement_codes=frozenset(codes),
            expected_question_count=sum(int(row["question_count"]) for row in cells),
            expected_response_count=sum(int(row["response_count"]) for row in cells),
            expected_total_score=Decimal(str(setting[0]["total_score"])),
        )
    except (BlueprintDocumentError, ValueError, KeyError, TypeError) as error:
        st.warning(f"Chưa thể tạo ma trận/bản đặc tả chính xác: {error}")
        return
    except Exception as error:
        st.error(f"Không tải được dữ liệu ma trận: {error}")
        return

    render_auto_blueprint_suggestion(st, client=client, setting=setting[0])

    st.info(f"Bản xem trước · {result.total_questions} câu · {result.total_responses} ý · {result.total_score} điểm · {selected['review_status']}")
    st.markdown("**Ma trận theo chủ đề × mức độ**")
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in result.matrix_rows:
        key = (str(row['topic_code']), str(row['cognitive_level_code']))
        item = grouped.setdefault(key, {"Chủ đề": key[0], "Mức độ": key[1], "Số câu": 0, "Số ý": 0, "Điểm": Decimal(0)})
        item['Số câu'] += row['question_count']
        item['Số ý'] += row['response_count']
        item['Điểm'] += row['target_score']
    st.dataframe(list(grouped.values()), hide_index=True, use_container_width=True)
    st.markdown("**Bản đặc tả từng vị trí câu**")
    st.dataframe([{
        "Ô ma trận": brief.cell_sequence, "Vị trí": brief.slot_number,
        "Chủ đề": brief.topic_code, "YCCĐ": brief.requirement_code,
        "Nội dung YCCĐ": brief.requirement_text, "Dạng": brief.question_type_code,
        "Mức độ": brief.cognitive_level_code, "Điểm": str(brief.score),
    } for brief in result.specification_rows], hide_index=True, use_container_width=True)
    st.caption("Mỗi dòng đặc tả tạo ra một đầu vào AI với đúng YCCĐ, dạng câu, mức độ và điểm. Bản xem trước không tự sinh/duyệt câu hỏi.")


def render_auto_blueprint_suggestion(
    st: Any, *, client: Any, setting: dict[str, Any]
) -> None:
    """Propose matrix cells using profile and approved question evidence only."""
    st.markdown("**Đề xuất phân bổ ma trận tự động**")
    try:
        codes = [str(code) for code in setting.get("requirement_codes") or []]
        if not codes:
            raise AutoBlueprintError("Thiết đặt chưa có YCCĐ")
        profile = str(setting["profile_code"])
        sections = _data(client.table("assessment_profile_sections")
                         .select("section_code,question_type_code,question_count,response_count,section_score")
                         .eq("profile_code", profile).order("sequence_number"))
        levels = _data(client.table("assessment_profile_level_allocations")
                       .select("cognitive_level_code,target_score")
                       .eq("profile_code", profile))
        canonical = _data(client.table("assessment_learning_requirements")
                          .select("requirement_code,topic_code,requirement_text,status,grade_level,metadata")
                          .in_("requirement_code", codes))
        by_code = {str(row["requirement_code"]): row for row in canonical}
        examples = _data(client.table("assessment_question_requirement_links")
                         .select("question_version_id,requirement_code")
                         .in_("requirement_code", codes).eq("link_role", "PRIMARY")
                         .limit(1000))
        if len(examples) == 1000:
            raise AutoBlueprintError("Quá nhiều câu mẫu; cần phân trang dữ liệu")
        version_ids = list({str(row["question_version_id"]) for row in examples})
        if not version_ids:
            raise AutoBlueprintError("Chưa có câu mẫu đã duyệt cho phạm vi này")
        versions = _data(client.table("assessment_question_versions")
                         .select("question_version_id,question_id,question_type_code,cognitive_level_code,review_status,locked_at")
                         .in_("question_version_id", version_ids).eq("review_status", "APPROVED")
                         .not_.is_("locked_at", "null"))
        version_by_id = {str(row["question_version_id"]): row for row in versions}
        question_ids = list({str(row["question_id"]) for row in versions})
        items = (_data(client.table("assessment_question_items")
                       .select("question_id,grade_level,lifecycle_status")
                       .in_("question_id", question_ids).eq("lifecycle_status", "ACTIVE"))
                 if question_ids else [])
        allowed_questions = {str(row["question_id"]) for row in items
                             if int(row["grade_level"]) == int(setting["grade_level"])}
        section_by_type = {str(s["question_type_code"]): str(s["section_code"])
                           for s in sections}
        evidence: dict[str, set[tuple[str, str]]] = {}
        for link in examples:
            version = version_by_id.get(str(link["question_version_id"]))
            if not version or str(version["question_id"]) not in allowed_questions:
                continue
            section_code = section_by_type.get(str(version["question_type_code"]))
            if section_code:
                evidence.setdefault(str(link["requirement_code"]), set()).add(
                    (section_code, str(version["cognitive_level_code"])))
        missing = sorted(set(codes) - set(evidence))
        eligible = [{"requirement_code": code, "topic_code": by_code[code]["topic_code"],
                     "eligibility": sorted(pairs)}
                    for code, pairs in sorted(evidence.items())
                    if code in by_code and by_code[code].get("status") == "ACTIVE"
                    and by_code[code].get("metadata", {}).get("canonical_status") == "VERIFIED"
                    and int(by_code[code]["grade_level"]) == int(setting["grade_level"])]
        proposed = plan_blueprint(
            sections=sections,
            cognitive_targets={str(row["cognitive_level_code"]): Decimal(str(row["target_score"]))
                               for row in levels},
            requirements=eligible,
            total_score=Decimal(str(setting["total_score"])),
        )
    except (AutoBlueprintError, ValueError, KeyError, TypeError) as error:
        st.warning(f"Chưa thể tự phân bổ an toàn: {error}")
        return
    except Exception as error:
        st.error(f"Không tải được dữ liệu để đề xuất ma trận: {error}")
        return
    st.caption("Nguồn quy tắc dạng câu/mức độ: câu mẫu ACTIVE đã APPROVED và khóa; đề xuất cần giáo viên rà soát.")
    if missing:
        st.warning(f"{len(missing)} YCCĐ chưa có câu mẫu đã duyệt nên chưa thể suy ra dạng câu/mức độ; cần rà soát bổ sung: {', '.join(missing)}")
    st.dataframe([{
        "Chủ đề": cell.topic_code, "Dạng": cell.question_type_code,
        "Mức độ": cell.cognitive_level_code, "Số câu": cell.question_count,
        "Số ý": cell.response_count, "Điểm": str(cell.target_score),
        "YCCĐ": ", ".join(cell.requirement_codes),
    } for cell in proposed], hide_index=True, use_container_width=True)
    st.caption("Đề xuất ở chế độ xem trước: chưa ghi đè ma trận đã lưu hoặc gửi yêu cầu cho AI.")
