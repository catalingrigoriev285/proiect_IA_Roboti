
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.app.services.run_service import RunService
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
from tsp_ai.nlp.plots import plot_comparison_bars, plot_confusion_matrix, plot_heatmap
from tsp_ai.tsp import solve_tsp
from tsp_ai.tsp.experiments import run_tsp_benchmark
from tsp_ai.tsp.io_utils import (
    coords_to_distance_matrix,
    random_distance_matrix,
    read_coordinates_csv,
    read_matrix_file,
)
from tsp_ai.tsp.plots import plot_cost_vs_n, plot_gap_vs_n, plot_runtime_vs_n, plot_runtime_vs_n_log
from tsp_ai.tsp.utils import format_tour_route


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TSP and NLP CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    tsp = sub.add_parser("tsp", help="TSP operations")
    tsp_sub = tsp.add_subparsers(dest="tsp_cmd", required=True)

    tsp_solve = tsp_sub.add_parser("solve", help="Solve a TSP instance")
    tsp_solve.add_argument("--algorithm", required=True, choices=["bkt", "nn", "hc", "sa", "ga"])
    tsp_solve.add_argument("--matrix-file", type=str)
    tsp_solve.add_argument("--coords-file", type=str)
    tsp_solve.add_argument("--random-n", type=int)
    tsp_solve.add_argument("--seed", type=int, default=42)
    tsp_solve.add_argument("--save", action="store_true")

    tsp_bench = tsp_sub.add_parser("bench", help="Run TSP benchmarks")
    tsp_bench.add_argument("--suite", required=True, choices=["small", "medium", "large", "custom"])
    tsp_bench.add_argument("--algorithms", nargs="+", default=["nn", "hc", "sa", "ga"])
    tsp_bench.add_argument("--seed", type=int, default=42)
    tsp_bench.add_argument("--repeats", type=int, default=1)
    tsp_bench.add_argument("--sizes", nargs="+", type=int)

    nlp = sub.add_parser("nlp", help="NLP operations")
    nlp_sub = nlp.add_subparsers(dest="nlp_cmd", required=True)

    nlp_run = nlp_sub.add_parser("run", help="Run NLP experiment")
    nlp_run.add_argument("--dataset", required=True, choices=["sms", "ag_news", "imdb"])
    nlp_run.add_argument("--model", required=True, choices=["lr", "svm"])
    nlp_run.add_argument("--max-features", type=int, default=5000)
    nlp_run.add_argument("--min-df", type=int, default=2)
    nlp_run.add_argument("--ngram-min", type=int, default=1)
    nlp_run.add_argument("--ngram-max", type=int, default=2)
    nlp_run.add_argument("--seed", type=int, default=42)
    nlp_run.add_argument("--save", action="store_true")

    nlp_lab = nlp_sub.add_parser("lab10", help="Lab 10 tasks")
    nlp_lab.add_argument("task", choices=["task1", "task2", "task3", "task4", "task5"])
    nlp_lab.add_argument("--categories", type=str, default=",".join(DEFAULT_CATEGORIES))
    nlp_lab.add_argument("--ngram", type=str, default="1,2")
    nlp_lab.add_argument("--max-features", type=str, default="5000")
    nlp_lab.add_argument("--ngrams", type=str)
    nlp_lab.add_argument("--max-features-list", type=str)
    nlp_lab.add_argument("--classifiers", type=str, default="nb,svm,lr,rf")

    return parser.parse_args()


def _load_matrix(args: argparse.Namespace) -> List[List[int]]:
    if args.matrix_file:
        return read_matrix_file(args.matrix_file)
    if args.coords_file:
        coords = read_coordinates_csv(args.coords_file)
        return coords_to_distance_matrix(coords)
    if args.random_n:
        return random_distance_matrix(args.random_n, 1, 100, seed=args.seed)
    raise ValueError("Provide --matrix-file, --coords-file, or --random-n")


