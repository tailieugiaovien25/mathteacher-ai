import base64
from pathlib import Path

from portal_v2.ui.lesson_slide_designer import (
    apply_surface_event,
    build_presentation_html,
    new_draft,
    validate_draft,
)


def _draft_with_slide():
    draft = new_draft()
    draft["slides"] = [{"id": "slide-media-1", "activity": "MO_DAU", "title": "Slide media", "blocks": []}]
    return draft


def test_insert_image_and_video_into_current_slide():
    draft = _draft_with_slide()
    image_data = base64.b64encode(b"test-image").decode("ascii")
    video_data = base64.b64encode(b"test-video").decode("ascii")

    draft = apply_surface_event(draft, {
        "action": "insert_media", "slide_id": "slide-media-1",
        "media_kind": "image", "mime": "image/png", "data_b64": image_data, "updates": [],
    })
    draft = apply_surface_event(draft, {
        "action": "insert_media", "slide_id": "slide-media-1",
        "media_kind": "video", "mime": "video/mp4", "data_b64": video_data, "updates": [],
    })

    validate_draft(draft)
    blocks = draft["slides"][0]["blocks"]
    assert [block["kind"] for block in blocks] == ["Hình ảnh", "Video"]
    assert blocks[0]["image"]["data_b64"] == image_data
    assert blocks[1]["video"]["data_b64"] == video_data
    assert blocks[0]["image"]["width"] == 42
    assert blocks[1]["video"]["height"] == 42


def test_media_can_be_moved_resized_and_deleted():
    draft = _draft_with_slide()
    video_data = base64.b64encode(b"test-video").decode("ascii")
    draft = apply_surface_event(draft, {
        "action": "insert_media", "slide_id": "slide-media-1",
        "media_kind": "video", "mime": "video/mp4", "data_b64": video_data, "updates": [],
    })
    draft = apply_surface_event(draft, {
        "action": "move_media", "slide_id": "slide-media-1", "block_index": 0,
        "x": 21, "y": 27, "updates": [],
    })
    draft = apply_surface_event(draft, {
        "action": "resize_media", "slide_id": "slide-media-1", "block_index": 0,
        "x": 21, "y": 27, "width": 68, "height": 51, "updates": [],
    })
    validate_draft(draft)
    media = draft["slides"][0]["blocks"][0]["video"]
    assert (media["x"], media["y"], media["width"], media["height"]) == (21.0, 27.0, 68, 51)

    draft = apply_surface_event(draft, {
        "action": "delete_component", "component_kind": "block",
        "slide_id": "slide-media-1", "block_index": 0, "updates": [],
    })
    assert draft["slides"][0]["blocks"] == []


def test_media_toolbar_and_resizer_render_in_editor_and_export():
    draft = _draft_with_slide()
    video_data = base64.b64encode(b"test-video").decode("ascii")
    draft = apply_surface_event(draft, {
        "action": "insert_media", "slide_id": "slide-media-1",
        "media_kind": "video", "mime": "video/mp4", "data_b64": video_data, "updates": [],
    })

    editor_html = build_presentation_html(draft, selected_slide_id="slide-media-1", shared_editor=True)
    assert 'id="lesson-insert-media"' in editor_html
    assert "data-media-object" in editor_html
    assert "media-object-resize" in editor_html
    assert 'src="about:blank"' in editor_html
    assert 'src="data:video/mp4;base64,' not in editor_html

    exported_html = build_presentation_html(draft, selected_slide_id="slide-media-1", shared_editor=False)
    assert 'src="data:video/mp4;base64,' in exported_html


def test_media_resize_uses_stable_pointer_delta_and_visible_handle():
    source_path = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "lesson_slide_designer.py"
    source = source_path.read_text(encoding="utf-8")

    # The handle must remain interactive even while slide text editing is active.
    assert "if(!handle||document.fullscreenElement)return;" in source
    # Resize should be computed from the starting dimensions plus pointer delta,
    # not from a changing bounding box (which made the size jump/stick).
    assert "d.startWidth+deltaX/d.sr.width*100" in source
    assert "d.startHeight+deltaY/d.canvasHeight*100" in source
    assert "event.clientX-br.left+d.w*d.sr.width/100" not in source
    assert ".lesson-media-object .media-object-resize{z-index:60}" in source
