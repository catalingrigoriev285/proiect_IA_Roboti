"""Dataset loading and caching for NLP experiments."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import List, Tuple

from sklearn.datasets import fetch_20newsgroups


@dataclass
class TextDataset:
    """Simple container for train/test splits.

    Args:
        x_train: Training texts.
        y_train: Training labels.
        x_test: Test texts.
        y_test: Test labels.
    """

    x_train: List[str]
    y_train: List[int]
    x_test: List[str]
    y_test: List[int]


def _require_datasets() -> None:
    try:
        import_module("datasets")
    except ImportError as exc:
        raise ImportError(
            "The 'datasets' package is required for NLP datasets. "
            "Install it with: pip install datasets"
        ) from exc


def load_dataset(name: str, cache_dir: str | Path) -> TextDataset:
    """Load a dataset from the Hugging Face datasets hub.

    Args:
        name: Dataset identifier ('sms', 'ag_news', 'imdb').
        cache_dir: Directory for dataset caching.

    Returns:
        TextDataset with train/test splits.
    """
    _require_datasets()
    from datasets import load_dataset as hf_load_dataset

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    key = name.lower()
    if key == "sms":
        ds = hf_load_dataset("sms_spam", cache_dir=str(cache_dir))
        train = ds["train"]
        test = ds["test"]
        x_train = list(train["sms"])
        y_train = list(train["label"])
        x_test = list(test["sms"])
        y_test = list(test["label"])
        return TextDataset(x_train, y_train, x_test, y_test)
    if key == "ag_news":
        ds = hf_load_dataset("ag_news", cache_dir=str(cache_dir))
        train = ds["train"]
        test = ds["test"]
        x_train = list(train["text"])
        y_train = list(train["label"])
        x_test = list(test["text"])
        y_test = list(test["label"])
        return TextDataset(x_train, y_train, x_test, y_test)
    if key == "imdb":
        ds = hf_load_dataset("imdb", cache_dir=str(cache_dir))
        train = ds["train"]
        test = ds["test"]
        x_train = list(train["text"])
        y_train = list(train["label"])
        x_test = list(test["text"])
        y_test = list(test["label"])
        return TextDataset(x_train, y_train, x_test, y_test)

    raise ValueError("Unknown dataset name.")


def load_20newsgroups_dataset(
    categories: List[str],
    remove_headers: bool = True,
) -> TextDataset:
    """Load the 20 Newsgroups dataset with selected categories.

    Args:
        categories: List of category names.
        remove_headers: Whether to remove headers/footers/quotes.

    Returns:
        TextDataset with train/test splits.
    """
    remove = ("headers", "footers", "quotes") if remove_headers else ()
    train = fetch_20newsgroups(subset="train", categories=categories, remove=remove)
    test = fetch_20newsgroups(subset="test", categories=categories, remove=remove)
    return TextDataset(
        x_train=list(train.data),
        y_train=list(train.target),
        x_test=list(test.data),
        y_test=list(test.target),
    )
