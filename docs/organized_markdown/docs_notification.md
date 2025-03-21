# Notification System

## Overview

The Notification System provides a flexible, reliable framework for creating,
sending, and managing notifications across multiple delivery channels. It
implements a publisher-subscriber pattern allowing for extensible notification
mechanisms while maintaining a consistent interface. This system is designed to
handle everything from informational messages to critical alerts, with support
for throttling, persistence, and delivery confirmation.

## Core Components

### NotificationManager

The `NotificationManager` class is the central component that coordinates the
entire notification workflow. It follows the Singleton pattern to ensure a
single, globally accessible instance.

Key responsibilities:

- Managing notification subscribers (channels)
- Throttling notifications to prevent flooding
- Storing notifications in the database
- Routing notifications to appropriate subscribers based on their type and level
- Applying rules-based filtering and transformations

```python
# Usage example
from backend.src.notification.notification_manager import NotificationManager

# Get the singleton instance
notification_manager = NotificationManager()

# Send a notification
notification_manager.send_notification(
    message="File upload completed successfully",
    level="INFO",
    notification_type="FILE_OPERATION",
    metadata={"file_path": "/path/to/file.txt", "size": 1024}
)
```

### NotificationSubscriber

`NotificationSubscriber` is an abstract base class that defines the interface
for all notification delivery channels. Each subscriber implements a specific
delivery mechanism.

Built-in subscribers:

- `LogSubscriber`: Writes notifications to the application logs
- `DatabaseSubscriber`: Stores notifications in the database for persistence
- `EmailSubscriber`: Sends email notifications (optional)
- `WebhookSubscriber`: Delivers notifications to external systems via webhooks
  (optional)

```python
# Custom subscriber example
from backend.src.notification.notification_manager import NotificationSubscriber

class CustomSubscriber(NotificationSubscriber):
    def __init__(self, config):
        self.config = config

    def _process_notification(self, notification):
        # Custom implementation for handling notifications
        print(f"Custom notification: {notification.message}")
```

### SimpleCache

The `SimpleCache` class provides an efficient caching mechanism used primarily
for throttling notifications. It implements a generic type system to ensure type
safety while maintaining flexibility.

Features:

- Time-to-live (TTL) functionality for cache entries
- Size limiting with LRU eviction policy
- Thread-safe operations

## Key Features

### Multi-Channel Delivery

The notification system can simultaneously deliver notifications through
multiple channels based on notification type and level. This ensures that
critical notifications reach users through multiple means, while routine
information is delivered through appropriate channels only.

### Notification Throttling

To prevent notification flooding, the system implements intelligent throttling
based on notification type, source, and frequency. Similar notifications
occurring in rapid succession are consolidated to reduce noise.

```python
# Throttling configuration
notification_manager.set_throttle_window(60)  # 60 second window
notification_manager.set_throttle_count(3)    # Max 3 similar notifications per window
```

### Defensive Dependency Handling

The system employs defensive programming techniques to handle optional
dependencies gracefully. Email and webhook subscribers are only activated if
their dependencies are available, making these features truly optional.

```python
# The system checks for email module availability at runtime
try:
    import importlib.util
    spec = importlib.util.find_spec("email.mime.text")
    if spec is not None:
        # Email module is available
        email_module = importlib.import_module("email.mime.text")
    else:
        # Email module is not available
        logger.warning("Email module not available")
except Exception as e:
    logger.warning(f"Failed to import email module: {e}")
```

### Persistence and History

All notifications are stored in the database by default, creating a searchable
history of system events. The CLI interface provides tools to query, filter, and
export this notification history.

## Notification Rules Engine

The notification system includes a powerful rules engine that allows for
sophisticated filtering, routing, and transformation of notifications based on
customizable conditions.

### Rule Components

Each rule consists of four main components:

- **Conditions**: Criteria that determine when the rule matches a notification
- **Time Conditions**: Time-based constraints that can limit when rules are
  active
- **Actions**: Changes to make to matching notifications (transform, route,
  block, etc.)
- **Metadata**: Name, description, priority, etc.

### Rule Conditions

Conditions are evaluations performed against notification properties. Each
condition has:

- **Field**: The notification property to check (level, type, message, source,
  etc.)
- **Operator**: How to compare the field value (equals, contains, matches regex,
  etc.)
- **Value**: What to compare against
- **Negate**: Whether to invert the result

