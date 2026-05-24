"""Genetic algorithm TSP solver using PyGAD."""

from __future__ import annotations

import time
from typing import Dict, List

import numpy as np
import pygad

from tsp_ai.tsp.types import TSPResult
from tsp_ai.tsp.utils import random_tour, seed_rng, tour_cost, validate_distance_matrix


def _ox_crossover(parent1: np.ndarray, parent2: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(parent1)
    a, b = sorted(rng.choice(n, size=2, replace=False))
    child = [-1] * n
    child[a : b + 1] = parent1[a : b + 1].tolist()
    fill = [g for g in parent2 if g not in child]
    idx = 0
    for i in range(n):
        if child[i] == -1:
            child[i] = fill[idx]
            idx += 1
    return np.array(child, dtype=int)


def _swap_mutation(solution: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(solution)
    i, j = rng.choice(n, size=2, replace=False)
    mutated = solution.copy()
    mutated[i], mutated[j] = mutated[j], mutated[i]
    return mutated


def solve_genetic_algorithm(
    D: List[List[int]],
    pop_size: int = 100,
    generations: int = 200,
    mutation_rate: float = 0.2,
    selection_type: str = "tournament",
    elitism: int = 2,
    tournament_k: int = 3,
    seed: int | None = 42,
) -> TSPResult:
    """Solve TSP using a genetic algorithm with OX crossover.

    Args:
        D: Distance matrix.
        pop_size: Population size.
        generations: Number of generations.
        mutation_rate: Mutation probability per individual.
        selection_type: Selection type (tournament, rws, rank, sus).
        elitism: Number of elites to keep.
        tournament_k: Tournament size for selection.
        seed: Random seed.

    Returns:
        TSPResult with the best tour found.
    """
    validate_distance_matrix(D)
    rng = seed_rng(seed)
    t0 = time.perf_counter()
    n = len(D)

    initial_population = [random_tour(n, rng) for _ in range(pop_size)]

    def fitness_func(_, solution, __) -> float:
        cost = tour_cost(D, list(solution))
        return 1.0 / (cost + 1e-9)

    def on_crossover(parents, offspring_size, ga_instance):
        offspring = []
        for k in range(offspring_size[0]):
            p1 = parents[k % parents.shape[0]]
            p2 = parents[(k + 1) % parents.shape[0]]
            child = _ox_crossover(p1, p2, rng)
            offspring.append(child)
        return np.array(offspring)

    def on_mutation(offspring, ga_instance):
        for idx in range(offspring.shape[0]):
            if rng.random() < mutation_rate:
                offspring[idx] = _swap_mutation(offspring[idx], rng)
        return offspring

    ga = pygad.GA(
        num_generations=generations,
        num_parents_mating=pop_size // 2,
        fitness_func=fitness_func,
        sol_per_pop=pop_size,
        num_genes=n,
        initial_population=np.array(initial_population),
        parent_selection_type=selection_type,
        keep_elitism=elitism,
        K_tournament=tournament_k,
        crossover_type=on_crossover,
        mutation_type=on_mutation,
        allow_duplicate_genes=False,
        gene_type=int,
    )
    ga.run()
    solution, solution_fitness, _ = ga.best_solution()
    best_tour = list(solution)
    best_cost = tour_cost(D, best_tour)
    elapsed = time.perf_counter() - t0

    params = {
        "pop_size": pop_size,
        "generations": generations,
        "mutation_rate": mutation_rate,
        "selection_type": selection_type,
        "elitism": elitism,
        "tournament_k": tournament_k,
        "seed": seed,
    }
    cost_history = [1.0 / f if f != 0 else float("inf") for f in ga.best_solutions_fitness]
    history = {"cost_best": cost_history}
    meta: Dict[str, int | float] = {"final_fitness": solution_fitness}
    return TSPResult(
        tour=best_tour,
        cost=float(best_cost),
        elapsed_sec=elapsed,
        algorithm="ga",
        params=params,
        meta=meta,
        history=history,
    )
