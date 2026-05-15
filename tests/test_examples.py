from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_user_example_smoke() -> None:
    example = Path(__file__).parents[1] / "examples" / "user.py"

    result = subprocess.run(
        [sys.executable, str(example)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "example smoke passed" in result.stdout
