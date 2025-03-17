"""
Tag classification module for automatic file tagging.

This module provides the TagClassifier class, which is responsible for
training and applying machine learning models to automatically tag files
based on their content and metadata.
"""

import json
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata

logger = logging.getLogger(__name__)


class TagClassifier:
    """
    Machine learning classifier for automatic file tagging.

    This class provides methods for training and applying machine learning
    models to automatically tag files based on their content and metadata.
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, model_dir: Path):
        """
        Initialize the TagClassifier with a model directory.

        Args:
            model_dir: Directory to store model files
        """
        self.model_dir = model_dir
        self.model_path = self.model_dir / "tag_classifier.pkl"
        self.metadata_path = self.model_dir / "tag_classifier_metadata.json"

        self.pipeline: Pipeline | None = None
        self.mlb: MultiLabelBinarizer | None = None
        self.feature_names: np.ndarray | None = None
        self.tag_names: list[str] = []
        self.training_metadata: dict[str, Any] = {}

        # Initialize the default model
        self._initialize_default_model()

    def _initialize_default_model(self) -> None:
        """Initialize the default model pipeline."""
        # Create a basic pipeline with TF-IDF and SVM
        self.pipeline = Pipeline(
            [
                ("vectorizer", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
                (
                    "classifier",
                    MultiOutputClassifier(
                        LinearSVC(C=1.0, class_weight="balanced", max_iter=10000)
                    ),
                ),
            ]
        )

        # Initialize MultiLabelBinarizer for tag encoding
        self.mlb = MultiLabelBinarizer()

        # Initialize empty tag set
        self.tag_names = []

    async def load_model(self) -> bool:
        """
        Load a trained model from disk.

        Returns:
            bool: True if a model was loaded, False otherwise
        """
        try:
            # Ensure model directory exists
            self.model_dir.mkdir(parents=True, exist_ok=True)

            # Check if model file exists
            if not self.model_path.exists():
                logger.info("No trained model found, using default model")
                return False

            # Load the model
            with open(self.model_path, "rb") as f:
                model_data = pickle.load(f)
                self.pipeline = model_data["pipeline"]
                self.mlb = model_data["mlb"]
                self.feature_names = model_data.get("feature_names")
                self.tag_names = model_data.get("tag_names", [])

            # Load metadata if available
            if self.metadata_path.exists():
                with open(self.metadata_path) as f:
                    self.training_metadata = json.load(f)

            logger.info(f"Loaded tag classifier model with {len(self.tag_names)} tags")
            return True

        except Exception as e:
            logger.error(f"Failed to load tag classifier model: {e}")
            self._initialize_default_model()
            return False

    async def save_model(self) -> bool:
        """
        Save the current model to disk.

        Returns:
            bool: True if the model was saved successfully, False otherwise
        """
        try:
            # Ensure model directory exists
            os.makedirs(self.model_dir, exist_ok=True)

            # Save the model
            model_data = {
                "pipeline": self.pipeline,
                "mlb": self.mlb,
                "feature_names": self.feature_names,
            }

            with open(self.model_path, "wb") as f:
                pickle.dump(model_data, f)

            # Update training metadata
            self.training_metadata.update(
                {
                    "last_updated": datetime.now().isoformat(),
                    "tag_names": self.tag_names,
                    "num_tags": len(self.tag_names),
                }
            )

            # Save metadata
            with open(self.metadata_path, "w") as f:
                json.dump(self.training_metadata, f, indent=2)

            logger.info(f"Saved tag classifier model with {len(self.tag_names)} tags")
            return True

        except Exception as e:
            logger.error(f"Error saving tag classifier model: {e}")
            return False

    def _extract_features(self, file_metadata: FileMetadata) -> str:
        """
        Extract features from file metadata for classification.

        Args:
            file_metadata: FileMetadata object

        Returns:
            str: Text features extracted from metadata
        """
        features = []

        # Add filename and extension
        if file_metadata.path:
            path = Path(file_metadata.path)
            features.append(path.name)
            if path.suffix:
                features.append(path.suffix.lstrip("."))

        # Add MIME type
        if file_metadata.mime_type:
            features.append(file_metadata.mime_type)

        # Add extracted content
        if file_metadata.preview:
            features.append(file_metadata.preview[:5000])  # Limit preview size

        # Add topics if available
        if hasattr(file_metadata, "topics") and file_metadata.topics:
            for topic_dict in file_metadata.topics:
                for topic, score in topic_dict.items():
                    features.append(f"topic:{topic}")

        # Add keywords if available
        if hasattr(file_metadata, "keywords") and file_metadata.keywords:
            for keyword in file_metadata.keywords:
                features.append(f"keyword:{keyword}")

        # Add entities if available
        if hasattr(file_metadata, "entities") and file_metadata.entities:
            for entity_type, entities in file_metadata.entities.items():
                for entity in entities:
                    features.append(f"entity:{entity_type}:{entity}")

        # Add language if available
        if hasattr(file_metadata, "language") and file_metadata.language:
            features.append(f"lang:{file_metadata.language}")

        # Add content type if available
        if hasattr(file_metadata, "content_type") and file_metadata.content_type:
            features.append(f"content_type:{file_metadata.content_type}")

        # Join all features
        return " ".join(str(feature) for feature in features if feature)

    def _get_tag_scores(self, file_metadata: FileMetadata) -> list[tuple[str, float]]:
        """
        Get confidence scores for all tags for a file.

        Args:
            file_metadata: File metadata

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        if not self.pipeline or not self.mlb or not self.tag_names:
            logger.warning("Model not initialized, cannot get tag scores")
            return []

        # Pipeline must not be None at this point
        pipeline = self.pipeline
        if pipeline is None:  # This is for type checking only
            return []

        try:
            # Extract features
            features = self._extract_features(file_metadata)
            if not features:
                logger.warning(f"No features extracted from file: {file_metadata.path}")
                return []

            # Convert to vector
            X = [features]

            # Get classifier from pipeline
            classifier = pipeline.named_steps["classifier"]

            # Transform text to TF-IDF
            X_tfidf = pipeline.named_steps["vectorizer"].transform(X)

            # For each classifier, get decision function scores
            tag_scores = []

            for i, estimator in enumerate(classifier.estimators_):
                if i < len(self.tag_names):
                    if hasattr(estimator, "decision_function"):
                        # Get decision score
                        score = estimator.decision_function(X_tfidf)[0]

                        # Convert to probability-like score (0-1)
                        # Using sigmoid function: 1 / (1 + exp(-x))
                        confidence = 1 / (1 + np.exp(-score))

                        tag_scores.append((self.tag_names[i], float(confidence)))
                    else:
                        # If no decision function, use predict_proba
                        proba = estimator.predict_proba(X_tfidf)[0][1]
                        tag_scores.append((self.tag_names[i], float(proba)))

            # Sort by confidence
            tag_scores.sort(key=lambda x: x[1], reverse=True)
            return tag_scores

        except Exception as e:
            logger.error(f"Error getting tag scores: {e}")
            return []

    async def classify(
        self,
        file_metadata: FileMetadata,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> list[tuple[str, float]]:
        """
        Classify a file and suggest tags with confidence scores.

        Args:
            file_metadata: FileMetadata object
            confidence_threshold: Minimum confidence threshold for tag suggestions

        Returns:
            List[Tuple[str, float]]: List of (tag_name, confidence) tuples
        """
        # Check if model is loaded
        if self.pipeline is None or self.mlb is None or not self.tag_names:
            await self.load_model()
            if not self.tag_names:
                logger.warning("No tags available for classification")
                return []

        # At this point, ensure pipeline is not None
        pipeline = self.pipeline
        if pipeline is None:  # This is for type checking only
            return []

        try:
            # Extract features
            features = self._extract_features(file_metadata)
            if not features:
                logger.warning(f"No features extracted from file: {file_metadata.path}")
                return []

            # Convert to vector
            X = [features]

            # Get classifier from pipeline
            classifier = pipeline.named_steps["classifier"]

            # Transform text to TF-IDF
            X_tfidf = pipeline.named_steps["vectorizer"].transform(X)

            # For each classifier, get decision function scores
            tag_scores = []

            for i, estimator in enumerate(classifier.estimators_):
                if i < len(self.tag_names):
                    if hasattr(estimator, "decision_function"):
                        # Get decision score
                        score = estimator.decision_function(X_tfidf)[0]

                        # Convert to probability-like confidence (sigmoid)
                        confidence = 1 / (1 + np.exp(-score))

                        if confidence >= confidence_threshold:
                            tag_scores.append((self.tag_names[i], float(confidence)))

            # Sort by confidence
            tag_scores.sort(key=lambda x: x[1], reverse=True)

            return tag_scores

        except Exception as e:
            logger.error(f"Error classifying file {file_metadata.path}: {e}")
            return []

    async def train(
        self,
        training_data: list[tuple[FileMetadata, list[str]]],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """
        Train the classifier with labeled examples.

        Args:
            training_data: List of (file_metadata, tags) tuples
            test_size: Portion of data to use for testing
            random_state: Random seed for reproducibility

        Returns:
            Dict[str, Any]: Training results with metrics

        Raises:
            ValueError: If training data is empty
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")

        # Initialize components if needed
        if self.pipeline is None:
            self._initialize_default_model()

        if self.mlb is None:
            self.mlb = MultiLabelBinarizer()

        # Ensure we have valid pipeline and mlb objects
        pipeline = self.pipeline
        mlb = self.mlb
        if pipeline is None or mlb is None:
            logger.error("Failed to initialize model components")
            raise RuntimeError("Model components could not be initialized")

        try:
            # Extract features and labels
            X = []
            y = []

            for metadata, tags in training_data:
                features = self._extract_features(metadata)
                if features:
                    X.append(features)
                    y.append(tags)

            if not X or not y:
                raise ValueError(
                    "No valid features or tags extracted from training data"
                )

            # Fit the binarizer on all tags
            y_bin = mlb.fit_transform(y)
            self.tag_names = list(mlb.classes_)

            # Split data into train and test sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_bin, test_size=test_size, random_state=random_state
            )

            # Train the model
            pipeline.fit(X_train, y_train)

            # Get feature names for introspection
            self.feature_names = pipeline.named_steps[
                "vectorizer"
            ].get_feature_names_out()

            # Evaluate on test set
            accuracy = pipeline.score(X_test, y_test)

            # Record training metadata
            self.training_metadata = {
                "num_samples": len(X),
                "num_tags": len(self.tag_names),
                "tag_names": self.tag_names,
                "accuracy": accuracy,
                "training_date": datetime.now().isoformat(),
                "test_size": test_size,
            }

            # Save the model
            await self.save_model()

            logger.info(
                f"Trained tag classifier on {len(X)} samples with {len(self.tag_names)} tags. Accuracy: {accuracy:.4f}"
            )

            return self.training_metadata

        except Exception as e:
            logger.error(f"Error training tag classifier: {e}")
            raise

    async def get_tag_features(
        self, tag_name: str, top_n: int = 10
    ) -> list[tuple[str, float]]:
        """
        Get the most important features for a tag.

        Args:
            tag_name: Name of the tag
            top_n: Number of top features to return

        Returns:
            List[Tuple[str, float]]: List of (feature, importance) tuples
        """
        if not self.pipeline or not self.mlb or not self.feature_names:
            await self.load_model()
            if not self.tag_names or not self.feature_names:
                return []

        # Make sure pipeline and feature_names are not None
        pipeline = self.pipeline
        feature_names = self.feature_names
        if pipeline is None or feature_names is None:
            logger.warning("Pipeline or feature_names not available")
            return []

        try:
            # Get tag index
            if tag_name not in self.tag_names:
                return []

            tag_idx = self.tag_names.index(tag_name)

            # Get coefficients for the tag
            classifier = pipeline.named_steps["classifier"]
            if tag_idx >= len(classifier.estimators_):
                return []

            estimator = classifier.estimators_[tag_idx]
            coefficients = estimator.coef_[0]

            # Pair features with coefficients
            feature_importance = [
                (feature, coef)
                for feature, coef in zip(feature_names, coefficients, strict=False)
            ]

            # Sort by absolute importance
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

            # Return top features
            return feature_importance[:top_n]

        except Exception as e:
            logger.error(f"Error finding important features for {tag_name}: {e}")
            return []

    async def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict[str, Any]: Model information and metadata
        """
        # Try to load the model if not loaded
        if not self.training_metadata:
            await self.load_model()

        return {
            **self.training_metadata,
            "model_path": str(self.model_path),
            "is_loaded": self.pipeline is not None and self.mlb is not None,
            "num_features": (
                len(self.feature_names) if self.feature_names is not None else 0
            ),
        }

    async def get_similar_tags(
        self, tag_name: str, top_n: int = 5
    ) -> list[tuple[str, float]]:
        """
        Find tags that are similar to the given tag based on model coefficients.

        Args:
            tag_name: Tag name
            top_n: Number of similar tags to return

        Returns:
            List[Tuple[str, float]]: List of (tag_name, similarity) tuples
        """
        if not self.pipeline or not self.mlb or not self.tag_names:
            await self.load_model()
            if not self.tag_names:
                return []

        # Ensure pipeline is not None
        pipeline = self.pipeline
        if pipeline is None:
            logger.warning("Pipeline not available")
            return []

        try:
            # Get tag index
            if tag_name not in self.tag_names:
                return []

            tag_idx = self.tag_names.index(tag_name)

            # Get coefficients for the tag
            classifier = pipeline.named_steps["classifier"]
            if tag_idx >= len(classifier.estimators_):
                return []

            reference_estimator = classifier.estimators_[tag_idx]
            reference_coefficients = reference_estimator.coef_[0]

            # Calculate cosine similarity with all other tags
            similarities = []

            for i, estimator in enumerate(classifier.estimators_):
                if i != tag_idx and i < len(self.tag_names):
                    coefficients = estimator.coef_[0]

                    # Calculate cosine similarity
                    dot_product = np.dot(reference_coefficients, coefficients)
                    norm_product = np.linalg.norm(
                        reference_coefficients
                    ) * np.linalg.norm(coefficients)
                    similarity = dot_product / norm_product if norm_product != 0 else 0

                    similarities.append((self.tag_names[i], float(similarity)))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            return similarities[:top_n]

        except Exception as e:
            logger.error(f"Error finding similar tags for {tag_name}: {e}")
            return []

    async def train_model(
        self,
        training_data: list[tuple[FileMetadata, list[str]]],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """
        Train the tag classifier on a dataset of file metadata and tags.

        Args:
            training_data: List of (file_metadata, tags) tuples
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility

        Returns:
            Dict[str, Any]: Training results and metrics

        Raises:
            ValueError: If training data is insufficient
        """
        if not training_data:
            raise ValueError("No training data provided")

        # Initialize components if not already done
        if self.pipeline is None:
            self._initialize_default_model()

        if self.mlb is None:
            self.mlb = MultiLabelBinarizer()

        # Ensure we have valid pipeline and mlb objects
        assert self.pipeline is not None, "Pipeline not initialized"
        assert self.mlb is not None, "MultiLabelBinarizer not initialized"

        try:
            # Extract features and labels
            X = []
            y = []

            for metadata, tags in training_data:
                features = self._extract_features(metadata)
                if features:
                    X.append(features)
                    y.append(tags)

            if not X or not y:
                raise ValueError(
                    "No valid features or tags extracted from training data"
                )

            # Fit the binarizer on all tags
            y_bin = self.mlb.fit_transform(y)
            self.tag_names = list(self.mlb.classes_)

            # Split data into train and test sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_bin, test_size=test_size, random_state=random_state
            )

            # Train the model
            self.pipeline.fit(X_train, y_train)

            # Get feature names for introspection
            self.feature_names = self.pipeline.named_steps[
                "vectorizer"
            ].get_feature_names_out()

            # Evaluate on test set
            accuracy = self.pipeline.score(X_test, y_test)

            # Record training metadata
            self.training_metadata = {
                "num_samples": len(X),
                "num_tags": len(self.tag_names),
                "tag_names": self.tag_names,
                "accuracy": accuracy,
                "trained_at": datetime.now().isoformat(),
            }

            # Save the model
            await self.save_model()

            logger.info(
                f"Trained tag classifier on {len(X)} samples with {len(self.tag_names)} tags. Accuracy: {accuracy:.4f}"
            )

            return self.training_metadata

        except Exception as e:
            logger.error(f"Error training tag classifier: {e}")
            raise
