# Plan for Enhancing the Extraction Module

Based on the detailed review, the following steps should be taken to improve the `infrastructure/extraction` module:

1.  **Refactor Caching Strategy (`manager.py`, `base_extractor.py`, `code.py`, `documents.py`):**
    *   **Goal:** Eliminate redundant caching and centralize cache management using the `CacheManager` interface.
    *   **Action:** Modify `MetadataManager.extract_metadata` to handle all caching checks *before* calling the extractor's `extract` method. Use `self.cache_manager.get()` and `self.cache_manager.put()`.
    *   **Action:** Define a consistent cache key structure in `MetadataManager` (e.g., including file path, mtime, extractor type).
    *   **Action:** Remove caching logic (`self.cache_manager.get`/`put`) from the `extract` methods within `CodeMetadataExtractor` and `DocumentMetadataExtractor`. Ensure they still receive the `cache_manager` instance if needed for other purposes (though likely not after this refactor).
    *   **Verify:** Test caching behavior to ensure hits and misses occur as expected and only one layer of caching is active for metadata results.

2.  **Improve Type Safety (`code.py`, `documents.py`, `base_extractor.py`):**
    *   **Goal:** Enhance type checking and clarity of return types.
    *   **Action:** Remove the `# type: ignore` comments from the `extract` method signatures in `CodeMetadataExtractor` and `DocumentMetadataExtractor`.
    *   **Action:** Run `mypy` to confirm no type errors are present after removing the ignores.
    *   **Action:** Define `TypedDict` classes (e.g., `CodeMetadataDict`, `DocumentMetadataDict`) for the return values of the `extract` methods in `code.py` and `documents.py`.
    *   **Action:** Update the return type hints for the `extract` methods in `base_extractor.py`, `code.py`, and `documents.py` to use the new `TypedDict`s instead of `dict[str, Any]`.
    *   **Action:** Update relevant docstrings (`:return:`) to reflect the new `TypedDict` return types.

3.  **Enhance Error Handling (Across Module):**
    *   **Goal:** Make error handling more specific and informative.
    *   **Action:** Review `try...except Exception` blocks in `base_extractor.py` (`_get_content`), `manager.py` (`extract_metadata`, creating `FileMetadata`), `tagging/classifier.py` (`load_model`, `save_model`, `classify`, `train`, `get_tag_features`, `get_similar_tags`), and `tagging/manager.py` (most methods).
    *   **Action:** Replace generic `Exception` catches with more specific ones where appropriate (e.g., `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`, `sqlite3.Error` subclasses, `pickle.UnpicklingError`, `ValueError`).
    *   **Action:** Ensure a fallback `except Exception` remains for unexpected errors, logging them thoroughly.
    *   **Action:** Update `:raises:` sections in docstrings to reflect the specific exceptions callers might need to handle.

4.  **Centralize Configuration:**
    *   **Goal:** Move hardcoded configuration values to the central `infrastructure.config` system.
    *   **Action:** Identify hardcoded values suitable for configuration (e.g., `TagClassifier.DEFAULT_CONFIDENCE_THRESHOLD`, default `max_concurrent` in `MetadataManager.extract_batch`, potentially regex patterns if configurable).
    *   **Action:** Define corresponding settings in `infrastructure/config/settings.py` (or appropriate location).
    *   **Action:** Modify the `__init__` methods of relevant classes (`TagClassifier`, `MetadataManager`) to accept these values as arguments.
    *   **Action:** Update the instantiation points of these classes (likely higher up in the application structure, outside this module) to read values from the config and inject them. (This step might be outside the scope of modifying *only* the extraction module).

5.  **Review and Update Docstrings (Across Module):**
    *   **Goal:** Ensure all docstrings are accurate, complete, consistent, and clear.
    *   **Action:** Perform a pass over all modules, classes, and public methods within `extraction` and `extraction/tagging`.
    *   **Action:** Verify `:param:`, `:return:`, and especially `:raises:` sections are accurate and detailed.
    *   **Action:** Ensure consistency in style (Google for classes/modules, Numpy for functions/methods).
    *   **Action:** Add missing docstrings (e.g., `TagClassifier._initialize_default_model`).
    *   **Action:** Improve clarity and descriptiveness where needed.
