Notification Channels
===================

The Notification Channels module provides different delivery mechanisms for notifications.

.. toctree::
   :maxdepth: 2

   base_channel
   console_channel
   email_channel
   file_channel

Base Channel
-----------

The BaseChannel class defines the interface that all notification channels must implement.

.. automodule:: the_aichemist_codex.backend.domain.notification.channels.base_channel
   :members:
   :undoc-members:
   :show-inheritance:

Console Channel
-------------

The ConsoleChannel outputs notifications to the console/terminal.

.. automodule:: the_aichemist_codex.backend.domain.notification.channels.console_channel
   :members:
   :undoc-members:
   :show-inheritance:

Email Channel
-----------

The EmailChannel delivers notifications via email.

.. automodule:: the_aichemist_codex.backend.domain.notification.channels.email_channel
   :members:
   :undoc-members:
   :show-inheritance:

File Channel
----------

The FileChannel outputs notifications to log files.

.. automodule:: the_aichemist_codex.backend.domain.notification.channels.file_channel
   :members:
   :undoc-members:
   :show-inheritance: