from __future__ import annotations

from models.analysis import ChangeType, CodeChangeClassification
from models.commit import Commit, FileChange
from prompts.code_change import build_code_change_prompt
from services.ollama_service import OllamaService

_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec"}
_TEST_STEM_SUFFIXES = ("_test", ".test", "_spec", ".spec")
_TEST_STEM_PREFIXES = ("test_",)
_DOC_MARKERS = (".md", ".rst", ".txt", "readme")
_CONFIG_DIR_NAMES = {"config", "configs", "settings"}
_DEPENDENCY_FILES = (
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pubspec.yaml",
    "pubspec.lock",
    "gemfile",
    "go.mod",
    "go.sum",
    "poetry.lock",
    "cargo.toml",
    "yarn.lock",
)
_CONFIG_EXTENSIONS = (".yml", ".yaml", ".ini", ".cfg", ".toml", ".env")

_MESSAGE_KEYWORDS: list[tuple[tuple[str, ...], ChangeType, float]] = [
    (("fix", "bug", "hotfix", "patch"), ChangeType.BUG_FIX, 0.6),
    (("feat", "add", "implement", "introduce"), ChangeType.NEW_FEATURE, 0.6),
    (("refactor", "cleanup", "restructure"), ChangeType.REFACTORING, 0.65),
    (("perf", "optimi", "speed up", "faster"), ChangeType.OPTIMIZATION, 0.65),
]


class CodeChangeService:
    """Module 3: classifies each changed file into a change-type category with a confidence score."""

    def __init__(self, ollama: OllamaService):
        self._ollama = ollama

    async def classify(self, commits: list[Commit]) -> list[CodeChangeClassification]:
        results: list[CodeChangeClassification] = []
        ambiguous: list[tuple[Commit, FileChange]] = []

        for commit in commits:
            for file in commit.files_changed:
                heuristic = self._heuristic_classify(file, commit.message)
                if heuristic is not None:
                    change_type, confidence, rationale = heuristic
                    results.append(
                        CodeChangeClassification(
                            file_path=file.path,
                            commit_hash=commit.commit_hash,
                            change_type=change_type,
                            confidence=confidence,
                            rationale=rationale,
                        )
                    )
                else:
                    ambiguous.append((commit, file))

        if ambiguous:
            results.extend(await self._ai_classify(ambiguous))

        return results

    @staticmethod
    def _heuristic_classify(file: FileChange, message: str) -> tuple[ChangeType, float, str] | None:
        path = file.path.lower()
        msg = message.lower()
        segments = path.split("/")
        filename = segments[-1]
        stem = filename.rsplit(".", 1)[0] if "." in filename else filename

        if any(segment in _TEST_DIR_NAMES for segment in segments[:-1]) or filename in _TEST_DIR_NAMES:
            return ChangeType.TESTING, 0.9, "File path indicates a test directory"
        if stem.startswith(_TEST_STEM_PREFIXES) or stem.endswith(_TEST_STEM_SUFFIXES):
            return ChangeType.TESTING, 0.9, "File name indicates a test file"
        if any(path.endswith(name) or path == name for name in _DEPENDENCY_FILES):
            return ChangeType.DEPENDENCY_UPDATE, 0.85, "Dependency manifest/lockfile changed"
        if any(marker in path for marker in _DOC_MARKERS) or "docs" in segments[:-1]:
            return ChangeType.DOCUMENTATION, 0.9, "Documentation file"
        if any(filename.endswith(ext) for ext in _CONFIG_EXTENSIONS) or any(
            segment in _CONFIG_DIR_NAMES for segment in segments[:-1]
        ):
            return ChangeType.CONFIGURATION, 0.75, "Configuration file"

        for keywords, change_type, confidence in _MESSAGE_KEYWORDS:
            if any(keyword in msg for keyword in keywords):
                return change_type, confidence, f"Commit message suggests: {change_type.value}"

        return None

    async def _ai_classify(
        self, items: list[tuple[Commit, FileChange]]
    ) -> list[CodeChangeClassification]:
        system, prompt = build_code_change_prompt(items)
        data = await self._ollama.generate_json(prompt, system=system)

        classifications: list[CodeChangeClassification] = []
        for entry in data.get("classifications", []):
            index = entry.get("index")
            if not isinstance(index, int) or not (0 <= index < len(items)):
                continue
            commit, file = items[index]
            change_type = self._parse_change_type(entry.get("change_type", ""))
            if change_type is None:
                continue
            confidence = float(entry.get("confidence", 0.5) or 0.5)
            classifications.append(
                CodeChangeClassification(
                    file_path=file.path,
                    commit_hash=commit.commit_hash,
                    change_type=change_type,
                    confidence=max(0.0, min(1.0, confidence)),
                    rationale=str(entry.get("rationale", "")).strip(),
                )
            )

        classified_indices = {
            i for i, (c, f) in enumerate(items) if any(cc.file_path == f.path and cc.commit_hash == c.commit_hash for cc in classifications)
        }
        for i, (commit, file) in enumerate(items):
            if i not in classified_indices:
                classifications.append(
                    CodeChangeClassification(
                        file_path=file.path,
                        commit_hash=commit.commit_hash,
                        change_type=ChangeType.REFACTORING,
                        confidence=0.3,
                        rationale="Fallback classification: model did not return a result",
                    )
                )

        return classifications

    @staticmethod
    def _parse_change_type(raw: str) -> ChangeType | None:
        raw = raw.strip().lower()
        for change_type in ChangeType:
            if change_type.value.lower() == raw:
                return change_type
        return None