def _handle_tsp_solve(args: argparse.Namespace) -> None:
    D = _load_matrix(args)
    params: Dict = {"seed": args.seed}
    result = solve_tsp(args.algorithm, D, **params)
    print(f"Algorithm: {result.algorithm}")
    print(f"Cost: {result.cost}")
    print(f"Elapsed: {result.elapsed_sec:.4f}s")
    print(f"Tour: {result.tour}")
    print(f"Route: {format_tour_route(result.tour)}")

    if args.save:
        service = RunService()
        exp_result = ExperimentResult(
            run_type="tsp",
            task="solve",
            metrics=[
                {
                    "algorithm": result.algorithm,
                    "cost": result.cost,
                    "elapsed_sec": result.elapsed_sec,
                }
            ],
            summary={"algorithm": result.algorithm, "cost": result.cost},
        )
        service.save_run(
            prefix=f"tsp_{result.algorithm}",
            config={"algorithm": result.algorithm, "params": result.params},
            result=exp_result,
        )


def _handle_tsp_bench(args: argparse.Namespace) -> None:
    df = run_tsp_benchmark(
        suite=args.suite,
        algorithms=args.algorithms,
        seed=args.seed,
        repeats=args.repeats,
        custom_sizes=args.sizes,
    )
    print(df)

    service = RunService()
    figures = {
        "runtime_vs_n": plot_runtime_vs_n(df),
        "runtime_vs_n_log": plot_runtime_vs_n_log(df),
        "cost_vs_n": plot_cost_vs_n(df),
    }
    if args.suite == "small":
        figures["gap_vs_n"] = plot_gap_vs_n(df)

    result = ExperimentResult(
        run_type="tsp",
        task="benchmark",
        metrics=df.to_dict(orient="records"),
        summary={"suite": args.suite, "rows": len(df)},
    )
    service.save_run(
        prefix=f"tsp_bench_{args.suite}",
        config={
            "suite": args.suite,
            "algorithms": args.algorithms,
            "seed": args.seed,
            "repeats": args.repeats,
            "sizes": args.sizes,
        },
        result=result,
        figures=figures,
    )


def _handle_nlp_run(args: argparse.Namespace) -> None:
    ngram_range = (args.ngram_min, args.ngram_max)
    result = run_nlp_experiment(
        dataset=args.dataset,
        model=args.model,
        max_features=args.max_features,
        min_df=args.min_df,
        ngram_range=ngram_range,
        seed=args.seed,
        save=args.save,
    )
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"Macro F1: {result['macro_f1']:.4f}")


def _parse_ngram_list(raw: str) -> List[Tuple[int, int]]:
    items = []
    for part in raw.split(";"):
        a, b = part.split(",")
        items.append((int(a.strip()), int(b.strip())))
    return items


def _parse_max_features_list(raw: str) -> List[int | None]:
    values = []
    for part in raw.split(","):
        part = part.strip()
        if part.lower() == "none":
            values.append(None)
        else:
            values.append(int(part))
    return values


