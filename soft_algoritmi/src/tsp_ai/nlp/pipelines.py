"""Pipeline builders for NLP models."""

from __future__ import annotations

from typing import Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


def build_vectorizer(
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
    stop_words: str | None = "english",
) -> FeatureUnion:
    """Build a combined word+char TF-IDF vectorizer.

    Args:
        max_features: Max features per vectorizer.
        ngram_range: N-gram range for word analyzer.
        min_df: Minimum document frequency.
        stop_words: Stop words configuration.

    Returns:
        FeatureUnion combining word and char TF-IDF.
    """
    word_vec = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        stop_words=stop_words,
        analyzer="word",
    )
    char_vec = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(3, 5),
        min_df=min_df,
        analyzer="char",
    )
    return FeatureUnion([("word", word_vec), ("char", char_vec)])


def build_pipeline(
    model: str,
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
    stop_words: str | None = "english",
) -> Pipeline:
    """Build a vectorizer + classifier pipeline.

    Args:
        model: Model type ('lr' or 'svm').
        max_features: Max features per vectorizer.
        ngram_range: N-gram range for word analyzer.
        min_df: Minimum document frequency.
        stop_words: Stop words configuration.

    Returns:
        Scikit-learn Pipeline.
    """
    vectorizer = build_vectorizer(max_features, ngram_range, min_df, stop_words)
    if model == "lr":
        clf = LogisticRegression(max_iter=200)
    elif model == "svm":
        clf = LinearSVC()
    else:
        raise ValueError("Unknown model type.")
    return Pipeline([("vec", vectorizer), ("clf", clf)])
