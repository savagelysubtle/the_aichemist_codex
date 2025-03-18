"""
Ingest manager implementation.

This module provides the implementation of the ingest system, which manages
content ingestion from various sources and processing through content processors.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

from ...core.interfaces.ingest_manager import IngestManager
from ...registry import Registry
from .models import ContentType, IngestContent, IngestJob, IngestSource, IngestStatus, ProcessedContent
from .processors.base_processor import BaseContentProcessor
from .sources.base_source import BaseIngestSource

logger = logging.getLogger(__name__)


class IngestManagerImpl(IngestManager):
    """
    Implementation of the ingest manager.

    This class manages the ingestion of content from various sources and
    processing through content processors.
    """

    def __init__(self):
        """Initialize the ingest manager."""
        self._registry = Registry.get_instance()
        self._sources: Dict[str, BaseIngestSource] = {}
        self._processors: Dict[str, BaseContentProcessor] = {}
        self._jobs: Dict[str, IngestJob] = {}
        self._content: Dict[str, IngestContent] = {}
        self._processed_content: Dict[str, ProcessedContent] = {}
        self._source_configs: Dict[str, IngestSource] = {}
        self._data_dir: Optional[Path] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the ingest manager."""
        if self._is_initialized:
            return

        # Initialize data directory
        project_paths = self._registry.project_paths
        self._data_dir = project_paths.get_data_dir() / "ingest"
        os.makedirs(self._data_dir, exist_ok=True)

        # Create subdirectories
        os.makedirs(self._data_dir / "jobs", exist_ok=True)
        os.makedirs(self._data_dir / "content", exist_ok=True)
        os.makedirs(self._data_dir / "processed", exist_ok=True)
        os.makedirs(self._data_dir / "sources", exist_ok=True)

        # Register default sources
        from .sources import FilesystemIngestSource, WebIngestSource

        await self.register_source(FilesystemIngestSource())
        await self.register_source(WebIngestSource())

        # Register default processors
        from .processors import TextContentProcessor, MarkdownContentProcessor, CodeContentProcessor

        await self.register_processor(TextContentProcessor())
        await self.register_processor(MarkdownContentProcessor())
        await self.register_processor(CodeContentProcessor())

        # Load source configurations
        await self._load_sources()

        # Load recent jobs
        await self._load_recent_jobs()

        self._is_initialized = True
        logger.info(f"Ingest manager initialized with {len(self._sources)} sources and {len(self._processors)} processors")

    async def close(self) -> None:
        """Close the ingest manager."""
        if not self._is_initialized:
            return

        # Close all sources
        for source in self._sources.values():
            try:
                await source.close()
            except Exception as e:
                logger.error(f"Error closing source {source.source_type}: {e}")

        # Close all processors
        for processor in self._processors.values():
            try:
                await processor.close()
            except Exception as e:
                logger.error(f"Error closing processor {processor.processor_id}: {e}")

        self._is_initialized = False
        logger.info("Ingest manager closed")

    async def register_source(self, source: BaseIngestSource) -> None:
        """
        Register an ingest source.

        Args:
            source: The source to register

        Raises:
            ValueError: If a source with the same type is already registered
            RuntimeError: If manager is not initialized
        """
        if self._is_initialized:
            # Initialize the source
            await source.initialize()

        # Register the source
        source_type = source.source_type
        if source_type in self._sources:
            raise ValueError(f"Source already registered: {source_type}")

        self._sources[source_type] = source
        logger.info(f"Registered ingest source: {source_type}")

    async def register_processor(self, processor: BaseContentProcessor) -> None:
        """
        Register a content processor.

        Args:
            processor: The processor to register

        Raises:
            ValueError: If a processor with the same ID is already registered
            RuntimeError: If manager is not initialized
        """
        if self._is_initialized:
            # Initialize the processor
            await processor.initialize()

        # Register the processor
        processor_id = processor.processor_id
        if processor_id in self._processors:
            raise ValueError(f"Processor already registered: {processor_id}")

        self._processors[processor_id] = processor
        logger.info(f"Registered content processor: {processor_id}")

    async def create_source(
        self,
        name: str,
        source_type: str,
        config: Dict[str, Any]
    ) -> IngestSource:
        """
        Create a new ingest source configuration.

        Args:
            name: Name of the source
            source_type: Type of the source
            config: Source configuration

        Returns:
            Created source configuration

        Raises:
            ValueError: If source type is not registered or config is invalid
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Check if source type exists
        if source_type not in self._sources:
            raise ValueError(f"Unknown source type: {source_type}")

        # Validate configuration
        source = self._sources[source_type]
        if not await source.validate_config(config):
            raise ValueError(f"Invalid configuration for source type: {source_type}")

        # Create source configuration
        source_config = IngestSource(
            name=name,
            type=source_type,
            config=config
        )

        # Save source configuration
        self._source_configs[source_config.id] = source_config
        await self._save_source(source_config)

        logger.info(f"Created source configuration: {source_config.id} ({name})")
        return source_config

    async def get_source(self, source_id: str) -> Optional[IngestSource]:
        """
        Get an ingest source configuration.

        Args:
            source_id: ID of the source

        Returns:
            Source configuration or None if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Check in-memory cache
        if source_id in self._source_configs:
            return self._source_configs[source_id]

        # Try to load from disk
        source_file = self._data_dir / "sources" / f"{source_id}.json"
        if source_file.exists():
            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                source = IngestSource.from_dict(data)
                self._source_configs[source_id] = source
                return source
            except Exception as e:
                logger.error(f"Error loading source {source_id}: {e}")

        return None

    async def update_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[IngestSource]:
        """
        Update an ingest source configuration.

        Args:
            source_id: ID of the source
            name: New name (or None to keep current)
            config: New configuration (or None to keep current)

        Returns:
            Updated source configuration or None if not found

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Get source
        source_config = await self.get_source(source_id)
        if not source_config:
            logger.warning(f"Source not found: {source_id}")
            return None

        # Update fields
        if name is not None:
            source_config.name = name

        if config is not None:
            # Validate new configuration
            source = self._sources[source_config.type]
            if not await source.validate_config(config):
                raise ValueError(f"Invalid configuration for source type: {source_config.type}")

            source_config.config = config

        # Save source configuration
        await self._save_source(source_config)

        logger.info(f"Updated source configuration: {source_id}")
        return source_config

    async def delete_source(self, source_id: str) -> bool:
        """
        Delete an ingest source configuration.

        Args:
            source_id: ID of the source

        Returns:
            True if source was deleted, False if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Check if source exists
        if source_id not in self._source_configs:
            source_config = await self.get_source(source_id)
            if not source_config:
                logger.warning(f"Source not found: {source_id}")
                return False

        # Remove from cache
        if source_id in self._source_configs:
            del self._source_configs[source_id]

        # Delete source file
        source_file = self._data_dir / "sources" / f"{source_id}.json"
        if source_file.exists():
            try:
                os.remove(source_file)
            except Exception as e:
                logger.error(f"Error deleting source file {source_file}: {e}")
                return False

        logger.info(f"Deleted source configuration: {source_id}")
        return True

    async def get_all_sources(self) -> List[IngestSource]:
        """
        Get all ingest source configurations.

        Returns:
            List of source configurations

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Load all sources from disk if not cached
        source_files = (self._data_dir / "sources").glob("*.json")
        for source_file in source_files:
            source_id = source_file.stem
            if source_id not in self._source_configs:
                await self.get_source(source_id)

        return list(self._source_configs.values())

    async def list_content(self, source_id: str) -> List[Dict[str, Any]]:
        """
        List content available in a source.

        Args:
            source_id: ID of the source

        Returns:
            List of content items with metadata

        Raises:
            ValueError: If source not found
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Get source configuration
        source_config = await self.get_source(source_id)
        if not source_config:
            raise ValueError(f"Source not found: {source_id}")

        # Get source implementation
        source_type = source_config.type
        if source_type not in self._sources:
            raise ValueError(f"Source type not registered: {source_type}")

        source = self._sources[source_type]

        # Update last used time
        source_config.last_used = datetime.now()
        await self._save_source(source_config)

        # List content
        return await source.list_content(source_config)

    async def create_job(
        self,
        name: str,
        source_ids: List[str],
        processor_ids: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IngestJob:
        """
        Create a new ingest job.

        Args:
            name: Name of the job
            source_ids: IDs of sources to ingest from
            processor_ids: IDs of processors to use (or None for default)
            config: Job configuration

        Returns:
            Created job

        Raises:
            ValueError: If any source or processor is not found
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Validate sources
        for source_id in source_ids:
            source_config = await self.get_source(source_id)
            if not source_config:
                raise ValueError(f"Source not found: {source_id}")

        # Use all processors if none specified
        if not processor_ids:
            processor_ids = list(self._processors.keys())
        else:
            # Validate processors
            for processor_id in processor_ids:
                if processor_id not in self._processors:
                    raise ValueError(f"Processor not found: {processor_id}")

        # Create job
        job = IngestJob(
            name=name,
            source_ids=source_ids,
            processor_ids=processor_ids,
            status=IngestStatus.PENDING,
            config=config or {}
        )

        # Save job
        self._jobs[job.id] = job
        await self._save_job(job)

        logger.info(f"Created ingest job: {job.id} ({name})")
        return job

    async def get_job(self, job_id: str) -> Optional[IngestJob]:
        """
        Get an ingest job.

        Args:
            job_id: ID of the job

        Returns:
            Job or None if not found

        Raises:
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Check in-memory cache
        if job_id in self._jobs:
            return self._jobs[job_id]

        # Try to load from disk
        job_file = self._data_dir / "jobs" / f"{job_id}.json"
        if job_file.exists():
            try:
                with open(job_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                job = IngestJob.from_dict(data)
                self._jobs[job_id] = job
                return job
            except Exception as e:
                logger.error(f"Error loading job {job_id}: {e}")

        return None

    async def run_job(self, job_id: str) -> IngestJob:
        """
        Run an ingest job.

        Args:
            job_id: ID of the job

        Returns:
            Updated job

        Raises:
            ValueError: If job not found or already running
            RuntimeError: If manager is not initialized
        """
        self._ensure_initialized()

        # Get job
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Check job status
        if job.status == IngestStatus.RUNNING:
            raise ValueError(f"Job already running: {job_id}")

        # Update job status
        job.status = IngestStatus.RUNNING
        job.started_at = datetime.now()
        job.error_message = None
        await self._save_job(job)

        logger.info(f"Running ingest job: {job_id}")

        try:
            # Process each source
            for source_id in job.source_ids:
                # Get source
                source_config = await self.get_source(source_id)
                if not source_config:
                    raise ValueError(f"Source not found: {source_id}")

                # Get source implementation
                source_type = source_config.type
                if source_type not in self._sources:
                    raise ValueError(f"Source type not registered: {source_type}")

                source = self._sources[source_type]

                # Process content
                content = await source.get_content(source_config)
                if not content:
                    raise ValueError(f"Content not found for source: {source_id}")

                # Process content with processors
                for processor_id in job.processor_ids:
                    processor = self._processors[processor_id]
                    if not processor:
                        raise ValueError(f"Processor not found: {processor_id}")

                    processed_content = await processor.process_content(content)
                    if not processed_content:
                        raise ValueError(f"Processed content not found for processor: {processor_id}")

                    # Save processed content
                    await self._save_processed_content(processed_content)

                # Update source status
                source_config.last_used = datetime.now()
                await self._save_source(source_config)

            # Update job status
            job.status = IngestStatus.COMPLETED
            await self._save_job(job)

            logger.info(f"Completed ingest job: {job_id}")
            return job
        except Exception as e:
            # Update job status
            job.status = IngestStatus.FAILED
            job.error_message = str(e)
            await self._save_job(job)

            logger.error(f"Failed to run ingest job: {job_id}, error: {e}")
            raise
```