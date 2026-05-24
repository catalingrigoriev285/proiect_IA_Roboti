"""NLP experiment runners and metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.app.services.run_service import RunService
from tsp_ai.nlp.datasets import load_dataset
from tsp_ai.nlp.pipelines import build_pipeline
from tsp_ai.nlp.plots import plot_confusion_matrix


def run_nlp_experiment(
    dataset: str,
    model: str,
    cache_dir: str | Path = "data/cache",
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
    stop_words: str | None = "english",
    seed: int = 42,
    save: bool = True,
) -> Dict[str, object]:
    """Run a single NLP experiment.

    Args:
        dataset: Dataset identifier ('sms', 'ag_news', 'imdb').
        model: Model identifier ('lr', 'svm').
        cache_dir: Cache directory for datasets.
        max_features: Max features for TF-IDF.
        ngram_range: N-gram range for word analyzer.
        min_df: Minimum document frequency.
        stop_words: Stop words configuration.
        seed: Random seed.
        save: Whether to save outputs.

    Returns:
        Dictionary with metrics and artifacts.
    """
    data = load_dataset(dataset, cache_dir)
    pipeline = build_pipeline(model, max_features, ngram_range, min_df, stop_words)
    pipeline.set_params(clf__random_state=seed) if model == "lr" else None

    pipeline.fit(data.x_train, data.y_train)
    preds = pipeline.predict(data.x_test)

    acc = accuracy_score(data.y_test, preds)
    macro_f1 = f1_score(data.y_test, preds, average="macro")
    report = classification_report(data.y_test, preds, output_dict=True)
    cm = confusion_matrix(data.y_test, preds)

    results = pd.DataFrame(
        [
            {
                "dataset": dataset,
                "model": model,
                "accuracy": acc,
                "macro_f1": macro_f1,
            }
        ]
    )

    figures = {"confusion_matrix": plot_confusion_matrix(cm, "Confusion Matrix", f"{dataset}-{model}")}

    run_dir = None
    if save:
        service = RunService()
        exp_result = ExperimentResult(
            run_type="nlp",
            task="basic",
            metrics=results.to_dict(orient="records"),
            summary={"accuracy": acc, "model": model},
        )
        run_dir = service.save_run(
            prefix=f"nlp_{dataset}_{model}",
            config={
                "dataset": dataset,
                "model": model,
                "max_features": max_features,
                "ngram_range": ngram_range,
                "min_df": min_df,
                "stop_words": stop_words,
                "seed": seed,
            },
            result=exp_result,
            figures=figures,
            artifacts={"confusion_matrix": cm.tolist()},
        )

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "report": report,
        "confusion_matrix": cm,
        "run_dir": run_dir,
    }
