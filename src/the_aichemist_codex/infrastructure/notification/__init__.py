"""Notification system for The Aichemist Codex."""

from the_aichemist_codex.infrastructure.notification.notification_manager import (
    Notification,
    NotificationLevel,
    NotificationManager,
    NotificationType,
    notification_manager,
)

# Import rule engine components if available
try:
    from the_aichemist_codex.infrastructure.notification.rule_engine import (
        ActionType,
        ConditionOperator,
        NotificationRule,
        RuleAction,
        RuleCondition,
        TimeCondition,
        TimeConditionType,
        rule_engine,
    )

    __all__ = [
        "Notification",
        "NotificationLevel",
        "NotificationType",
        "NotificationManager",
        "notification_manager",
        "NotificationRule",
        "RuleCondition",
        "RuleAction",
        "TimeCondition",
        "ConditionOperator",
        "TimeConditionType",
        "ActionType",
        "rule_engine",
    ]
except ImportError:
    # Rule engine not available
    __all__ = [
        "Notification",
        "NotificationLevel",
        "NotificationType",
        "NotificationManager",
        "notification_manager",
    ]
