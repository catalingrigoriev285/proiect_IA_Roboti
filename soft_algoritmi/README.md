# INTELIGENTA ARTIFICIALA 2025-2026

A comprehensive, production-ready platform for AI/optimization education featuring a desktop GUI and command-line tools. Includes a complete TSP solver suite (BKT, NN, HC, SA, GA) and NLP experimental platform.

## Features

### TSP Platform
- **Backtracking (BKT)**: Exact algorithm with branch-and-bound, configurable stop modes
- **Nearest Neighbor (NN)**: Base + multistart capabilities
- **Hill Climbing (HC)**: 2-opt with random restarts
- **Simulated Annealing (SA)**: Custom implementation with multiple schedules and neighbor ops
- **Genetic Algorithm (GA)**: Using PyGAD with OX crossover
- **Comprehensive benchmarking**: Small/medium/large suites with performance analysis
- **Visualization**: Tour plots, cost histories, temperature schedules, performance curves

### NLP Platform
- **Multiple datasets**: SMS Spam, AG News, IMDb
- **Pipelines**: TF-IDF + LogisticRegression, TF-IDF + LinearSVC
- **Evaluation**: Accuracy, F1, classification reports, confusion matrices
- **Visualization**: Learning curves, model comparisons

### Desktop GUI (PySide2)
- **TSP Solver tab**: Interactive solver with real-time results and visualization
- **TSP Benchmarks tab**: Suite-based benchmarking with comparative plots
- **NLP Experiments tab**: Dataset and model configuration with results
- **Outputs Viewer tab**: Browse and manage past experimental runs
- **Responsive UI**: Async workers to keep UI responsive during long operations

### Command-Line Interface
- Headless operation for automation and benchmarking
- Compatible with all GUI features

## Installation

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

### Launch GUI
```bash
python -m tsp_ai.gui.app
```

### Command-Line

**TSP Operations:**
```bash
# Run small benchmark suite
python -m tsp_ai.cli tsp bench --suite small

# Solve TSP with specific algorithm
python -m tsp_ai.cli tsp solve --matrix-file data/example.txt --algorithm sa --seed 42
```

**NLP Operations:**
```bash
# Run NLP experiment
python -m tsp_ai.cli nlp run --dataset sms --model lr --seed 42
```

## Project Structure

```
src/tsp_ai/
├── __init__.py
├── cli.py                          # CLI entry point
├── common/
│   ├── __init__.py
│   ├── run_registry.py            # Manage experiment runs
│   └── plotting.py                # Matplotlib/seaborn utilities
├── tsp/
│   ├── __init__.py
│   ├── types.py                   # TSPResult, dataclasses
│   ├── io_utils.py                # Matrix I/O, coordinate handling
│   ├── utils.py                   # Shared utilities (distance, validation)
│   ├── backtracking.py            # BKT exact solver
│   ├── nearest_neighbor.py        # NN heuristic
│   ├── hill_climbing.py           # HC metaheuristic
│   ├── simulated_annealing.py     # SA metaheuristic
│   ├── genetic_algorithm.py       # GA with PyGAD
│   ├── experiments.py             # Benchmark suites
│   └── plots.py                   # TSP-specific visualizations
├── nlp/
│   ├── __init__.py
│   ├── datasets.py                # Dataset loading & caching
│   ├── pipelines.py               # Vectorizers & classifiers
│   ├── experiments.py             # NLP benchmark framework
│   └── plots.py                   # NLP visualizations
└── gui/
    ├── __init__.py
    ├── app.py                     # QApplication entry
    ├── main_window.py             # Main window & tabs
    ├── widgets/
    │   ├── __init__.py
    │   └── mpl_canvas.py          # Matplotlib Qt integration
    ├── tabs/
    │   ├── __init__.py
    │   ├── tsp_solver_tab.py      # TSP Solver interface
    │   ├── tsp_benchmarks_tab.py  # Benchmarking interface
    │   ├── nlp_experiments_tab.py # NLP interface
    │   └── outputs_viewer_tab.py  # Results browser
    └── workers/
        ├── __init__.py
        ├── worker_base.py         # Base worker class
        ├── tsp_workers.py         # TSP background tasks
        └── nlp_workers.py         # NLP background tasks

data/                              # Dataset cache
outputs/                           # Experimental runs
tests/                             # Unit tests
```

## Output Format

All experimental runs are automatically saved to `outputs/runs/<timestamp>/` containing:
- `config.json`: Complete configuration and parameters
- `results.csv`: Metrics and results
- `plots/`: Generated visualizations (PNG format)

## Quality Standards

- Full type hints throughout
- Google-style docstrings (Args/Returns/Raises)
- No Romanian diacritics in code (UI strings may contain Romanian)
- Reproducible results with fixed seeds
- Comprehensive error handling
- Unit tests for core algorithms

## Testing

```bash
pytest tests/
```

## Author

AI/Optimization Course TA
