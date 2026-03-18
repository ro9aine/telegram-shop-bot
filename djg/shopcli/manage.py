import os
from pathlib import Path
import sys

from django.core.management import execute_from_command_line


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / "shop"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
    execute_from_command_line([sys.argv[0], *sys.argv[1:]])
