"""NLP-specific worker helpers."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from tsp_ai.nlp.lab10 import (
    DEFAULT_CATEGORIES,
    load_20newsgroups,
    task1_basic_nb,
    task2_compare_classifiers,
    task3_ngram_study,
    task4_max_features_study,
    task5_grid_search,
)


def run_lab10_task(
    task: str,
    categories: Optional[List[str]],
    ngram_range: Tuple[int, int],
    max_features: Optional[int],
    stop_words: bool,
    sublinear_tf: bool,
    classifiers: Optional[List[str]] = None,
    ngram_ranges: Optional[List[Tuple[int, int]]] = None,
    max_features_list: Optional[List[Optional[int]]] = None,
    progress_cb=None,
    cancel_cb=None,
) -> Dict[str, object]:
    """Execute a Lab10 task and return the results.

    Args:
        task: Task identifier (task1..task5).
        categories: Selected categories.
        ngram_range: Base ngram_range.
        max_features: Base max_features.
        stop_words: Whether to use English stop words.
        sublinear_tf: Whether to use sublinear TF.
        classifiers: Classifiers for task2.
        ngram_ranges: Ngram ranges for task3/task5.
        max_features_list: Max features list for task4/task5.
        progress_cb: Optional progress callback.
        cancel_cb: Optional cancel callback.

    Returns:
        Result dictionary.
    """
    data = load_20newsgroups(categories or DEFAULT_CATEGORIES)
    if task == "task1":
        metrics = task1_basic_nb(data, ngram_range, max_features, stop_words, sublinear_tf)
        return {"task": task, "dataset": data, "metrics": metrics}
    if task == "task2":
        clf_list = classifiers or ["nb", "svm", "lr", "rf"]
        results = task2_compare_classifiers(
            data,
            clf_list,
            ngram_range,
            max_features,
            stop_words,
            sublinear_tf,
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )
        return {"task": task, "dataset": data, "results": results}
    if task == "task3":
        ranges = ngram_ranges or [(1, 1), (1, 2), (2, 2)]
        results = task3_ngram_study(
            data,
            ranges,
            "svm",
            max_features,
            stop_words,
            sublinear_tf,
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )
        return {"task": task, "dataset": data, "results": results}
    if task == "task4":
        mf_list = max_features_list or [1000, 2000, 5000, None]
        results = task4_max_features_study(
            data,
            mf_list,
            "svm",
            ngram_range,
            stop_words,
            sublinear_tf,
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )
        return {"task": task, "dataset": data, "results": results}
    if task == "task5":
        ranges = ngram_ranges or [(1, 1), (1, 2), (1, 3)]
        mf_list = max_features_list or [500, 2000, 5000, 10000]
        result = task5_grid_search(
            data,
            ranges,
            mf_list,
            "svm",
            stop_words,
            sublinear_tf,
            progress_cb=progress_cb,
            cancel_cb=cancel_cb,
        )
        return {"task": task, "dataset": data, "result": result}
    raise ValueError("Unknown Lab10 task")
