from .core.interfaces.notification_manager import NotificationManager
from .core.interfaces.ingest_manager import IngestManager


class Registry:
    @property
    def notification_manager(self) -> NotificationManager:
        """Get the notification manager."""
        return self._lazy_load(
            "notification_manager",
            NotificationManager,
            self._create_notification_manager,
        )

    def _create_notification_manager(self) -> NotificationManager:
        """Create the notification manager."""
        from .backend.domain.notification import NotificationManagerImpl

        return NotificationManagerImpl()

    @property
    def ingest_manager(self) -> IngestManager:
        """Get the ingest manager."""
        return self._lazy_load("ingest_manager", IngestManager, self._create_ingest_manager)

    def _create_ingest_manager(self) -> IngestManager:
        """Create the ingest manager."""
        from .backend.domain.ingest import IngestManagerImpl
        return IngestManagerImpl()
