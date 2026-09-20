from __future__ import annotations

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    ROOT / "notebooks" / "01_from_sky_to_galactic_phase_space.ipynb",
    ROOT / "notebooks" / "02_reading_the_disturbed_anticentre.ipynb",
    ROOT / "notebooks" / "03_from_spiral_winding_to_a_galactic_clock.ipynb",
]


@pytest.mark.parametrize("notebook_path", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_executes_in_fresh_kernel(notebook_path: Path) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    expected_stage = "task-3-complete" if notebook_path.name.startswith("01_") else "task-1-shell"
    assert notebook.metadata["lambert_lab"]["stage"] == expected_stage
    client = NotebookClient(
        notebook,
        timeout=60,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    executed = client.execute()
    assert any(cell.cell_type == "code" for cell in executed.cells)
