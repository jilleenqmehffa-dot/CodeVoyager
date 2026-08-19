import os
from pathlib import Path

from app.core.exceptions import InvalidLocalProjectError
from app.models.project_files import ProjectFile, ProjectFileCategory
from app.models.project_scans import ProjectScan
from app.models.projects import Project
from app.repositories.project_files import ProjectFileRepository
from app.repositories.project_scans import ProjectScanRepository
from app.schemas.project_scans import ProjectScanResult

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

LANGUAGES_BY_SUFFIX = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".go": "Go",
    ".h": "C",
    ".hpp": "C++",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".json": "JSON",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}

PROGRAMMING_LANGUAGES = {
    "C",
    "C#",
    "C++",
    "CSS",
    "Dart",
    "Elixir",
    "Go",
    "HTML",
    "Java",
    "JavaScript",
    "Kotlin",
    "PHP",
    "Python",
    "Ruby",
    "Rust",
    "Scala",
    "Shell",
    "SQL",
    "Swift",
    "TypeScript",
    "Vue",
}

DEPENDENCY_FILES = {
    "cargo.lock",
    "cargo.toml",
    "composer.json",
    "composer.lock",
    "gemfile",
    "gemfile.lock",
    "build.gradle",
    "build.gradle.kts",
    "go.mod",
    "go.sum",
    "package-lock.json",
    "package.json",
    "pipfile",
    "pipfile.lock",
    "pom.xml",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
}

CONFIG_FILES = {
    ".editorconfig",
    ".env",
    ".env.example",
    ".gitignore",
    "eslint.config.js",
    "jsconfig.json",
    "mypy.ini",
    "pytest.ini",
    "ruff.toml",
    "tsconfig.json",
}

TEST_DIRECTORIES = {"test", "tests", "spec", "specs", "__tests__"}
DOCS_DIRECTORIES = {"doc", "docs", "documentation"}
SOURCE_DIRECTORIES = {"app", "backend", "frontend", "lib", "src"}

ENTRYPOINT_NAMES = {
    "__main__.py",
    "app.py",
    "index.js",
    "index.jsx",
    "index.ts",
    "index.tsx",
    "main.go",
    "main.js",
    "main.jsx",
    "main.py",
    "main.rs",
    "main.ts",
    "main.tsx",
    "manage.py",
    "server.js",
    "server.ts",
}

FRAMEWORK_MARKERS = {
    "Angular": ("@angular/core",),
    "Django": ("django",),
    "Express": ('"express"',),
    "FastAPI": ("fastapi",),
    "Flask": ("flask",),
    "Next.js": ('"next"',),
    "React": ('"react"',),
    "Spring": ("spring-boot", "org.springframework"),
    "Vue": ('"vue"',),
}


def scan_project(project: Project) -> ProjectScanResult:
    """Scan a project's filesystem and return deterministic structured facts."""

    root = project.local_path.expanduser().resolve()
    if not root.is_dir():
        raise InvalidLocalProjectError(
            f"Local project path is not a directory: {root}"
        )

    files: list[ProjectFile] = []
    languages: set[str] = set()
    frameworks: set[str] = set()
    entrypoints: list[str] = []

    for current_root, directory_names, file_names in os.walk(root, topdown=True):
        directory_names[:] = sorted(
            name for name in directory_names if not should_ignore(name)
        )
        current_path = Path(current_root)

        for directory_name in directory_names:
            directory_path = current_path / directory_name
            relative_path = directory_path.relative_to(root).as_posix()
            files.append(
                ProjectFile(
                    project_id=project.id,
                    path=relative_path,
                    name=directory_name,
                    category=detect_category(relative_path, is_directory=True),
                    is_directory=True,
                )
            )

        for file_name in sorted(file_names):
            file_path = current_path / file_name
            relative_path = file_path.relative_to(root).as_posix()
            file_type = file_path.suffix.lower() or None
            language = detect_language(file_path)
            category = detect_category(relative_path, is_directory=False)
            files.append(
                ProjectFile(
                    project_id=project.id,
                    path=relative_path,
                    name=file_name,
                    file_type=file_type,
                    language=language,
                    category=category,
                    is_directory=False,
                )
            )

            if language in PROGRAMMING_LANGUAGES:
                languages.add(language)
            if _is_entrypoint(file_name, category):
                entrypoints.append(relative_path)
            if category == "dependency":
                frameworks.update(_detect_frameworks(file_path))

    scan = ProjectScan(
        project_id=project.id,
        languages=sorted(languages),
        frameworks=sorted(frameworks),
        entrypoints=sorted(entrypoints),
    )
    return ProjectScanResult(scan=scan, files=files)


def scan_and_save_project(
    project: Project,
    scan_repository: ProjectScanRepository,
    file_repository: ProjectFileRepository,
) -> ProjectScanResult:
    """Scan a project and replace its previously persisted scan result."""

    result = scan_project(project)
    scan_repository.save(result.scan)
    file_repository.save_many(project.id, result.files)
    return result


def should_ignore(directory_name: str) -> bool:
    return directory_name.lower() in IGNORED_DIRECTORIES


def detect_language(path: Path) -> str | None:
    return LANGUAGES_BY_SUFFIX.get(path.suffix.lower())


def detect_category(path: str, *, is_directory: bool) -> ProjectFileCategory:
    relative_path = Path(path)
    name = relative_path.name.lower()
    parts = {part.lower() for part in relative_path.parts}

    if is_directory:
        if parts & TEST_DIRECTORIES:
            return "test"
        if parts & DOCS_DIRECTORIES:
            return "docs"
        if parts & SOURCE_DIRECTORIES:
            return "source"
        return "other"

    if name == "readme" or name.startswith("readme."):
        return "readme"
    if name == "dockerfile" or name.startswith("dockerfile."):
        return "dockerfile"
    if _is_compose_file(name):
        return "compose"
    if name in DEPENDENCY_FILES or name.startswith("requirements-"):
        return "dependency"
    if parts & TEST_DIRECTORIES or _is_test_file(name):
        return "test"
    if parts & DOCS_DIRECTORIES:
        return "docs"
    if _is_config_file(name):
        return "config"
    if detect_language(relative_path) in PROGRAMMING_LANGUAGES:
        return "source"
    return "other"


def _is_compose_file(name: str) -> bool:
    return name in {
        "compose.yaml",
        "compose.yml",
        "docker-compose.yaml",
        "docker-compose.yml",
    }


def _is_test_file(name: str) -> bool:
    path = Path(name)
    return (
        name.startswith("test_")
        or path.stem.endswith("_test")
        or ".spec." in name
        or ".test." in name
    )


def _is_config_file(name: str) -> bool:
    return (
        name in CONFIG_FILES
        or ".config." in name
        or name.startswith("config.")
        or name.startswith("settings.")
    )


def _is_entrypoint(
    file_name: str,
    category: ProjectFileCategory,
) -> bool:
    return category == "source" and file_name.lower() in ENTRYPOINT_NAMES


def _detect_frameworks(path: Path) -> set[str]:
    try:
        if path.stat().st_size > 1_000_000:
            return set()
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return set()

    return {
        framework
        for framework, markers in FRAMEWORK_MARKERS.items()
        if any(marker in content for marker in markers)
    }
