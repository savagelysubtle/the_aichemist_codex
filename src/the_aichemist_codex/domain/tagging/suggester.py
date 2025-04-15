"""
Tag suggestion system using domain interfaces.
"""

import logging
from pathlib import Path

# Import domain interfaces and entities
from the_aichemist_codex.domain.repositories.interfaces.tag_repository import (
    TagRepositoryInterface,
)
from the_aichemist_codex.domain.services.interfaces.tag_classifier import (
    TagClassifierInterface,
)

# Import infrastructure type hint for FileMetadata, but avoid direct infrastructure logic
from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata
from the_aichemist_codex.infrastructure.utils.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


class TagSuggester:
    """
    Suggests tags for files based on multiple strategies, using domain interfaces.
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(
        self,
        tag_repository: TagRepositoryInterface,
        classifier: TagClassifierInterface | None = None,
    ) -> None:
        """
        Initialize the tag suggester.

        Args:
            tag_repository: Implementation of TagRepositoryInterface.
            classifier: Optional implementation of TagClassifierInterface.
        """
        self.tag_repository = tag_repository
        self.classifier = classifier
        self.batch_processor = BatchProcessor()

    async def suggest_tags(
        self,
        file_metadata: FileMetadata,
        min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
        max_suggestions: int = 10,
    ) -> list[tuple[str, float]]:
        """
        Suggest tags for a file using multiple strategies.

        Args:
            file_metadata: FileMetadata object containing file info and extracted features.
            min_confidence: Minimum confidence threshold for suggestions.
            max_suggestions: Maximum number of suggestions to return.

        Returns:
            List of (tag_name, confidence) tuples.
        """
        all_suggestions: dict[str, float] = {}

        # 1. Classifier Suggestions (if available)
        if self.classifier:
            try:
                classifier_suggestions = await self.classifier.classify(
                    file_metadata, confidence_threshold=min_confidence
                )
                for tag, conf in classifier_suggestions:
                    all_suggestions[tag] = max(all_suggestions.get(tag, 0.0), conf)
            except Exception as e:
                logger.error(f"Error getting classifier suggestions: {e}")

        # 2. Content-Based Suggestions (from metadata)
        content_suggestions = self._get_content_based_suggestions(
            file_metadata, min_confidence
        )
        for tag, conf in content_suggestions:
            all_suggestions[tag] = max(
                all_suggestions.get(tag, 0.0), conf * 0.9
            )  # Weight content-based slightly lower

        # 3. Collaborative Suggestions (based on similar files - simplified)
        # Note: A full implementation might involve finding similar files first.
        # Here, we simulate by looking at tags of files with same extension/in same dir.
        # This logic might be better placed in the application layer or a dedicated service.
        try:
            similar_tags = await self._get_collaborative_suggestions(
                file_metadata.path, min_confidence
            )
            for tag, conf in similar_tags:
                all_suggestions[tag] = max(
                    all_suggestions.get(tag, 0.0), conf * 0.8
                )  # Weight collaborative lower
        except Exception as e:
            logger.error(f"Error getting collaborative suggestions: {e}")

        # Combine, sort, and limit
        suggestions = [
            (tag, conf)
            for tag, conf in all_suggestions.items()
            if conf >= min_confidence
        ]
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:max_suggestions]

    def _get_content_based_suggestions(
        self, file_metadata: FileMetadata, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Generate tag suggestions based purely on the file's metadata attributes.
        """
        suggestions = []
        conf_ext = 0.95
        conf_mime = 0.9
        conf_format = 0.85
        conf_topic = 0.8
        conf_keyword = 0.75
        conf_lang = 0.95
        conf_content_type = 0.9

        # Suggest tags based on file extension
        if file_metadata.extension:
            suggestions.append((f"ext:{file_metadata.extension.lstrip('.')}", conf_ext))

        # Suggest tags based on mime type
        if file_metadata.mime_type and "/" in file_metadata.mime_type:
            main_type, sub_type = file_metadata.mime_type.split("/", 1)
            suggestions.append((f"type:{main_type}", conf_mime))
            if sub_type != "*":
                suggestions.append((f"format:{sub_type}", conf_format))

        # Suggest tags based on extracted topics
        if hasattr(file_metadata, "topics") and file_metadata.topics:
            for topic_dict in file_metadata.topics:
                for topic, score in topic_dict.items():
                    if score >= min_confidence:
                        suggestions.append((f"topic:{topic}", score * conf_topic))

        # Suggest tags based on keywords
        if hasattr(file_metadata, "keywords") and file_metadata.keywords:
            for keyword in file_metadata.keywords[:5]:  # Limit keyword tags
                suggestions.append((keyword, conf_keyword))

        # Suggest tags based on language
        if hasattr(file_metadata, "language") and file_metadata.language:
            suggestions.append((f"lang:{file_metadata.language}", conf_lang))

        # Suggest tags based on content type
        if hasattr(file_metadata, "content_type") and file_metadata.content_type:
            suggestions.append(
                (f"content:{file_metadata.content_type}", conf_content_type)
            )

        # Filter duplicates by taking max confidence, then filter by threshold
        final_suggestions = {}
        for tag, conf in suggestions:
            final_suggestions[tag] = max(final_suggestions.get(tag, 0.0), conf)

        return [
            (tag, conf)
            for tag, conf in final_suggestions.items()
            if conf >= min_confidence
        ]

    async def _get_collaborative_suggestions(
        self, file_path: Path, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Simulate collaborative suggestions by checking tags of related files.
        In a real system, this would use more advanced techniques.
        """
        suggestions = {}
        try:
            # Get tags from files in the same directory
            parent_dir = file_path.parent
            siblings = [
                f for f in parent_dir.glob("*") if f.is_file() and f != file_path
            ]

            for sibling in siblings[:10]:  # Limit sibling check
                sibling_tags = await self.tag_repository.get_tags_for_file(sibling)
                for tag_assoc in sibling_tags:
                    tag = await self.tag_repository.get_tag(tag_assoc.tag_id)
                    if tag:
                        suggestions[tag.name] = max(
                            suggestions.get(tag.name, 0.0), 0.6
                        )  # Base confidence for directory relation

            # Get tags from files with the same extension (simplified query)
            # Note: This requires a repository method not strictly defined in the interface yet
            # We might need to enhance the interface or use a different approach.
            # Placeholder: Assume we can get some common tags for the extension.
            if file_path.suffix:
                # Example: Get top 5 tags associated with this extension (requires new repo method)
                # common_ext_tags = await self.tag_repository.get_common_tags_for_extension(file_path.suffix)
                # for tag_name, freq_score in common_ext_tags:
                #    suggestions[tag_name] = max(suggestions.get(tag_name, 0.0), 0.7 * freq_score)
                pass

        except Exception as e:
            logger.error(f"Error during collaborative suggestion simulation: {e}")

        return [
            (tag, conf) for tag, conf in suggestions.items() if conf >= min_confidence
        ]

    # Methods like analyze_directory and batch_suggest_tags would need to be adapted
    # to use an injected FileReader or accept FileMetadata objects directly.
