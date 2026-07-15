"""Architecture contract tests — structural rules enforced as tests, not convention.

N2 (PRD): no AGPL code (PyMuPDF/fitz, Ghostscript wrapper, anything under
infrastructure/agpl) may be importable — even transitively — from the served
surfaces (HTTP API, MCP server). One breach shipped before this test existed
(REVIEW.md P0); it must not recur.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

# Top-level imports so gazelle wires the served surfaces (and their trees) into this
# test's bazel deps/runfiles. The N2 check itself runs in a FRESH subprocess, so
# importing them here does not contaminate the assertion.
import pdf_toolkit.api.app  # noqa: F401
import pdf_toolkit.mcp_server.server  # noqa: F401

_CHECK = """
import sys
import pdf_toolkit.api.app          # noqa: F401
import pdf_toolkit.mcp_server.server  # noqa: F401

# Trigger every lazy import reachable from served entrypoints: call the module-level
# import blocks by importing the modules they defer to at top level here would defeat
# the test, so instead assert on what the surfaces actually pulled in.
bad = sorted(
    m for m in sys.modules
    if m == "fitz" or m.startswith("fitz.") or ".infrastructure.agpl" in m
)
if bad:
    print("AGPL modules reachable from served surfaces: " + ", ".join(bad))
    sys.exit(1)
print("clean")
"""


def test_n2_no_agpl_importable_from_served_surfaces():
    """Fresh interpreter: import API + MCP, assert no fitz/agpl module loaded."""
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))  # hermetic (bazel) safe
    proc = subprocess.run(
        [sys.executable, "-c", _CHECK], capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "clean" in proc.stdout


def test_n2_lazy_served_imports_are_also_clean():
    """The served surfaces defer some imports into function bodies; grep those too."""
    from pathlib import Path

    for served in ("pdf_toolkit.api.app", "pdf_toolkit.mcp_server.server"):
        spec = importlib.util.find_spec(served)
        assert spec is not None and spec.origin is not None
        text = Path(spec.origin).read_text()
        assert "agpl" not in text, f"{served} references the AGPL quarantine package"
        assert "import fitz" not in text, f"{served} imports fitz directly"


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
