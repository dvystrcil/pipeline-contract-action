"""TDD test suite for check_pipeline_contract.py.

Each test runs the contract checker against a fixture and asserts the expected
exit code + that the expected error keyword appears in stderr. Fixtures live
under tests/fixtures/.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CHECK = ROOT / "check_pipeline_contract.py"
FIXTURES = HERE / "fixtures"


def run_check(*paths: Path) -> tuple[int, str, str]:
    """Invoke the checker on the given fixture paths. Returns (rc, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(CHECK), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_ACTIONS": ""},
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_good_pipeline_passes() -> None:
    rc, out, err = run_check(FIXTURES / "good_pipeline.py")
    assert rc == 0, f"expected clean exit, got rc={rc}\nstdout: {out}\nstderr: {err}"


def test_bad_sync_inlet_fails_ac2() -> None:
    rc, out, err = run_check(FIXTURES / "bad_sync_inlet.py")
    assert rc != 0, "expected non-zero exit"
    combined = (out + err).lower()
    assert "inlet" in combined, f"error should mention 'inlet': {combined}"
    assert "async" in combined, f"error should mention 'async': {combined}"


def test_bad_sync_lifecycle_fails_ac3() -> None:
    rc, out, err = run_check(FIXTURES / "bad_sync_lifecycle.py")
    assert rc != 0
    combined = (out + err).lower()
    assert "on_startup" in combined
    assert "async" in combined


def test_bad_missing_pipelines_field_fails_ac4() -> None:
    rc, out, err = run_check(FIXTURES / "bad_missing_pipelines_field.py")
    assert rc != 0
    combined = (out + err).lower()
    assert "pipelines" in combined
    assert "valves" in combined


def test_bad_missing_instance_attrs_fails_ac5() -> None:
    rc, out, err = run_check(FIXTURES / "bad_missing_instance_attrs.py")
    assert rc != 0
    combined = (out + err).lower()
    # At least one of the required attrs should be flagged
    assert any(attr in combined for attr in ("self.type", "self.name", "self.valves"))


def test_multiple_files_aggregate() -> None:
    """Two files, one good one bad — overall rc should be non-zero, both reported."""
    rc, out, err = run_check(
        FIXTURES / "good_pipeline.py",
        FIXTURES / "bad_sync_inlet.py",
    )
    assert rc != 0


def test_no_files_clean() -> None:
    """No file args — should exit 0 with a 'no files' message."""
    rc, out, err = run_check()
    assert rc == 0


if __name__ == "__main__":
    # When invoked directly, just run the tests in declaration order.
    import inspect

    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
                fails += 1
    sys.exit(0 if fails == 0 else 1)
