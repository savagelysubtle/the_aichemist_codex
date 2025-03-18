Notification (Legacy)
==================

.. note::
   This is a legacy documentation page. Please refer to the updated :doc:`domain/notification`
   documentation for the current implementation.

The Notification module provides functionality for creating, sending, and managing notifications to users.

Current Implementation
--------------------

The notification system has been migrated to the new domain-driven architecture. Please see:

* :doc:`domain/notification` - Current notification module documentation
* :doc:`domain/notification/notification_manager` - Current notification manager implementation
* :doc:`domain/notification/channels/index` - Notification delivery channels

.. raw:: html

   <meta http-equiv="refresh" content="0; url=domain/notification.html">

Notification Manager
-----------------

The NotificationManager is responsible for creating and dispatching notifications.

.. automodule:: backend.src.notification.manager
   :members:
   :undoc-members:
   :show-inheritance:

Notification Types
---------------

The notification types define different kinds of notifications and their properties.

.. automodule:: backend.src.notification.types
   :members:
   :undoc-members:
   :show-inheritance:

Notification Channels
------------------

The notification channels handle delivery of notifications through different media.

.. automodule:: backend.src.notification.channels
   :members:
   :undoc-members:
   :show-inheritance:

Email Notifications
----------------

Functionality for sending notifications via email.

.. automodule:: backend.src.notification.email
   :members:
   :undoc-members:
   :show-inheritance:

Push Notifications
---------------

Functionality for sending push notifications to desktop or mobile devices.

.. automodule:: backend.src.notification.push
   :members:
   :undoc-members:
   :show-inheritance:

Notification Templates
-------------------

Templates for formatting different types of notifications.

.. automodule:: backend.src.notification.templates
   :members:
   :undoc-members:
   :show-inheritance:
