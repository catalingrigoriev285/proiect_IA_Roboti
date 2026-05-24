"""Smoke test for Lab10 dataset loader."""

import pytest

from tsp_ai.nlp.lab10 import load_20newsgroups


def test_load_20newsgroups_smoke() -> None:
    try:
        data = load_20newsgroups()
    except Exception:
        pytest.skip("Dataset download failed (offline).")
    assert len(data.x_train) > 0
    assert len(data.x_test) > 0
