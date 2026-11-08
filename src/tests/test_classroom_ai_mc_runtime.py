from portal_v2.ui.classroom_ai_mc_runtime import build_gameshow_mc_html


def test_gameshow_mc_overlay_is_added_without_replacing_game_controls():
    source = b"<html><body><button id='judgeCorrect'>Correct</button></body></html>"
    result = build_gameshow_mc_html(source).decode("utf-8")

    assert "mathteacher-gameshow-ai-mc" in result
    assert "mt-mc-listen" in result
    assert "judgeCorrect" in result
    assert "mathteacherGameshow" in result


def test_gameshow_mc_overlay_is_idempotent():
    source = "<html><body>stage</body></html>"
    once = build_gameshow_mc_html(source)
    twice = build_gameshow_mc_html(once)

    assert once == twice


def test_gameshow_mc_overlay_keeps_ai_as_mc_not_score_controller():
    result = build_gameshow_mc_html("<html><body>stage</body></html>").decode("utf-8")

    assert "student_answer" in result
    assert "Không tự kết luận đúng sai" not in result  # policy is enforced server-side
    assert "mt-mc-stop" in result
    assert "judgeCorrect" not in result
