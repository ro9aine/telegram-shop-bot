from pathlib import Path

from watchfiles import run_process

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IGNORED_PREFIXES = (
    PROJECT_ROOT / "logs",
    PROJECT_ROOT / "__pycache__",
    PROJECT_ROOT / ".pytest_cache",
)


def _watch_filter(_: object, changed_path: str) -> bool:
    path = Path(changed_path).resolve()
    for prefix in IGNORED_PREFIXES:
        resolved_prefix = prefix.resolve()
        if path == resolved_prefix or resolved_prefix in path.parents:
            return False
    return True


def _run_bot() -> None:
    from app.main import run

    run()


def run() -> None:
    run_process(
        ".",
        target=_run_bot,
        watch_filter=_watch_filter,
    )


if __name__ == "__main__":
    run()
