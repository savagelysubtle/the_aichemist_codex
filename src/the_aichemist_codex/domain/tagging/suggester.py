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
from the_aichemist_codex.domain.value_objects import FileDataForTagging

logger = logging.getLogger(__name__)


class TagSuggester:
    """
    Suggests tags for files based on multiple strategies, using domain interfaces.
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(
        self: "TagSuggester",
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

    async def suggest_tags(
        self: "TagSuggester",
        tagging_data: FileDataForTagging,
        min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
        max_suggestions: int = 10,
    ) -> list[tuple[str, float]]:
        """
        Suggest tags for a file using multiple strategies.

        Args:
            tagging_data: Value object containing file data for tagging.
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
                    tagging_data, confidence_threshold=min_confidence
                )
                for tag, conf in classifier_suggestions:
                    all_suggestions[tag] = max(all_suggestions.get(tag, 0.0), conf)
            except Exception as e:
                logger.error(f"Error getting classifier suggestions: {e}")

        # 2. Content-Based Suggestions (from metadata)
        content_suggestions = self._get_content_based_suggestions(
            tagging_data, min_confidence
        )
        for tag, conf in content_suggestions:
            all_suggestions[tag] = max(
                all_suggestions.get(tag, 0.0), conf * 0.9
            )  # Weight content-based slightly lower

        # 3. Collaborative Suggestions (based on similar files)
        try:
            similar_tags = await self._get_collaborative_suggestions(
                tagging_data.path, min_confidence
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
        self: "TagSuggester", tagging_data: FileDataForTagging, min_confidence: float
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

        # Suggest tags based on file extension
        extension = tagging_data.path.suffix
        if extension:
            suggestions.append((f"ext:{extension.lstrip('.')}", conf_ext))

        # Suggest tags based on mime type
        if tagging_data.mime_type and "/" in tagging_data.mime_type:
            main_type, sub_type = tagging_data.mime_type.split("/", 1)
            suggestions.append((f"type:{main_type}", conf_mime))
            if sub_type != "*":
                suggestions.append((f"format:{sub_type}", conf_format))

        # Suggest tags based on extracted topics
        if tagging_data.topics:
            for topic_dict in tagging_data.topics:
                for topic, score in topic_dict.items():
                    if isinstance(score, int | float) and score >= min_confidence:
                        suggestions.append((f"topic:{topic}", score * conf_topic))

        # Suggest tags based on keywords
        if tagging_data.keywords:
            for keyword in tagging_data.keywords[:5]:  # Limit keyword tags
                suggestions.append((keyword, conf_keyword))

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
        self: "TagSuggester", file_path: Path, min_confidence: float
    ) -> list[tuple[str, float]]:
        """
        Get suggestions by checking tags of related files.
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

        except Exception as e:
            logger.error(f"Error during collaborative suggestion: {e}")

        return [
            (tag, conf) for tag, conf in suggestions.items() if conf >= min_confidence
        ]

    # Methods like analyze_directory and batch_suggest_tags would need to be adapted
    # to use an injected FileReader or accept FileMetadata objects directly.
