from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocument,
)


class DynamicAssessmentRendererError(ValueError):
    """Raised when an assessment template cannot be rendered."""


DOCUMENT_ROOTS = MappingProxyType(
    {
        "MATRIX": "matrix",
        "SPECIFICATION": "specification",
        "STUDENT_EXAM": "questions",
        "ANSWER_KEY": "answer_key",
        "SCORING_GUIDE": "scoring_guide",
    }
)

SUPPORTED_RENDERER_CODES = frozenset(
    {
        "DOCX_JSON_V1",
    }
)

SUPPORTED_SECTION_TYPES = frozenset(
    {
        "FIELDS",
        "TABLE",
        "REPEAT",
        "TEXT",
        "PAGE_BREAK",
    }
)


def _required_text(
    value: object,
    field_name: str,
    *,
    maximum_length: int = 200,
) -> str:
    if not isinstance(value, str):
        raise DynamicAssessmentRendererError(
            f"{field_name} must be text"
        )

    normalized = value.strip()

    if not normalized:
        raise DynamicAssessmentRendererError(
            f"{field_name} is required"
        )

    if len(normalized) > maximum_length:
        raise DynamicAssessmentRendererError(
            f"{field_name} is too long"
        )

    return normalized


def _mapping(
    value: object,
    field_name: str,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise DynamicAssessmentRendererError(
            f"{field_name} must be an object"
        )

    return {
        str(key): item
        for key, item in value.items()
    }


def _sequence(
    value: object,
    field_name: str,
) -> tuple[object, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise DynamicAssessmentRendererError(
            f"{field_name} must be an array"
        )

    return tuple(value)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                str(key): _freeze(item)
                for key, item in value.items()
            }
        )

    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
    ):
        return tuple(
            _freeze(item)
            for item in value
        )

    return value


def _canonical_root(
    document: CanonicalAssessmentDocument,
) -> dict[str, object]:
    return {
        "metadata": document.metadata,
        "matrix": document.matrix,
        "specification": document.specification,
        "questions": document.questions,
        "answer_key": document.answer_key,
        "scoring_guide": document.scoring_guide,
    }


def _resolve_path(
    root: object,
    path: str,
    *,
    field_name: str,
) -> object:
    normalized_path = _required_text(
        path,
        field_name,
        maximum_length=500,
    )

    segments = normalized_path.split(".")

    if any(not segment for segment in segments):
        raise DynamicAssessmentRendererError(
            f"{field_name} contains an empty path segment"
        )

    current = root

    for segment in segments:
        if isinstance(current, Mapping):
            if segment not in current:
                raise DynamicAssessmentRendererError(
                    f"{field_name} does not resolve: "
                    f"{normalized_path}"
                )

            current = current[segment]
            continue

        if (
            isinstance(current, Sequence)
            and not isinstance(
                current,
                (str, bytes, bytearray),
            )
        ):
            if not segment.isdigit():
                raise DynamicAssessmentRendererError(
                    f"{field_name} requires an array index: "
                    f"{normalized_path}"
                )

            index = int(segment)

            if index >= len(current):
                raise DynamicAssessmentRendererError(
                    f"{field_name} index is out of range: "
                    f"{normalized_path}"
                )

            current = current[index]
            continue

        raise DynamicAssessmentRendererError(
            f"{field_name} traverses a scalar value: "
            f"{normalized_path}"
        )

    return current


