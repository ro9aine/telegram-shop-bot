from watchfiles import run_process


def _run_bot() -> None:
    from app.main import run

    run()


def run() -> None:
    run_process(
        ".",
        target=_run_bot,
        watch_filter=None,
    )


if __name__ == "__main__":
    run()
