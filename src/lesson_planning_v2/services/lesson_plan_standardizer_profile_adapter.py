from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

_LEGACY_SECTION_KEYS = {
    "page": {"paper_size", "orientation", "margin_left_cm", "margin_right_cm", "margin_top_cm", "margin_bottom_cm", "border_enabled", "border_style", "border_width_pt", "border_color_rgb"},
    "body": {"font", "size_pt", "line_spacing", "color_rgb", "character_spacing_pt"},
    "title": {"size_pt"},
    "table": {"size_pt", "repeat_header", "allow_row_split", "border_style", "border_width_pt", "border_color_rgb"},
    "header_footer": {"remove_existing", "page_number", "page_number_alignment"},
    "equations": {"mode", "text_font", "math_font", "preserve_omml_structure", "preserve_value", "rollback_on_integrity_failure"},
}

def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None

def _nonnegative_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None

def _nonblank_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None

def _apply_legacy_shaped_overrides(*, profile: dict[str, Any], admin_template_profile: Mapping[str, Any]) -> None:
    for section_name, allowed_keys in _LEGACY_SECTION_KEYS.items():
        section = admin_template_profile.get(section_name)
        if not isinstance(section, Mapping):
            continue
        target = profile.get(section_name)
        if not isinstance(target, dict):
            target = {}
            profile[section_name] = target
        for key in allowed_keys:
            if key not in section:
                continue
            value = section[key]
            if key.startswith("margin_"):
                parsed = _nonnegative_number(value)
                if parsed is not None:
                    target[key] = parsed
            elif key in {"size_pt", "line_spacing", "border_width_pt"}:
                parsed = _positive_number(value)
                if parsed is not None:
                    target[key] = parsed
            elif key in {"font", "text_font", "math_font", "mode", "page_number_alignment", "paper_size", "orientation", "border_style", "border_color_rgb", "color_rgb"}:
                parsed = _nonblank_text(value)
                if parsed is not None:
                    target[key] = parsed
            elif key in {"repeat_header", "allow_row_split", "remove_existing", "page_number", "preserve_omml_structure", "preserve_value", "rollback_on_integrity_failure", "border_enabled"}:
                if isinstance(value, bool):
                    target[key] = value

def _apply_rich_layout_overrides(*, profile: dict[str, Any], admin_template_profile: Mapping[str, Any]) -> None:
    layout = admin_template_profile.get("layout")
    if not isinstance(layout, Mapping):
        return
    page = profile.setdefault("page", {})
    body = profile.setdefault("body", {})
    table = profile.setdefault("table", {})
    equations = profile.setdefault("equations", {})
    for source_key in ("margin_left_cm", "margin_right_cm", "margin_top_cm", "margin_bottom_cm"):
        if source_key in layout:
            parsed = _nonnegative_number(layout[source_key])
            if parsed is not None:
                page[source_key] = parsed
    font_name = _nonblank_text(layout.get("font_name"))
    if font_name is not None:
        body["font"] = font_name
    body_size = _positive_number(layout.get("body_font_size_pt"))
    if body_size is not None:
        body["size_pt"] = body_size
    line_spacing = _positive_number(layout.get("line_spacing"))
    if line_spacing is not None:
        body["line_spacing"] = line_spacing
    paper_size = _nonblank_text(layout.get("paper_size"))
    if paper_size in {"A3", "A4", "A5"}:
        page["paper_size"] = paper_size
    color_map = {"black": "000000", "blue": "0000FF", "red": "FF0000"}
    color_name = _nonblank_text(layout.get("font_color"))
    if color_name in color_map:
        body["color_rgb"] = color_map[color_name]
    try:
        character_spacing = float(layout.get("character_spacing_pt", 0.0))
    except (TypeError, ValueError):
        character_spacing = 0.0
    body["character_spacing_pt"] = max(-1.0, min(5.0, character_spacing))
    for source_key, target_key in (
        ("page_border_enabled", "border_enabled"),
        ("page_border_style", "border_style"),
        ("page_border_width_pt", "border_width_pt"),
    ):
        if source_key in layout:
            page[target_key] = layout[source_key]
    for source_key, target_key in (
        ("table_border_style", "border_style"),
        ("table_border_width_pt", "border_width_pt"),
        ("table_repeat_header", "repeat_header"),
        ("table_allow_row_split", "allow_row_split"),
    ):
        if source_key in layout:
            table[target_key] = layout[source_key]
    # Formula policy is mandatory and cannot be weakened by an ACTIVE profile.
    equations.update({
        "mode": "force_times", "text_font": "Times New Roman",
        "math_font": "Times New Roman", "preserve_omml_structure": True,
        "preserve_value": True, "rollback_on_integrity_failure": True,
    })

def build_runtime_standardizer_profile(*, legacy_profile_path: Path, admin_template_profile: Mapping[str, Any] | None) -> dict[str, Any]:
    legacy = json.loads(Path(legacy_profile_path).read_text(encoding="utf-8"))
    if not isinstance(legacy, dict):
        raise ValueError("legacy lesson-plan profile must be a JSON object")
    profile = deepcopy(legacy)
    if not isinstance(admin_template_profile, Mapping):
        return profile
    profile_name = _nonblank_text(admin_template_profile.get("profile_name"))
    if profile_name is not None:
        profile["profile_name"] = profile_name
    _apply_legacy_shaped_overrides(profile=profile, admin_template_profile=admin_template_profile)
    _apply_rich_layout_overrides(profile=profile, admin_template_profile=admin_template_profile)
    snapshot = admin_template_profile.get("_admin_configuration_snapshot")
    if isinstance(snapshot, Mapping):
        profile["_admin_configuration_snapshot"] = dict(snapshot)
    profile.setdefault("equations", {}).update({
        "mode": "force_times", "text_font": "Times New Roman",
        "math_font": "Times New Roman", "preserve_omml_structure": True,
        "preserve_value": True, "rollback_on_integrity_failure": True,
    })
    return profile