def _handle_nlp_lab10(args: argparse.Namespace) -> None:
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    ngram = tuple(int(x.strip()) for x in args.ngram.split(","))
    max_features = None
    if args.max_features.lower() != "none":
        max_features = int(args.max_features)
    classifiers = [c.strip() for c in args.classifiers.split(",") if c.strip()]
    data = load_20newsgroups(categories or DEFAULT_CATEGORIES)
    service = RunService()

    if args.task == "task1":
        metrics = task1_basic_nb(data, ngram, max_features, True, True)
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task1",
            metrics=[{"model": "nb", "accuracy": metrics["accuracy"], "train_time": metrics["train_time"]}],
            summary={"accuracy": metrics["accuracy"]},
        )
        service.save_run(
            prefix="nlp_lab10_task1",
            config={"task": "task1", "ngram": ngram, "max_features": max_features},
            result=result,
            figures={"confusion_matrix": plot_confusion_matrix(metrics["confusion_matrix"], "Confusion Matrix", "NB")},
            artifacts={"confusion_matrix": metrics["confusion_matrix"].tolist()},
        )
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        return

    if args.task == "task2":
        rows = task2_compare_classifiers(data, classifiers, ngram, max_features, True, True)
        best = max(rows, key=lambda r: r["accuracy"])
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task2",
            metrics=[{"model": r["classifier"], "accuracy": r["accuracy"], "train_time": r["train_time"]} for r in rows],
            summary={"best_model": best["classifier"], "accuracy": best["accuracy"]},
        )
        service.save_run(
            prefix="nlp_lab10_task2",
            config={"task": "task2", "classifiers": classifiers, "ngram": ngram, "max_features": max_features},
            result=result,
            figures={"comparison": plot_comparison_bars(
                [{"label": r["classifier"], "accuracy": r["accuracy"]} for r in rows],
                "Classifier Comparison",
            )},
            artifacts={"raw": rows},
        )
        print(f"Best: {best['classifier']} acc={best['accuracy']:.4f}")
        return

    if args.task == "task3":
        ngrams_raw = args.ngrams or (args.ngram if ";" in args.ngram else "1,1;1,2;2,2")
        ngrams = _parse_ngram_list(ngrams_raw)
        rows = task3_ngram_study(data, ngrams, "svm", max_features, True, True)
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task3",
            metrics=[{"ngram_range": r["ngram_range"], "accuracy": r["accuracy"], "train_time": r["train_time"]} for r in rows],
        )
        service.save_run(
            prefix="nlp_lab10_task3",
            config={"task": "task3", "ngrams": ngrams, "max_features": max_features},
            result=result,
            figures={"ngram_study": plot_comparison_bars(
                [{"label": r["ngram_range"], "accuracy": r["accuracy"]} for r in rows],
                "Ngram Study",
            )},
            artifacts={"raw": rows},
        )
        print("Task3 complete")
        return

    if args.task == "task4":
        mf_raw = args.max_features_list or (
            args.max_features if "," in args.max_features or "none" in args.max_features.lower() else "100,500,1000,5000,None"
        )
        mf_list = _parse_max_features_list(mf_raw)
        rows = task4_max_features_study(data, mf_list, "svm", ngram, True, True)
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task4",
            metrics=[{"max_features": r["max_features"], "accuracy": r["accuracy"], "train_time": r["train_time"]} for r in rows],
        )
        service.save_run(
            prefix="nlp_lab10_task4",
            config={"task": "task4", "max_features": mf_list, "ngram": ngram},
            result=result,
            figures={"max_features": plot_comparison_bars(
                [{"label": r["max_features"], "accuracy": r["accuracy"]} for r in rows],
                "Max Features Study",
            )},
            artifacts={"raw": rows},
        )
        print("Task4 complete")
        return

    if args.task == "task5":
        ngrams_raw = args.ngrams or "1,1;1,2;1,3"
        mf_raw = args.max_features_list or (args.max_features if "," in args.max_features else "500,2000,5000,10000")
        ngrams = _parse_ngram_list(ngrams_raw)
        mf_list = _parse_max_features_list(mf_raw)
        result_data = task5_grid_search(data, ngrams, mf_list, "svm", True, True)
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task5",
            metrics=[{
                "ngram_range": result_data["best"]["ngram_range"],
                "max_features": result_data["best"]["max_features"],
                "accuracy": result_data["best_accuracy"],
            }],
            summary={"best_accuracy": result_data["best_accuracy"]},
        )
        service.save_run(
            prefix="nlp_lab10_task5",
            config={"task": "task5", "ngrams": ngrams, "max_features": mf_list},
            result=result,
            figures={"grid": plot_heatmap(result_data["grid"], result_data["max_features"], result_data["ngram_ranges"], "Grid Search")},
            artifacts={"grid": result_data},
        )
        print("Task5 complete")
        return


def main() -> None:
    args = _parse_args()
    if args.command == "tsp":
        if args.tsp_cmd == "solve":
            _handle_tsp_solve(args)
        elif args.tsp_cmd == "bench":
            _handle_tsp_bench(args)
    elif args.command == "nlp":
        if args.nlp_cmd == "run":
            _handle_nlp_run(args)
        elif args.nlp_cmd == "lab10":
            _handle_nlp_lab10(args)


if __name__ == "__main__":
    main()
