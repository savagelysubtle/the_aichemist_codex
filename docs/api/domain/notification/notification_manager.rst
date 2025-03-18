Notification Manager
==================

The Notification Manager is responsible for creating, managing, and delivering notifications through various channels.

Overview
--------

The Notification Manager:

* Creates and sends notifications
* Manages notification channels
* Handles notification delivery
* Tracks notification status and history

Implementation
-------------

.. automodule:: the_aichemist_codex.backend.domain.notification.notification_manager
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* **Multi-Channel Support**: Sends notifications through multiple channels
* **Priority Management**: Handles notification priority and delivery order
* **Template Support**: Uses templates for consistent notification formatting
* **Delivery Tracking**: Tracks notification status and delivery statistics
* **Subscription Management**: Manages user subscriptions to notification types

Usage Example
------------

.. code-block:: python

   from the_aichemist_codex.backend.domain.notification import NotificationManager
   from the_aichemist_codex.backend.domain.notification.models import NotificationType, NotificationPriority

   # Initialize the notification manager
   notification_manager = NotificationManager()

   # Send a simple notification
   await notification_manager.notify(
       title="File Processing Complete",
       message="Your file has been processed successfully",
       notification_type=NotificationType.SYSTEM,
       priority=NotificationPriority.NORMAL,
       user_id="user123"
   )

   # Send a notification with custom data
   await notification_manager.notify(
       title="Search Results Ready",
       message="Your search query returned 15 results",
       notification_type=NotificationType.INFO,
       priority=NotificationPriority.LOW,
       user_id="user123",
       data={
           "query": "machine learning",
           "results_count": 15,
           "execution_time": 0.35
       }
   )