@dataclass(frozen=True, slots=True)
class AssessmentTemplateDefinition:
    document_type_code: str
    renderer_code: str
    layout_schema: Mapping[str, object]
    style_schema: Mapping[str, object]
    binding_schema: Mapping[str, object]
    section_schema: tuple[Mapping[str, object], ...]
    template_asset_path: str | None = None
    template_asset_hash: str | None = None

    def __post_init__(self) -> None:
        document_type_code = _required_text(
            self.document_type_code,
            "document_type_code",
            maximum_length=50,
        ).upper()

        if document_type_code not in DOCUMENT_ROOTS:
            raise DynamicAssessmentRendererError(
                "unsupported document type"
            )

        renderer_code = _required_text(
            self.renderer_code,
            "renderer_code",
            maximum_length=100,
        ).upper()

        if renderer_code not in SUPPORTED_RENDERER_CODES:
            raise DynamicAssessmentRendererError(
                "unsupported renderer code"
            )

        layout_schema = _mapping(
            self.layout_schema,
            "layout_schema",
        )
        style_schema = _mapping(
            self.style_schema,
            "style_schema",
        )
        binding_schema = _mapping(
            self.binding_schema,
            "binding_schema",
        )

        section_items = _sequence(
            self.section_schema,
            "section_schema",
        )

        sections = tuple(
            _mapping(
                item,
                f"section_schema[{index}]",
            )
            for index, item in enumerate(section_items)
        )

        if not sections:
            raise DynamicAssessmentRendererError(
                "section_schema must not be empty"
            )

        normalized_bindings: dict[str, str] = {}

        for raw_binding_name, binding_path in (
            binding_schema.items()
        ):
            binding_name = _required_text(
                raw_binding_name,
                "binding name",
                maximum_length=100,
            )

            if binding_name in normalized_bindings:
                raise DynamicAssessmentRendererError(
                    "binding names must be unique"
                )

            normalized_bindings[binding_name] = (
                _required_text(
                    binding_path,
                    f"binding_schema.{binding_name}",
                    maximum_length=500,
                )
            )

        section_codes: set[str] = set()

        for index, section in enumerate(sections):
            section_code = _required_text(
                section.get("section_code"),
                f"section_schema[{index}].section_code",
                maximum_length=100,
            )

            if section_code in section_codes:
                raise DynamicAssessmentRendererError(
                    "section codes must be unique"
                )

            section_codes.add(section_code)

            section_type = _required_text(
                section.get("section_type"),
                f"section_schema[{index}].section_type",
                maximum_length=30,
            ).upper()

            if section_type not in SUPPORTED_SECTION_TYPES:
                raise DynamicAssessmentRendererError(
                    "unsupported section type"
                )

        asset_path = self.template_asset_path
        asset_hash = self.template_asset_hash

        if asset_path is not None:
            asset_path = _required_text(
                asset_path,
                "template_asset_path",
                maximum_length=500,
            )

        if asset_hash is not None:
            asset_hash = _required_text(
                asset_hash,
                "template_asset_hash",
                maximum_length=64,
            ).lower()

            if (
                len(asset_hash) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in asset_hash
                )
            ):
                raise DynamicAssessmentRendererError(
                    "template_asset_hash must be SHA-256"
                )

        if (asset_path is None) != (asset_hash is None):
            raise DynamicAssessmentRendererError(
                "template asset path and hash must be paired"
            )

        object.__setattr__(
            self,
            "document_type_code",
            document_type_code,
        )
        object.__setattr__(
            self,
            "renderer_code",
            renderer_code,
        )
        object.__setattr__(
            self,
            "layout_schema",
            _freeze(layout_schema),
        )
        object.__setattr__(
            self,
            "style_schema",
            _freeze(style_schema),
        )
        object.__setattr__(
            self,
            "binding_schema",
            _freeze(normalized_bindings),
        )
        object.__setattr__(
            self,
            "section_schema",
            _freeze(sections),
        )
        object.__setattr__(
            self,
            "template_asset_path",
            asset_path,
        )
        object.__setattr__(
            self,
            "template_asset_hash",
            asset_hash,
        )


@dataclass(frozen=True, slots=True)
class AssessmentDocumentRenderPlan:
    schema_version: int
    document_type_code: str
    renderer_code: str
    layout: Mapping[str, object]
    styles: Mapping[str, object]
    bindings: Mapping[str, object]
    sections: tuple[Mapping[str, object], ...]
    template_asset_path: str | None
    template_asset_hash: str | None

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise DynamicAssessmentRendererError(
                "unsupported render plan schema"
            )

        object.__setattr__(
            self,
            "layout",
            _freeze(dict(self.layout)),
        )
        object.__setattr__(
            self,
            "styles",
            _freeze(dict(self.styles)),
        )
        object.__setattr__(
            self,
            "bindings",
            _freeze(dict(self.bindings)),
        )
        object.__setattr__(
            self,
            "sections",
            _freeze(tuple(self.sections)),
        )


