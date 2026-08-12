from .rule import (
    Rule,
    RuleStatus,
)


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def register(
        self,
        rule: Rule,
    ) -> None:
        rule_id = rule.rule_id.strip()

        if not rule_id:
            raise ValueError(
                "rule_id không được để trống."
            )

        if rule_id in self._rules:
            raise ValueError(
                f"Rule đã tồn tại: {rule_id}"
            )

        self._rules[rule_id] = rule

    def get(
        self,
        rule_id: str,
    ) -> Rule:
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Rule: {rule_id}"
            ) from exc

    def all(
        self,
    ) -> tuple[Rule, ...]:
        return tuple(
            self._rules.values()
        )

    def active(
        self,
    ) -> tuple[Rule, ...]:
        return tuple(
            rule
            for rule in self._rules.values()
            if rule.status == RuleStatus.ACTIVE
        )

    def find(
        self,
        *,
        data_type_id: str,
        context: str,
        rule_type: str | None = None,
    ) -> tuple[Rule, ...]:

        matches = []

        for rule in self._rules.values():

            if rule.status != RuleStatus.ACTIVE:
                continue

            if (
                rule.applies_to_data_type
                != data_type_id
            ):
                continue

            if rule.context != context:
                continue

            if (
                rule_type is not None
                and rule.rule_type != rule_type
            ):
                continue

            matches.append(rule)

        matches.sort(
            key=lambda item: item.priority
        )

        return tuple(matches)