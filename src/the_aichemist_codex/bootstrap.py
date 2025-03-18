async def initialize_app():
    """Initialize the application."""
    # ... existing code ...

    # Initialize Output Formatter
    logger.info("Initializing Output Formatter...")
    formatter_manager = registry.formatter_manager
    await formatter_manager.initialize()

    # Initialize Notification System
    logger.info("Initializing Notification System...")
    notification_manager = registry.notification_manager
    await notification_manager.initialize()

    # Initialize Ingest System
    logger.info("Initializing Ingest System...")
    ingest_manager = registry.ingest_manager
    await ingest_manager.initialize()

    # ... existing code ...