class DynamicAssessmentDocumentRenderer:
    """Resolve an approved template against canonical assessment data."""

    RENDER_PLAN_SCHEMA_VERSION = 1

    def render(
        self,
        *,
        document: CanonicalAssessmentDocument,
        template: AssessmentTemplateDefinition,
    ) -> AssessmentDocumentRenderPlan:
        if not isinstance(
            document,
            CanonicalAssessmentDocument,
        ):
            raise DynamicAssessmentRendererError(
                "canonical assessment document is required"
            )

        if not isinstance(
            template,
            AssessmentTemplateDefinition,
        ):
            raise DynamicAssessmentRendererError(
                "assessment template definition is required"
            )

        canonical = _canonical_root(document)

        expected_root = DOCUMENT_ROOTS[
            template.document_type_code
        ]

        resolved_bindings: dict[str, object] = {}

        for binding_name, path_value in (
            template.binding_schema.items()
        ):
            path = _required_text(
                path_value,
                f"binding_schema.{binding_name}",
                maximum_length=500,
            )

            top_level_root = path.split(".", maxsplit=1)[0]

            allowed_roots = {
                "metadata",
                expected_root,
            }

            if top_level_root not in allowed_roots:
                raise DynamicAssessmentRendererError(
                    "binding is outside the permitted "
                    "document data scope"
                )

            resolved_bindings[binding_name] = _resolve_path(
                canonical,
                path,
                field_name=(
                    f"binding_schema.{binding_name}"
                ),
            )

        rendered_sections = tuple(
            self._render_section(
                section=section,
                resolved_bindings=resolved_bindings,
                section_index=index,
            )
            for index, section in enumerate(
                template.section_schema
            )
        )

        return AssessmentDocumentRenderPlan(
            schema_version=self.RENDER_PLAN_SCHEMA_VERSION,
            document_type_code=(
                template.document_type_code
            ),
            renderer_code=template.renderer_code,
            layout=template.layout_schema,
            styles=template.style_schema,
            bindings=resolved_bindings,
            sections=rendered_sections,
            template_asset_path=template.template_asset_path,
            template_asset_hash=template.template_asset_hash,
        )

    def _render_section(
        self,
        *,
        section: Mapping[str, object],
        resolved_bindings: Mapping[str, object],
        section_index: int,
    ) -> Mapping[str, object]:
        section_code = _required_text(
            section.get("section_code"),
            f"section_schema[{section_index}].section_code",
            maximum_length=100,
        )

        section_type = _required_text(
            section.get("section_type"),
            f"section_schema[{section_index}].section_type",
            maximum_length=30,
        ).upper()

        if section_type not in SUPPORTED_SECTION_TYPES:
            raise DynamicAssessmentRendererError(
                "unsupported section type"
            )

        binding_names = _sequence(
            section.get("bindings", ()),
            (
                f"section_schema[{section_index}]"
                ".bindings"
            ),
        )

        section_bindings: dict[str, object] = {}

        for binding_position, binding_value in enumerate(
            binding_names
        ):
            binding_name = _required_text(
                binding_value,
                (
                    f"section_schema[{section_index}]"
                    f".bindings[{binding_position}]"
                ),
                maximum_length=100,
            )

            if binding_name not in resolved_bindings:
                raise DynamicAssessmentRendererError(
                    "section references an unknown binding"
                )

            section_bindings[binding_name] = (
                resolved_bindings[binding_name]
            )

        rendered = {
            str(key): value
            for key, value in section.items()
            if key != "bindings"
        }
        rendered["section_code"] = section_code
        rendered["section_type"] = section_type
        rendered["data"] = section_bindings

        return _freeze(rendered)
