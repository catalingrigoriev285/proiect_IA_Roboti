"""NLP datasets and experiment utilities."""

from tsp_ai.nlp.experiments import run_nlp_experiment
from tsp_ai.nlp.lab10 import (
	DEFAULT_CATEGORIES,
	load_20newsgroups,
	task1_basic_nb,
	task2_compare_classifiers,
	task3_ngram_study,
	task4_max_features_study,
	task5_grid_search,
)

__all__ = [
	"run_nlp_experiment",
	"DEFAULT_CATEGORIES",
	"load_20newsgroups",
	"task1_basic_nb",
	"task2_compare_classifiers",
	"task3_ngram_study",
	"task4_max_features_study",
	"task5_grid_search",
]
