```
# **The Aichemist Codex**

## **Overview**
The Aichemist Codex is an automated project analysis and organization tool designed to:

- Generate file tree structures dynamically.
- Summarize functions, classes, and code structure.
- Convert outputs into structured Markdown or JSON formats.
- Assist with AI-driven file organization.

---

## **Installation**

### **Prerequisites**
Ensure you have the following installed:

- **Python 3.12.3** or higher
- **pip** package manager

### **Clone the Repository**
```sh
git clone https://github.com/savagelysubtle/the_aichemist_codex.git
cd the_aichemist_codex
```

### **Setup Virtual Environment (Recommended)**

```sh
python -m venv venv
source venv/bin/activate  # MacOS/Linux
venv\Scripts\activate     # Windows
```

### **Install Dependencies**

```sh
pip install -r requirements.txt
```

---

## **Usage**

### **Generate a File Tree**

```sh
python src/project_reader/main.py --tree path/to/project
```

### **Summarize Codebase**

```sh
python src/project_reader/main.py --code path/to/project
```

### **Run GUI for Directory Selection**

```sh
python scripts/run_analysis.py --gui
```

### **Batch File Management**

```sh
python src/file_manager/file_manager.py path/to/move_files.json
```

---

## **Project Structure**

```plaintext
the_aichemist_codex/
│── src/
│   ├── common/              # Shared utilities and config
│   ├── file_manager/        # Handles file organization
│   ├── project_reader/      # Code parsing and tree generation
│── templates/               # Sample project structures
│── docs/                    # Documentation
│── tests/                   # Unit tests
│── scripts/                 # Standalone execution scripts
│── pyproject.toml           # Project metadata
│── requirements.txt         # Dependencies
```

---

## **Configuration**

Modify `src/common/config.py` for custom settings such as:

- Output directory locations.
- Logging configurations.
- File management rules.

---

## **Logging**

Logs are saved in `data/logs/`, managed via `src/common/logging_config.py`.

---

## **Contributing**

Follow these steps to contribute:

1. Fork the repository.
2. Create a feature branch:

   ```sh
   git checkout -b feature-name
   ```

3. Commit your changes:

   ```sh
   git commit -m "Add new feature"
   ```

4. Push to your branch:

   ```sh
   git push origin feature-name
   ```

5. Open a pull request.

---

## **License**

This project is licensed under the **MIT License**.

```