```python
# Example condition that matches ERROR notifications
condition = RuleCondition(
    field="level",
    operator=ConditionOperator.EQUALS,
    value="ERROR"
)

# Example condition that matches messages NOT containing "success"
condition = RuleCondition(
    field="message",
    operator=ConditionOperator.CONTAINS,
    value="success",
    negate=True
)
```

### Time Conditions

Time conditions restrict when rules are active:

- **Time of Day**: Only active during specific hours
- **Day of Week**: Only active on certain days
- **Date Range**: Only active between specific dates
- **Frequency**: Limits how often a notification type can occur

```python
# Example time condition that only matches during work hours
time_condition = TimeCondition(
    condition_type=TimeConditionType.TIME_OF_DAY,
    value={"start": "09:00", "end": "17:00"}
)

# Example time condition that only matches on weekends
time_condition = TimeCondition(
    condition_type=TimeConditionType.DAY_OF_WEEK,
    value=[5, 6]  # Saturday and Sunday
)
```

### Rule Actions

Actions determine what happens when a rule matches:

- **TRANSFORM**: Modify the notification (change level, message, etc.)
- **ROUTE**: Send to specific subscribers only
- **BLOCK**: Prevent the notification from being sent
- **THROTTLE**: Apply custom throttling parameters
- **ENRICH**: Add additional data to the notification

```python
# Example action that routes critical notifications to email
action = RuleAction(
    action_type=ActionType.ROUTE,
    parameters={"subscribers": ["email"]}
)

# Example action that blocks test notifications
action = RuleAction(
    action_type=ActionType.BLOCK,
    parameters={}
)

# Example action that enriches notifications with context
action = RuleAction(
    action_type=ActionType.ENRICH,
    parameters={
        "add_fields": {"environment": "production"},
        "add_context": ["request_id", "user_id"]
    }
)
```

### Creating and Managing Rules

Rules can be created programmatically or through the CLI:

```python
# Programmatic rule creation example
from backend.src.notification import (
    NotificationRule, RuleCondition, TimeCondition, RuleAction,
    ConditionOperator, TimeConditionType, ActionType, rule_engine
)

# Create a rule to route security notifications to email and webhook
rule = NotificationRule(
    name="Security Alert Routing",
    description="Routes security alerts to email and webhook subscribers",
    conditions=[
        RuleCondition(
            field="type",
            operator=ConditionOperator.EQUALS,
            value="security"
        ),
        RuleCondition(
            field="level",
            operator=ConditionOperator.EQUALS,
            value="ERROR"
        )
    ],
    actions=[
        RuleAction(
            action_type=ActionType.ROUTE,
            parameters={"subscribers": ["email", "webhook"]}
        ),
        RuleAction(
            action_type=ActionType.TRANSFORM,
            parameters={
                "message": "[SECURITY ALERT] {message}"
            }
        )
    ],
    priority=10  # Lower number = higher priority
)

# Add the rule to the rule engine
rule_id = await rule_engine.add_rule(rule)
```

### CLI Rule Management

The notification system provides comprehensive CLI commands for rule management:

```bash
# List all rules
python -m backend.cli notify rule list

# Show details of a specific rule
python -m backend.cli notify rule show <rule_id>

# Add a new rule from a JSON file
python -m backend.cli notify rule add --file rule_definition.json

# Update an existing rule
python -m backend.cli notify rule update <rule_id> --file updated_rule.json

# Delete a rule
python -m backend.cli notify rule delete <rule_id>

# Enable or disable a rule
python -m backend.cli notify rule toggle <rule_id> --enable true

# Test a rule against a notification
python -m backend.cli notify rule test <rule_id> --message "Test notification" --level ERROR
```

### Rule Processing Flow

When a notification is sent through the `NotificationManager`, it is processed
by the rules engine in the following sequence:

1. Each rule is evaluated in priority order (lower priority number = higher
   precedence)
2. If a rule matches, its actions are applied to the notification
3. If a rule with a BLOCK action matches, the notification is discarded
4. If rules specify routing, only the specified subscribers receive the
   notification
5. Custom throttling parameters can be applied by matching rules

This allows for sophisticated notification workflows such as:

- Routing critical errors to immediate channels (email, SMS)
- Enriching notifications with additional context
- Blocking or throttling noisy notifications during specific time periods
- Transforming notification content based on destination

## Command-Line Interface

The notification system provides a comprehensive CLI for managing notifications:

