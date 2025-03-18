"""
Text content analyzer for AIChemist Codex.

This module provides content analysis capabilities for text-based files,
extracting metadata, entities, keywords, and enabling summarization.
"""

import logging
import re
from pathlib import Path
from typing import Any

from the_aichemist_codex.backend.core.exceptions import AnalysisError
from the_aichemist_codex.backend.core.interfaces import FileReader

from .base_analyzer import BaseContentAnalyzer

logger = logging.getLogger(__name__)


class TextContentAnalyzer(BaseContentAnalyzer):
    """
    Content analyzer specialized for text-based files.

    This analyzer provides analysis for plain text, markdown, and
    other text-based file formats.
    """

    def __init__(self, file_reader: FileReader):
        """
        Initialize the text content analyzer.

        Args:
            file_reader: Service for accessing file content
        """
        super().__init__(file_reader)

    async def _register_supported_types(self) -> None:
        """
        Register supported file types and content types.

        This analyzer supports common text formats like txt, md, etc.
        """
        # Register supported file extensions
        self._supported_extensions.update(
            [
                "txt",
                "md",
                "markdown",
                "rst",
                "asc",
                "text",
                "log",
                "info",
                "readme",
                "license",
                "config",
                "ini",
                "cfg",
                "conf",
                "properties",
            ]
        )

        # Register MIME type mappings
        self._mime_type_map.update(
            {
                "txt": "text/plain",
                "md": "text/markdown",
                "markdown": "text/markdown",
                "rst": "text/x-rst",
                "asc": "text/plain",
                "text": "text/plain",
                "log": "text/plain",
                "readme": "text/plain",
                "license": "text/plain",
                "config": "text/plain",
                "ini": "text/plain",
                "cfg": "text/plain",
                "conf": "text/plain",
                "properties": "text/plain",
            }
        )

        # Register supported content types
        self._supported_content_types.update(
            [
                "text/plain",
                "text/markdown",
                "text/x-rst",
            ]
        )

    async def analyze_text(
        self,
        text: str,
        content_type: str | None = None,
        file_path: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze text content and extract meaningful information.

        Args:
            text: The text content to analyze
            content_type: Optional hint about the content type
            file_path: Optional path to the source file (for context)
            options: Optional dictionary of analyzer-specific options

        Returns:
            Dictionary containing extracted information

        Raises:
            AnalysisError: If analysis fails
        """
        self._ensure_initialized()

        if not text:
            return {
                "word_count": 0,
                "line_count": 0,
                "char_count": 0,
                "is_empty": True,
                "average_line_length": 0,
                "average_word_length": 0,
                "language": None,
                "content_preview": "",
            }

        try:
            # Basic text statistics
            lines = text.splitlines()
            words = re.findall(r"\b\w+\b", text.lower())

            line_count = len(lines)
            word_count = len(words)
            char_count = len(text)

            # Calculate averages
            avg_line_length = char_count / max(line_count, 1)
            avg_word_length = sum(len(word) for word in words) / max(word_count, 1)

            # Simple language detection heuristic
            language = self._detect_language(text)

            # Create content preview (up to 500 chars)
            content_preview = text[:500] + ("..." if len(text) > 500 else "")

            # Prepare result
            result = {
                "word_count": word_count,
                "line_count": line_count,
                "char_count": char_count,
                "is_empty": char_count == 0,
                "average_line_length": round(avg_line_length, 2),
                "average_word_length": round(avg_word_length, 2),
                "language": language,
                "content_preview": content_preview,
            }

            # Extract additional metadata based on content type
            if content_type == "text/markdown":
                result.update(self._analyze_markdown(text))

            return result

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            raise AnalysisError(
                f"Error analyzing text: {e}",
                file_path=str(file_path) if file_path else None,
                analyzer_type=self.__class__.__name__,
                content_type=content_type,
            ) from e

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words.

        Args:
            text: Text to analyze

        Returns:
            Detected language code (e.g., "en", "es")
        """
        # This is a very basic implementation
        # In a real project, use a proper language detection library

        # Convert to lowercase and get words
        text_lower = text.lower()

        # Count common English words
        english_words = [
            "the",
            "and",
            "is",
            "in",
            "to",
            "of",
            "that",
            "for",
            "it",
            "with",
        ]
        english_count = sum(
            1 for word in english_words if f" {word} " in f" {text_lower} "
        )

        # Count common Spanish words
        spanish_words = ["el", "la", "que", "de", "en", "y", "a", "los", "del", "se"]
        spanish_count = sum(
            1 for word in spanish_words if f" {word} " in f" {text_lower} "
        )

        # Simple decision
        if english_count > spanish_count:
            return "en"
        elif spanish_count > english_count:
            return "es"
        else:
            return "unknown"

    def _analyze_markdown(self, text: str) -> dict[str, Any]:
        """
        Extract Markdown-specific information.

        Args:
            text: Markdown content to analyze

        Returns:
            Dictionary with Markdown-specific metadata
        """
        # Find headings
        headings = []
        heading_pattern = r"^(#{1,6})\s+(.+?)(?:\s+#+)?$"

        for line in text.splitlines():
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append({"level": level, "title": title})

        # Count code blocks
        code_blocks = len(re.findall(r"```\w*\n[\s\S]*?\n```", text))

        # Count tables
        tables = len(re.findall(r"\|(?:[^|]+\|)+\s*\n\|(?:[:-]+\|)+\s*\n", text))

        # Count links
        links = len(re.findall(r"\[.+?\]\(.+?\)", text))

        return {
            "headings": headings,
            "code_blocks_count": code_blocks,
            "tables_count": tables,
            "links_count": links,
            "is_markdown": True,
        }

    async def summarize(
        self, content: str | Path, max_length: int = 500, format: str = "text"
    ) -> str:
        """
        Generate a summary of text content.

        This implementation extracts key sentences from the text
        to create a representative summary.

        Args:
            content: Either a string of content or a path to a file
            max_length: Maximum length of the summary in characters
            format: Output format (e.g., "text", "html", "markdown")

        Returns:
            Generated summary as a string

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If summarization fails
        """
        self._ensure_initialized()

        try:
            # Load content
            text = await self._load_content(content)

            if not text:
                return ""

            # Split into sentences
            sentences = re.split(r"(?<=[.!?])\s+", text)

            if not sentences:
                return ""

            # If text is already short, return it as is
            if len(text) <= max_length:
                return text

            # Simple extractive summarization:
            # 1. Take the first sentence (often contains the main point)
            # 2. Take sentences with keywords
            # 3. Take the last sentence (often contains a conclusion)

            summary_sentences = [sentences[0]]

            # Extract keywords (simple implementation)
            words = re.findall(r"\b\w+\b", text.lower())
            word_count = {}
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_count[word] = word_count.get(word, 0) + 1

            # Get top keywords
            top_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            top_keywords = [word for word, _ in top_keywords]

            # Select sentences with keywords
            for sentence in sentences[1:-1]:
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in top_keywords):
                    summary_sentences.append(sentence)
                if len(" ".join(summary_sentences)) >= max_length:
                    break

            # Add the last sentence if there's room
            if (
                sentences[-1] not in summary_sentences
                and len(" ".join(summary_sentences) + " " + sentences[-1]) <= max_length
            ):
                summary_sentences.append(sentences[-1])

            # Join sentences and ensure we don't exceed max_length
            summary = " ".join(summary_sentences)
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            return summary

        except Exception as e:
            file_path = str(content) if isinstance(content, Path) else None
            logger.error(f"Error summarizing content: {e}")
            raise AnalysisError(
                f"Error summarizing content: {e}",
                file_path=file_path,
                analyzer_type=self.__class__.__name__,
            ) from e

    async def extract_entities(
        self,
        content: str | Path,
        entity_types: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract named entities from text content.

        This basic implementation uses regex patterns to find
        common entity types like emails, URLs, phone numbers, etc.

        Args:
            content: Either a string of content or a path to a file
            entity_types: Types of entities to extract
            min_confidence: Minimum confidence score for extracted entities

        Returns:
            Dictionary mapping entity types to lists of extracted entities

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If entity extraction fails
        """
        self._ensure_initialized()

        try:
            # Load content
            text = await self._load_content(content)

            # Initialize results
            result: dict[str, list[dict[str, Any]]] = {}

            # Patterns for various entity types
            patterns = {
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "url": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?",
                "phone": r"\b(?:\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
                "date": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
                "time": r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\s*(?:AM|PM|am|pm)?\b",
                "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            }

            # Filter entity types if specified
            if entity_types:
                patterns = {k: v for k, v in patterns.items() if k in entity_types}

            # Extract entities for each pattern
            for entity_type, pattern in patterns.items():
                matches = re.finditer(pattern, text)
                entities = []

                for match in matches:
                    entities.append(
                        {
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 1.0,  # Basic regex matches have full confidence
                        }
                    )

                if entities:
                    result[entity_type] = entities

            return result

        except Exception as e:
            file_path = str(content) if isinstance(content, Path) else None
            logger.error(f"Error extracting entities: {e}")
            raise AnalysisError(
                f"Error extracting entities: {e}",
                file_path=file_path,
                analyzer_type=self.__class__.__name__,
            ) from e

    async def extract_keywords(
        self, content: str | Path, max_keywords: int = 10, min_relevance: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Extract keywords or key phrases from text content.

        This implementation uses a simple TF (term frequency) approach
        to identify important words in the text.

        Args:
            content: Either a string of content or a path to a file
            max_keywords: Maximum number of keywords to extract
            min_relevance: Minimum relevance score for keywords

        Returns:
            List of dictionaries containing keywords and their relevance scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If keyword extraction fails
        """
        self._ensure_initialized()

        try:
            # Load content
            text = await self._load_content(content)

            if not text.strip():
                return []

            # Tokenize and clean text
            # (Remove punctuation, convert to lowercase, etc.)
            words = re.findall(r"\b\w+\b", text.lower())

            # Remove common stop words
            stop_words = {
                "a",
                "an",
                "the",
                "and",
                "or",
                "but",
                "if",
                "then",
                "else",
                "when",
                "at",
                "from",
                "by",
                "for",
                "with",
                "about",
                "to",
                "in",
                "on",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "can",
                "could",
                "shall",
                "should",
                "will",
                "would",
                "may",
                "might",
                "must",
                "that",
                "this",
                "these",
                "those",
                "it",
                "its",
                "of",
                "not",
            }

            filtered_words = [
                word for word in words if word not in stop_words and len(word) > 2
            ]

            if not filtered_words:
                return []

            # Count word frequencies
            word_counts = {}
            for word in filtered_words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Find maximum frequency for normalization
            max_count = max(word_counts.values())

            # Convert to list of dictionaries with normalized scores
            keywords = [
                {"keyword": word, "relevance": count / max_count, "count": count}
                for word, count in word_counts.items()
                if count / max_count >= min_relevance
            ]

            # Sort by relevance and limit to max_keywords
            keywords.sort(key=lambda x: x["relevance"], reverse=True)
            return keywords[:max_keywords]

        except Exception as e:
            file_path = str(content) if isinstance(content, Path) else None
            logger.error(f"Error extracting keywords: {e}")
            raise AnalysisError(
                f"Error extracting keywords: {e}",
                file_path=file_path,
                analyzer_type=self.__class__.__name__,
            ) from e

    async def classify_content(
        self,
        content: str | Path,
        taxonomy: list[str] | None = None,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Classify text content into categories.

        This basic implementation uses keyword matching to categorize
        content into predefined categories.

        Args:
            content: Either a string of content or a path to a file
            taxonomy: Optional list of categories to use
            min_confidence: Minimum confidence score for classifications

        Returns:
            List of dictionaries containing categories and confidence scores

        Raises:
            FileError: If the file cannot be read
            AnalysisError: If classification fails
        """
        self._ensure_initialized()

        try:
            # Load content
            text = await self._load_content(content)
            text_lower = text.lower()

            # Define default taxonomy if not provided
            default_taxonomy = {
                "technical": [
                    "code",
                    "function",
                    "class",
                    "module",
                    "library",
                    "programming",
                    "software",
                    "hardware",
                    "algorithm",
                    "data",
                    "system",
                    "computer",
                ],
                "business": [
                    "business",
                    "market",
                    "strategy",
                    "sales",
                    "customer",
                    "product",
                    "service",
                    "revenue",
                    "profit",
                    "company",
                    "industry",
                    "management",
                ],
                "creative": [
                    "design",
                    "art",
                    "creative",
                    "style",
                    "color",
                    "image",
                    "visual",
                    "photography",
                    "illustration",
                    "content",
                    "story",
                    "video",
                ],
                "scientific": [
                    "research",
                    "science",
                    "experiment",
                    "study",
                    "analysis",
                    "method",
                    "theory",
                    "observation",
                    "hypothesis",
                    "test",
                    "measure",
                    "result",
                ],
                "educational": [
                    "learn",
                    "education",
                    "school",
                    "student",
                    "teacher",
                    "course",
                    "training",
                    "skill",
                    "knowledge",
                    "curriculum",
                    "teaching",
                    "lesson",
                ],
            }

            # Use custom taxonomy if provided
            categories = {}
            if taxonomy:
                # Simple implementation: assume taxonomy items are the categories
                for category in taxonomy:
                    categories[category] = []
            else:
                categories = default_taxonomy

            # Calculate confidence scores for each category
            results = []
            for category, keywords in categories.items():
                # Count keyword occurrences
                matches = 0
                for keyword in keywords:
                    matches += text_lower.count(keyword)

                # Calculate confidence based on matches
                # This is a simple heuristic that could be improved
                if matches > 0:
                    # Normalize confidence: more matches = higher confidence
                    confidence = min(0.3 + (matches / len(keywords) * 0.7), 1.0)

                    if confidence >= min_confidence:
                        results.append(
                            {
                                "category": category,
                                "confidence": round(confidence, 2),
                                "match_count": matches,
                            }
                        )

            # Sort by confidence
            results.sort(key=lambda x: x["confidence"], reverse=True)
            return results

        except Exception as e:
            file_path = str(content) if isinstance(content, Path) else None
            logger.error(f"Error classifying content: {e}")
            raise AnalysisError(
                f"Error classifying content: {e}",
                file_path=file_path,
                analyzer_type=self.__class__.__name__,
            ) from e
