begin;

-- V74.2 seeds the canonical subject-specific competency backbone.  These
-- records describe stable programme-level components; grade-specific YCCD
-- links remain governed and must be reviewed separately.
insert into public.competency_components (
    competency_component_id,
    competency_domain_id,
    component_code,
    component_name,
    description,
    display_order,
    status,
    metadata
)
values
    ('component-math-reasoning','competency-math','NL-MATH-REASONING','Tư duy và lập luận toán học','Thực hiện các thao tác tư duy, lập luận và giải thích toán học.',10,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-MATH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-math-modeling','competency-math','NL-MATH-MODELING','Mô hình hoá toán học','Thiết lập, sử dụng và diễn giải mô hình toán học trong tình huống thực tiễn.',20,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-MATH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-math-problem-solving','competency-math','NL-MATH-PROBLEM-SOLVING','Giải quyết vấn đề toán học','Nhận biết vấn đề, lựa chọn và thực hiện giải pháp toán học.',30,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-MATH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-math-communication','competency-math','NL-MATH-COMMUNICATION','Giao tiếp toán học','Đọc, viết, trình bày và trao đổi thông tin toán học.',40,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-MATH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-math-tools','competency-math','NL-MATH-TOOLS','Sử dụng công cụ, phương tiện học toán','Lựa chọn và sử dụng công cụ, phương tiện phù hợp trong học toán.',50,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-MATH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-english-listening','competency-english','NL-ENG-LISTENING','Nghe','Tiếp nhận và xử lí thông tin tiếng Anh qua kênh nghe.',10,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-ENGLISH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-english-speaking','competency-english','NL-ENG-SPEAKING','Nói','Tạo lập và tương tác bằng ngôn ngữ nói tiếng Anh.',20,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-ENGLISH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-english-reading','competency-english','NL-ENG-READING','Đọc','Tiếp nhận và xử lí thông tin trong văn bản tiếng Anh.',30,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-ENGLISH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-english-writing','competency-english','NL-ENG-WRITING','Viết','Tạo lập văn bản tiếng Anh phù hợp mục đích và ngữ cảnh.',40,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-ENGLISH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9"}'::jsonb),
    ('component-english-language-knowledge','competency-english','NL-ENG-LANGUAGE-KNOWLEDGE','Kiến thức ngôn ngữ','Vận dụng ngữ âm, từ vựng và ngữ pháp để hỗ trợ giao tiếp tiếng Anh.',50,'ACTIVE','{"canonical":true,"source_document_id":"SRC-CUR-ENGLISH-2018","regulation_id":"32/2018/TT-BGDĐT","scope":"grades-6-9","role":"supporting"}'::jsonb)
on conflict (competency_component_id) do update set
    component_code=excluded.component_code,
    component_name=excluded.component_name,
    description=excluded.description,
    display_order=excluded.display_order,
    status=excluded.status,
    metadata=excluded.metadata,
    updated_at=now();

insert into public.competency_indicators (
    competency_indicator_id,
    competency_component_id,
    indicator_code,
    indicator_text,
    observable_behavior,
    evidence_guidance,
    grade_min,
    grade_max,
    proficiency_level,
    evidence_strength,
    display_order,
    status,
    metadata
)
values
    ('indicator-math-reasoning-6-9','component-math-reasoning','NL-MATH-REASONING-6-9','Thực hiện và giải thích được lập luận toán học phù hợp với yêu cầu cần đạt.','Trình bày căn cứ, các bước suy luận và kết luận.','Bài làm có dấu vết suy luận hoặc phần giải thích có thể chấm được.',6,9,'UNSPECIFIED','DIRECT',10,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-math-modeling-6-9','component-math-modeling','NL-MATH-MODELING-6-9','Thiết lập, sử dụng và diễn giải được mô hình toán học phù hợp với tình huống.','Chuyển tình huống sang biểu diễn toán học và đối chiếu kết quả với ngữ cảnh.','Nhiệm vụ có dữ kiện hoặc bối cảnh đủ để quan sát chu trình mô hình hoá.',6,9,'UNSPECIFIED','DIRECT',20,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-math-problem-solving-6-9','component-math-problem-solving','NL-MATH-PROBLEM-SOLVING-6-9','Lựa chọn và thực hiện được giải pháp cho vấn đề toán học phù hợp.','Xác định vấn đề, chọn cách giải và kiểm tra kết quả.','Bài làm thể hiện được quyết định hoặc chiến lược giải.',6,9,'UNSPECIFIED','DIRECT',30,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-math-communication-6-9','component-math-communication','NL-MATH-COMMUNICATION-6-9','Sử dụng được ngôn ngữ và biểu diễn toán học để trình bày, trao đổi kết quả.','Dùng thuật ngữ, kí hiệu, bảng, biểu đồ hoặc hình vẽ phù hợp.','Sản phẩm trình bày có thể đánh giá độ chính xác và rõ ràng.',6,9,'UNSPECIFIED','DIRECT',40,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-math-tools-6-9','component-math-tools','NL-MATH-TOOLS-6-9','Lựa chọn và sử dụng được công cụ, phương tiện học toán phù hợp.','Dùng thước, máy tính, phần mềm hoặc phương tiện được phép để hoàn thành nhiệm vụ.','Chỉ gắn khi đề thực sự cho phép hoặc yêu cầu sử dụng công cụ.',6,9,'UNSPECIFIED','CONTEXTUAL',50,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-english-listening-6-9','component-english-listening','NL-ENG-LISTENING-6-9','Nghe và xử lí được thông tin tiếng Anh theo yêu cầu cần đạt của lớp học.','Xác định thông tin, ý chính hoặc chi tiết từ ngữ liệu nghe.','Cần có tệp hoặc kịch bản nghe và đáp án quan sát được.',6,9,'UNSPECIFIED','DIRECT',10,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-english-speaking-6-9','component-english-speaking','NL-ENG-SPEAKING-6-9','Nói và tương tác được bằng tiếng Anh theo yêu cầu cần đạt của lớp học.','Tạo lập lượt nói hoặc duy trì tương tác phù hợp nhiệm vụ.','Cần rubric nói và bằng chứng ghi nhận phần thể hiện.',6,9,'UNSPECIFIED','DIRECT',20,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-english-reading-6-9','component-english-reading','NL-ENG-READING-6-9','Đọc và xử lí được thông tin trong văn bản tiếng Anh theo yêu cầu cần đạt.','Xác định thông tin, ý chính, chi tiết hoặc suy luận từ văn bản.','Ngữ liệu đọc và câu hỏi phải cho phép đối chiếu đáp án.',6,9,'UNSPECIFIED','DIRECT',30,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-english-writing-6-9','component-english-writing','NL-ENG-WRITING-6-9','Viết được văn bản tiếng Anh theo mục đích, ngữ cảnh và yêu cầu cần đạt.','Tạo lập câu hoặc văn bản có nội dung và hình thức phù hợp.','Cần rubric thể hiện nội dung, tổ chức và sử dụng ngôn ngữ.',6,9,'UNSPECIFIED','DIRECT',40,'ACTIVE','{"canonical":true,"mapping_policy":"review-required"}'::jsonb),
    ('indicator-english-language-knowledge-6-9','component-english-language-knowledge','NL-ENG-LANGUAGE-KNOWLEDGE-6-9','Vận dụng được ngữ âm, từ vựng và ngữ pháp để thực hiện nhiệm vụ giao tiếp.','Dùng kiến thức ngôn ngữ trong nhiệm vụ nghe, nói, đọc hoặc viết.','Không dùng làm đích đánh giá tách rời khi nhiệm vụ chỉ kiểm tra ghi nhớ máy móc.',6,9,'UNSPECIFIED','INDIRECT',50,'ACTIVE','{"canonical":true,"mapping_policy":"review-required","role":"supporting"}'::jsonb)
on conflict (competency_indicator_id) do update set
    indicator_code=excluded.indicator_code,
    indicator_text=excluded.indicator_text,
    observable_behavior=excluded.observable_behavior,
    evidence_guidance=excluded.evidence_guidance,
    grade_min=excluded.grade_min,
    grade_max=excluded.grade_max,
    proficiency_level=excluded.proficiency_level,
    evidence_strength=excluded.evidence_strength,
    display_order=excluded.display_order,
    status=excluded.status,
    metadata=excluded.metadata,
    updated_at=now();

-- Preserve the legacy assessment API while declaring the canonical owner.
insert into public.canonical_entity_links (
    link_id,
    canonical_entity_type,
    canonical_entity_code,
    domain_name,
    domain_entity_type,
    domain_entity_key,
    link_type,
    status,
    metadata
)
values
    ('link-legacy-math-reasoning','COMPETENCY_COMPONENT','NL-MATH-REASONING','assessment','assessment_mathematical_competency','MATH-REASONING','COMPATIBILITY','ACTIVE','{"canonical_owner":"competency_components","migration":"V74.2"}'::jsonb),
    ('link-legacy-math-modeling','COMPETENCY_COMPONENT','NL-MATH-MODELING','assessment','assessment_mathematical_competency','MATH-MODELING','COMPATIBILITY','ACTIVE','{"canonical_owner":"competency_components","migration":"V74.2"}'::jsonb),
    ('link-legacy-math-problem-solving','COMPETENCY_COMPONENT','NL-MATH-PROBLEM-SOLVING','assessment','assessment_mathematical_competency','MATH-PROBLEM-SOLVING','COMPATIBILITY','ACTIVE','{"canonical_owner":"competency_components","migration":"V74.2"}'::jsonb),
    ('link-legacy-math-communication','COMPETENCY_COMPONENT','NL-MATH-COMMUNICATION','assessment','assessment_mathematical_competency','MATH-COMMUNICATION','COMPATIBILITY','ACTIVE','{"canonical_owner":"competency_components","migration":"V74.2"}'::jsonb),
    ('link-legacy-math-tools','COMPETENCY_COMPONENT','NL-MATH-TOOLS','assessment','assessment_mathematical_competency','MATH-TOOLS','COMPATIBILITY','ACTIVE','{"canonical_owner":"competency_components","migration":"V74.2"}'::jsonb)
on conflict (
    canonical_entity_type,
    canonical_entity_code,
    domain_name,
    domain_entity_type,
    domain_entity_key
) do update set
    link_type=excluded.link_type,
    status=excluded.status,
    metadata=excluded.metadata;

commit;
