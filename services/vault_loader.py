import base64
import logging
from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO

logger = logging.getLogger(__name__)

INCLUDE_PATHS = [
    "10_Projects/Lemana Pro",
    "10_Projects/Pet_Projects",
    "99_Ideas",
    "Lemana_Pro_Project",
]

SKIP_PATHS = [
    "20_Research",
    "10_Projects/Yandex_Practicum",
    "Claude_Code",
    "80_Templates",
    ".obsidian",
]

MAX_CHARS = 20_000


def _should_include(path: str) -> bool:
    for skip in SKIP_PATHS:
        if path.startswith(skip):
            return False
    for include in INCLUDE_PATHS:
        if path.startswith(include):
            return True
    return False


def _fetch_all_md(repo, path: str = "") -> list[tuple[str, str]]:
    results = []
    try:
        items = repo.get_contents(path)
    except Exception as e:
        logger.warning(f"Cannot fetch {path}: {e}")
        return results

    for item in items:
        if item.type == "dir":
            if not any(item.path.startswith(s) for s in SKIP_PATHS):
                results.extend(_fetch_all_md(repo, item.path))
        elif item.name.endswith(".md") and item.name != ".gitkeep":
            if _should_include(item.path):
                try:
                    content = base64.b64decode(item.content).decode("utf-8", errors="ignore")
                    results.append((item.path, content[:3000]))
                except Exception as e:
                    logger.warning(f"Cannot decode {item.path}: {e}")
    return results


def load_vault_context() -> str:
    logger.info("Loading Obsidian vault context from GitHub...")
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    files = _fetch_all_md(repo)
    logger.info(f"Loaded {len(files)} .md files from vault")

    parts = []
    total_chars = 0

    for path, content in files:
        block = f"\n\n---\n### [{path}]\n{content.strip()}"
        if total_chars + len(block) > MAX_CHARS:
            logger.info(f"Context limit reached at {len(parts)} files")
            break
        parts.append(block)
        total_chars += len(block)

    logger.info(f"Vault context: {total_chars} chars from {len(parts)} files")
    return "".join(parts)
