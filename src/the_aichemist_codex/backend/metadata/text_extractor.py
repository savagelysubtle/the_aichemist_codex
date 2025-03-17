"""Text metadata extractor for extracting information from text files.

This module provides functionality for analyzing text content to extract
keywords, topics, entities, and other metadata from text files.
"""

# mypy: disable-error-code="return-value"

import asyncio
import logging
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import (
    CountVectorizer,  # type: ignore
    TfidfVectorizer,
)

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.utils.cache_manager import CacheManager

from .extractor import BaseMetadataExtractor, MetadataExtractorRegistry

logger = logging.getLogger(__name__)


@MetadataExtractorRegistry.register
class TextMetadataExtractor(BaseMetadataExtractor):
    """Metadata extractor for text files.

    Analyzes text content to extract keywords, topics, entities, and other
    text-based metadata using NLP techniques.
    """

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        max_keywords: int = 15,
        max_topics: int = 5,
        min_keyword_length: int = 3,
        min_keyword_freq: int = 2,
    ):
        """Initialize the text metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching results
            max_keywords: Maximum number of keywords to extract
            max_topics: Maximum number of topics to extract
            min_keyword_length: Minimum length for a keyword
            min_keyword_freq: Minimum frequency for a keyword
        """
        self.cache_manager = cache_manager
        self.max_keywords = max_keywords
        self.max_topics = max_topics
        self.min_keyword_length = min_keyword_length
        self.min_keyword_freq = min_keyword_freq

        # Common English stop words to filter out
        self.stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "because",
            "as",
            "what",
            "when",
            "where",
            "how",
            "who",
            "which",
            "this",
            "that",
            "these",
            "those",
            "then",
            "just",
            "so",
            "than",
            "such",
            "both",
            "through",
            "about",
            "for",
            "is",
            "of",
            "while",
            "during",
            "to",
        }

        # Initialize TF-IDF vectorizer for keyword extraction
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=min_keyword_freq,
        )

        # Regular expressions for entity extraction
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.url_pattern = re.compile(
            r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*(?:\?[=&%\w.-]*)?(?:#[\w-]*)?"
        )
        self.date_pattern = re.compile(
            r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}\b"
        )
        self.phone_pattern = re.compile(
            r"\b\+?(\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        )

        # Initialize simple language detector based on common words
        self.language_markers = {
            "en": [
                "the",
                "and",
                "of",
                "to",
                "in",
                "that",
                "for",
                "it",
                "with",
                "as",
                "was",
                "on",
            ],
            "es": [
                "el",
                "la",
                "de",
                "que",
                "y",
                "en",
                "un",
                "por",
                "con",
                "no",
                "una",
                "para",
            ],
            "fr": [
                "le",
                "la",
                "de",
                "et",
                "à",
                "en",
                "un",
                "une",
                "que",
                "qui",
                "dans",
                "par",
            ],
            "de": [
                "der",
                "die",
                "das",
                "und",
                "zu",
                "in",
                "den",
                "von",
                "mit",
                "auf",
                "für",
                "ist",
            ],
        }

    @property
    def supported_mime_types(self) -> list[str]:
        """List of MIME types supported by this extractor."""
        return [
            "text/*",
            "application/json",
            "application/xml",
            "application/yaml",
            "application/x-yaml",
            "application/toml",
        ]

    async def extract(  # type: ignore
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """Extract metadata from a text file.

        Args:
            file_path: Path to the file
            content: Optional pre-loaded file content
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            A dictionary containing extracted metadata
        """
        start_time = time.time()

        # Check if we have cached results
        if self.cache_manager and hasattr(self.cache_manager, "get"):
            cache_key = f"text_metadata:{file_path}"
            # Properly await the async cache manager get method
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result and isinstance(cached_result, dict):
                logger.debug(f"Using cached metadata for {file_path}")
                return cached_result  # type: ignore

        # Get the content if not provided
        if content is None:
            # Convert file_path to Path object
            path = Path(file_path) if isinstance(file_path, str) else file_path
            content = await self._get_content(path)  # type: ignore
            if not content:
                return {
                    "error": "Failed to read file content",
                    "extraction_complete": False,
                    "extraction_confidence": 0.0,
                    "extraction_time": time.time() - start_time,
                }

        # Detect language (simplified approach)
        language = self._detect_language(content)

        # Extract text metadata
        extracted_data: dict[str, Any] = {}
        extracted_data["language"] = language

        # Only proceed with English content for now
        if language == "en":
            # Extract keywords using TF-IDF
            keywords = await asyncio.to_thread(self._extract_keywords, content)
            extracted_data["keywords"] = keywords

            # Extract topics
            topics = await asyncio.to_thread(self._extract_topics, content)
            extracted_data["topics"] = topics

            # Extract entities
            entities = self._extract_entities(content)
            extracted_data["entities"] = entities

            # Generate potential tags from the extracted information
            tags = self._generate_tags(keywords, topics, entities)
            extracted_data["tags"] = tags

            # Generate a simple summary
            summary = self._generate_summary(content)
            extracted_data["summary"] = summary

        # Mark extraction as complete
        extracted_data["extraction_complete"] = True
        extracted_data["extraction_confidence"] = 0.8  # Reasonable default
        extracted_data["extraction_time"] = time.time() - start_time

        # Cache the results if we have a cache manager
        if self.cache_manager and hasattr(self.cache_manager, "put"):
            await self.cache_manager.put(cache_key, extracted_data)  # type: ignore

        return extracted_data

    def _detect_language(self, content: str) -> str:
        """Detect the language of the content.

        This is a very simplified implementation. In a real-world application,
        you would use a proper language detection library.

        Args:
            content: The text content

        Returns:
            The detected language code (e.g., 'en' for English)
        """
        # Simplified implementation - just assuming English for now
        return "en"

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract keywords from the content using TF-IDF.

        Args:
            content: The text content

        Returns:
            A list of extracted keywords
        """
        try:
            # Fit the vectorizer (this would be done once in a real implementation)
            X = self.tfidf_vectorizer.fit_transform([content])

            # Get feature names
            feature_names = self.tfidf_vectorizer.get_feature_names_out()

            # Convert sparse matrix to numpy array directly
            # This avoids calling .toarray() or .sum() on the spmatrix directly
            X_array = np.asarray(X.todense())  # type: ignore

            # Now we can safely sum with numpy
            sums = np.sum(X_array, axis=0).ravel()

            # Create feature scores
            feature_scores = list(zip(feature_names, sums, strict=False))

            # Sort by score
            sorted_features = sorted(feature_scores, key=lambda x: x[1], reverse=True)

            # Filter out short keywords and return the top max_keywords
            keywords = [
                word
                for word, score in sorted_features
                if len(word) >= self.min_keyword_length
                and word.lower() not in self.stop_words
            ]

            return keywords[: self.max_keywords]
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

    def _extract_topics(self, content: str) -> list[dict[str, float]]:
        """Extract topics from the content.

        In a real implementation, this would use a topic modeling algorithm like LDA.
        For simplicity, we'll use a basic approach based on word co-occurrence.

        Args:
            content: The text content

        Returns:
            A list of topics, each represented as a dictionary mapping words to weights
        """
        try:
            # Split content into sentences
            sentences = content.split(".")

            # Initialize a CountVectorizer for word co-occurrence
            count_vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 1))

            # Fit the vectorizer
            X = count_vectorizer.fit_transform(sentences)

            # Get feature names
            feature_names = count_vectorizer.get_feature_names_out()

            # For simplicity, let's define topics based on the most common words in different parts of the text
            num_parts = min(self.max_topics, max(1, len(sentences) // 10))
            topics = []

            for i in range(num_parts):
                start_idx = i * len(sentences) // num_parts
                end_idx = (i + 1) * len(sentences) // num_parts

                part_sentences = sentences[start_idx:end_idx]
                part_text = " ".join(part_sentences)

                # Get word counts for this part
                word_counts = Counter(re.findall(r"\b\w+\b", part_text.lower()))

                # Remove stop words
                for word in self.stop_words:
                    if word in word_counts:
                        del word_counts[word]

                # Get the top 5 words for this topic
                top_words = word_counts.most_common(5)

                # Normalize weights
                total_count = sum(count for _, count in top_words) or 1
                topic = {word: count / total_count for word, count in top_words}

                if topic:
                    topics.append(topic)

            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []

    def _extract_entities(self, content: str) -> dict[str, list[str]]:
        """Extract named entities from the content.

        In a real implementation, this would use a NER model.
        For simplicity, we'll use regex patterns for common entities.

        Args:
            content: The text content

        Returns:
            A dictionary mapping entity types to lists of entities
        """
        entities: dict[str, list[str]] = {
            "email": [],
            "url": [],
            "date": [],
            "phone": [],
        }

        # Extract emails
        emails = set(self.email_pattern.findall(content))
        entities["email"] = list(emails)

        # Extract URLs
        urls = set(self.url_pattern.findall(content))
        entities["url"] = list(urls)

        # Extract dates
        dates = set(self.date_pattern.findall(content))
        entities["date"] = list(dates)

        # Extract phone numbers
        phones = set(self.phone_pattern.findall(content))
        entities["phone"] = list(phones)

        return entities

    def _generate_tags(
        self,
        keywords: list[str],
        topics: list[dict[str, float]],
        entities: dict[str, list[str]],
    ) -> list[str]:
        """Generate tags from the extracted information.

        Args:
            keywords: List of extracted keywords
            topics: List of extracted topics
            entities: Dictionary of extracted entities

        Returns:
            A list of generated tags
        """
        tags = set()

        # Add the top keywords
        for keyword in keywords[:5]:
            if len(keyword) >= self.min_keyword_length:
                tags.add(keyword)

        # Add top words from each topic
        for topic in topics:
            for word in list(topic.keys())[:2]:
                if len(word) >= self.min_keyword_length:
                    tags.add(word)

        # Add entity-based tags
        if entities.get("url"):
            tags.add("contains-urls")

        if entities.get("email"):
            tags.add("contains-emails")

        return list(tags)

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate a simple summary of the content.

        In a real implementation, this would use a more sophisticated
        summarization algorithm.

        Args:
            content: The text content
            max_length: Maximum length of the summary

        Returns:
            A summary of the content
        """
        # Simplistic approach: take the first few sentences
        sentences = content.split(".")
        summary_sentences = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if current_length + len(sentence) > max_length:
                break

            summary_sentences.append(sentence)
            current_length += len(sentence) + 1  # +1 for the period

        return ". ".join(summary_sentences) + ("." if summary_sentences else "")
