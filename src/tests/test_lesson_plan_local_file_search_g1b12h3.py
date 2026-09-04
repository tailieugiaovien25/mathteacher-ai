from lesson_planning_v2.services.lesson_plan_local_file_search import find_local_lesson_plans,read_local_lesson_plan

def test_normalized_week(tmp_path):
    f=tmp_path/"KHBD.ANH6.TUAN1.docx"; f.write_bytes(b"docx")
    r=find_local_lesson_plans(preferred_file_name="KHBD.ANH6.TUAN01.docx",roots=(tmp_path,))
    assert len(r)==1 and r[0].path==f
    assert read_local_lesson_plan(r[0])==b"docx"

def test_unrelated_not_selected(tmp_path):
    (tmp_path/"Unit9_NLS_HSKT.docx").write_bytes(b"x")
    assert find_local_lesson_plans(preferred_file_name="KHBD.ANH6.TUAN01.docx",roots=(tmp_path,))==()

def test_multiple_remain_ambiguous(tmp_path):
    a=tmp_path/"a"; b=tmp_path/"b"; a.mkdir(); b.mkdir()
    (a/"KHBD.ANH6.TUAN01.docx").write_bytes(b"1")
    (b/"KHBD.ANH6.TUAN1.docx").write_bytes(b"2")
    assert len(find_local_lesson_plans(preferred_file_name="KHBD.ANH6.TUAN01.docx",roots=(tmp_path,)))==2