```bash
# List all notifications
python -m backend.cli notify list

# List notifications in JSON format
python -m backend.cli notify list --format json

# Show details of a specific notification
python -m backend.cli notify show <notification_id>

# Send a new notification
python -m backend.cli notify send --message "Test notification" --level INFO --type SYSTEM

# Clean up old notifications
python -m backend.cli notify cleanup --days 30
```

## Configuration

The notification system is configured through the application's main
configuration system. Key settings include:

```yaml
notification:
  # General settings
  enabled: true
  default_level: INFO

  # Email settings
  email:
    enabled: true
    smtp_server: smtp.example.com
    smtp_port: 587
    username: notifications@example.com
    password: ${ENV_SMTP_PASSWORD}
    from_address: notifications@example.com

  # Webhook settings
  webhook:
    enabled: true
    endpoints:
      - url: https://example.com/webhook
        secret: ${ENV_WEBHOOK_SECRET}
        content_type: application/json

  # Throttling settings
  throttling:
    enabled: true
    window_seconds: 60
    max_count: 3
```

## Notification Levels and Types

### Levels

- `DEBUG`: Detailed information useful for debugging
- `INFO`: General information about system operation
- `WARNING`: Indicates potential issues that don't prevent system operation
- `ERROR`: Indicates errors that prevent specific functions from working
- `CRITICAL`: Indicates critical errors that may prevent the system from
  functioning

### Types

- `SYSTEM`: System-level events (startup, shutdown, etc.)
- `FILE_OPERATION`: Events related to file operations (creation, modification,
  deletion)
- `SECURITY`: Security-related events (authentication, authorization)
- `USER_ACTION`: User-initiated actions
- `BACKGROUND_TASK`: Events from background tasks and scheduled jobs

## Best Practices

### When to Use Notifications

- **DO** use notifications for important system events that users should be
  aware of
- **DO** include relevant metadata with notifications to provide context
- **DO** set appropriate notification levels based on severity
- **DON'T** create notifications for routine operations that don't require user
  attention
- **DON'T** include sensitive information in notification messages

### Creating Custom Subscribers

1. Inherit from the `NotificationSubscriber` base class
2. Implement the `_process_notification` method
3. Add initialization logic to handle configuration
4. Register the subscriber with the `NotificationManager`

```python
# Register a custom subscriber
notification_manager.add_subscriber(CustomSubscriber(config))
```

### Creating Effective Rules

1. **Be specific**: Make rule conditions as precise as possible to avoid
   unintended matches
2. **Use priorities**: Assign appropriate priorities to ensure rules are
   evaluated in the correct order
3. **Limit scope**: Use time conditions to limit when rules are active
4. **Test rules**: Use the `test` command to verify rule behavior
5. **Monitor performance**: Rules with complex conditions or many actions can
   impact performance

## Implementation Details

### Notification Delivery Flow

1. `send_notification()` is called on the `NotificationManager`
2. Notification is validated and converted to a `Notification` object
3. Notification is processed through the rules engine (if available)
4. Throttling logic determines if the notification should be processed
5. Notification is stored in the database via the `DatabaseSubscriber`
6. Notification is dispatched to all relevant subscribers
7. Each subscriber processes the notification in its own way
8. Results from each subscriber are collected and returned

### Error Handling

The notification system is designed to be resilient to failures in any
individual subscriber. If a subscriber fails to process a notification, the
error is logged, but other subscribers continue to receive the notification.

```python
try:
    result = subscriber.process_notification(notification)
    results[subscriber.name] = result
except Exception as e:
    logger.error(f"Failed to process notification with subscriber {subscriber.name}: {e}")
    results[subscriber.name] = False
```

## Code Organization

- `notification_manager.py`: Contains the main `NotificationManager` class and
  base `NotificationSubscriber` class
- `email_subscriber.py`: Implementation of the `EmailSubscriber` class
- `webhook_subscriber.py`: Implementation of the `WebhookSubscriber` class
- `rule_engine.py`: Implementation of the rules system
- `__init__.py`: Exports key classes and functions for easy importing

## Future Enhancements

- **Mobile push notifications**: Add support for sending push notifications to
  mobile devices
- **User preferences**: Allow users to customize which notifications they
  receive
- **Read status tracking**: Track which notifications have been read by users
- **Notification templates**: Support for customizable notification templates
- **Rich notifications**: Support for rich content in notifications (HTML,
  images, etc.)
- **Advanced rule conditions**: Support for more complex rule conditions
- **Rule groups**: Support for organizing rules into logical groups
