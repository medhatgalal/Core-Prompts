import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_things3_bridge_node_suite():
    result = subprocess.run(["node", "--test", str(ROOT / "tests" / "gtd" / "things.test.js")],
                            capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
