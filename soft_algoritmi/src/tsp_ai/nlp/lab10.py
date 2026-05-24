"""Lab 10 NLP tasks for 20 Newsgroups classification."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier


DEFAULT_CATEGORIES = [
    "sci.space",
    "rec.sport.hockey",
    "talk.politics.guns",
    "comp.graphics",
]


@dataclass
class Lab10Dataset:
    """Container for 20 Newsgroups splits.

    Args:
        x_train: Training texts.
        y_train: Training labels.
        x_test: Test texts.
        y_test: Test labels.
        target_names: Class names.
    """

    x_train: List[str]
    y_train: List[int]
    x_test: List[str]
    y_test: List[int]
    target_names: List[str]


def load_20newsgroups(
    categories: Optional[List[str]] = None,
    remove_headers: bool = True,
) -> Lab10Dataset:
    """Load 20 Newsgroups dataset with selected categories.

    Args:
        categories: List of category names.
        remove_headers: Whether to remove headers/footers/quotes.

    Returns:
        Lab10Dataset instance.
    """
    cats = categories or DEFAULT_CATEGORIES
    remove = ("headers", "footers", "quotes") if remove_headers else ()
    train = fetch_20newsgroups(subset="train", categories=cats, remove=remove)
    test = fetch_20newsgroups(subset="test", categories=cats, remove=remove)
    return Lab10Dataset(
        x_train=list(train.data),
        y_train=list(train.target),
        x_test=list(test.data),
        y_test=list(test.target),
        target_names=list(train.target_names),
    )


def build_pipeline(
    classifier: str,
    ngram_range: Tuple[int, int] = (1, 2),
    max_features: Optional[int] = 5000,
    stop_words: bool = True,
    sublinear_tf: bool = True,
) -> Pipeline:
    """Build a TF-IDF + classifier pipeline.

    Args:
        classifier: Classifier name (nb, svm, lr, rf).
        ngram_range: N-gram range.
        max_features: Max features or None.
        stop_words: Whether to use English stop words.
        sublinear_tf: Whether to use sublinear TF.

    Returns:
        Scikit-learn Pipeline.
    """
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        max_features=max_features,
        stop_words="english" if stop_words else None,
        sublinear_tf=sublinear_tf,
    )
    if classifier == "nb":
        clf = MultinomialNB()
    elif classifier == "svm":
        clf = LinearSVC()
    elif classifier == "lr":
        clf = LogisticRegression(max_iter=200)
    elif classifier == "rf":
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
    else:
        raise ValueError("Unknown classifier")
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def evaluate_model(
    pipeline: Pipeline,
    dataset: Lab10Dataset,
) -> Dict[str, object]:
    """Train and evaluate a model.

    Args:
        pipeline: Pipeline to train.
        dataset: Dataset container.

    Returns:
        Dictionary with metrics and outputs.
    """
    start = time.perf_counter()
    pipeline.fit(dataset.x_train, dataset.y_train)
    train_time = time.perf_counter() - start
    preds = pipeline.predict(dataset.x_test)
    acc = accuracy_score(dataset.y_test, preds)
    cm = confusion_matrix(dataset.y_test, preds)
    return {
        "accuracy": acc,
        "train_time": train_time,
        "confusion_matrix": cm,
        "preds": preds,
    }


def task1_basic_nb(
    dataset: Lab10Dataset,
    ngram_range: Tuple[int, int],
    max_features: Optional[int],
    stop_words: bool,
    sublinear_tf: bool,
) -> Dict[str, object]:
    """Task 1: Basic Naive Bayes model."""
    pipeline = build_pipeline("nb", ngram_range, max_features, stop_words, sublinear_tf)
    return evaluate_model(pipeline, dataset)


def task2_compare_classifiers(
    dataset: Lab10Dataset,
    classifiers: Iterable[str],
    ngram_range: Tuple[int, int],
    max_features: Optional[int],
    stop_words: bool,
    sublinear_tf: bool,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, object]]:
    """Task 2: Compare multiple classifiers.

    Args:
        dataset: Dataset container.
        classifiers: Iterable of classifier names.
        ngram_range: N-gram range.
        max_features: Max features or None.
        stop_words: Whether to use stop words.
        sublinear_tf: Whether to use sublinear TF.
        progress_cb: Optional progress callback.
        cancel_cb: Optional cancellation callback.

    Returns:
        List of result dictionaries.
    """
    results = []
    classifiers = list(classifiers)
    total = len(classifiers)
    for idx, clf in enumerate(classifiers, start=1):
        if cancel_cb and cancel_cb():
            raise RuntimeError("Cancelled")
        pipeline = build_pipeline(clf, ngram_range, max_features, stop_words, sublinear_tf)
        metrics = evaluate_model(pipeline, dataset)
        results.append({"classifier": clf, **metrics})
        if progress_cb:
            progress_cb(idx, total)
    return results


def task3_ngram_study(
    dataset: Lab10Dataset,
    ngram_ranges: List[Tuple[int, int]],
    classifier: str,
    max_features: Optional[int],
    stop_words: bool,
    sublinear_tf: bool,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, object]]:
    """Task 3: Study ngram_range impact."""
    results = []
    total = len(ngram_ranges)
    for idx, ngram in enumerate(ngram_ranges, start=1):
        if cancel_cb and cancel_cb():
            raise RuntimeError("Cancelled")
        pipeline = build_pipeline(classifier, ngram, max_features, stop_words, sublinear_tf)
        metrics = evaluate_model(pipeline, dataset)
        results.append({"ngram_range": f"{ngram}", **metrics})
        if progress_cb:
            progress_cb(idx, total)
    return results


def task4_max_features_study(
    dataset: Lab10Dataset,
    max_features_list: List[Optional[int]],
    classifier: str,
    ngram_range: Tuple[int, int],
    stop_words: bool,
    sublinear_tf: bool,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, object]]:
    """Task 4: Study max_features impact."""
    results = []
    total = len(max_features_list)
    for idx, mf in enumerate(max_features_list, start=1):
        if cancel_cb and cancel_cb():
            raise RuntimeError("Cancelled")
        pipeline = build_pipeline(classifier, ngram_range, mf, stop_words, sublinear_tf)
        metrics = evaluate_model(pipeline, dataset)
        label = "None" if mf is None else str(mf)
        results.append({"max_features": label, **metrics})
        if progress_cb:
            progress_cb(idx, total)
    return results


def task5_grid_search(
    dataset: Lab10Dataset,
    ngram_ranges: List[Tuple[int, int]],
    max_features_list: List[Optional[int]],
    classifier: str,
    stop_words: bool,
    sublinear_tf: bool,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> Dict[str, object]:
    """Task 5: Grid search over ngram_range and max_features.

    Returns:
        Dict containing heatmap data and best config.
    """
    grid = np.zeros((len(ngram_ranges), len(max_features_list)))
    best_acc = -1.0
    best_cfg = None
    total = len(ngram_ranges) * len(max_features_list)
    step = 0
    for i, ngram in enumerate(ngram_ranges):
        for j, mf in enumerate(max_features_list):
            if cancel_cb and cancel_cb():
                raise RuntimeError("Cancelled")
            pipeline = build_pipeline(classifier, ngram, mf, stop_words, sublinear_tf)
            metrics = evaluate_model(pipeline, dataset)
            grid[i, j] = metrics["accuracy"]
            if metrics["accuracy"] > best_acc:
                best_acc = metrics["accuracy"]
                best_cfg = {"ngram_range": ngram, "max_features": mf}
            step += 1
            if progress_cb:
                progress_cb(step, total)
    return {
        "grid": grid,
        "ngram_ranges": [str(n) for n in ngram_ranges],
        "max_features": ["None" if m is None else str(m) for m in max_features_list],
        "best": best_cfg,
        "best_accuracy": best_acc,
    }
