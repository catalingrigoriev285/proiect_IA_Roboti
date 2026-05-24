"""Algoritm Genetic peste politici (cf. teme/IA_lab_09.md).

Cromozomul = politica deterministica per celula (W*H gene, fiecare in 0..n_actions-1).
Fitness = recompensa totala obtinuta intr-un rollout greedy.
Crossover uniform (50% de la fiecare parinte) - VALID prin constructie pentru
mapare-celule.
Mutatie per gena: cu probabilitate `mut_rate`, schimba actiunea aleator.

Foloseste biblioteca PyGAD (din lab 09).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

try:
    import pygad   # type: ignore
except ImportError:   # pragma: no cover
    pygad = None

from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.policy import Policy

log = logging.getLogger("rl.genetic")


@dataclass
class GAStats:
    """Statistici peste generatii."""
    generations: int = 0
    best_fitness: list[float] = field(default_factory=list)
    mean_fitness: list[float] = field(default_factory=list)
    success_rate: list[float] = field(default_factory=list)   # % politici care ajung la goal
    elapsed_s: float = 0.0


def chromosome_to_policy(chromo: np.ndarray, width: int, height: int) -> Policy:
    """Decodeaza un cromozom 1D in matrice (H, W) de actiuni."""
    grid = chromo.reshape(height, width).astype(np.int8)
    return Policy(action_grid=grid, algo_name="genetic")


def _evaluate(chromo: np.ndarray, env: GridWorldEnv, n_rollouts: int = 1) -> tuple[float, bool]:
    """Ruleaza politica de N ori si returneaza (media recompenselor, reached_any_goal)."""
    pol = chromosome_to_policy(chromo, env.grid.width, env.grid.height)
    total = 0.0
    reached_any = False
    for _ in range(n_rollouts):
        s = env.reset()
        for _ in range(env.max_steps):
            a = pol(s)
            res = env.step(a)
            total += res.reward
            s = res.state
            if res.done:
                if res.info.get("reached_goal"):
                    reached_any = True
                break
    return total / n_rollouts, reached_any


def _uniform_crossover(parents: np.ndarray, offspring_size: tuple[int, int],
                       ga_instance) -> np.ndarray:
    """Crossover uniform pe cromozomi (gene independente)."""
    n_offspring, n_genes = offspring_size
    rng = np.random.default_rng()
    offspring = np.empty(offspring_size, dtype=parents.dtype)
    n_parents = parents.shape[0]
    for i in range(n_offspring):
        p1 = parents[i % n_parents]
        p2 = parents[(i + 1) % n_parents]
        mask = rng.random(n_genes) < 0.5
        child = np.where(mask, p1, p2)
        offspring[i] = child
    return offspring


def _random_mutation(offspring: np.ndarray, ga_instance) -> np.ndarray:
    """Mutatie: cu probabilitate `mutation_percent_genes/100`, schimba actiunea per gena."""
    rate = ga_instance.mutation_percent_genes / 100.0
    n_actions = ga_instance._n_actions   # injectat de noi mai jos
    rng = np.random.default_rng()
    for i in range(offspring.shape[0]):
        mask = rng.random(offspring.shape[1]) < rate
        n_mut = int(mask.sum())
        if n_mut:
            offspring[i, mask] = rng.integers(0, n_actions, size=n_mut)
    return offspring


class PolicyGA:
    """Wrapper peste PyGAD pentru evolvarea politicilor de tip mapare-celula.

    Foloseste:
        - crossover uniform (pe gene)
        - mutatie random per gena
        - selectie turneu (configurabila)
        - elitism (configurabil)
    """

    name = "genetic"

    def __init__(self, env: GridWorldEnv,
                 pop_size: int = 60, n_generations: int = 100,
                 mutation_percent_genes: float = 5.0,
                 keep_elitism: int = 2,
                 k_tournament: int = 3,
                 selection: str = "tournament",
                 n_rollouts_per_eval: int = 1,
                 seed: int | None = None) -> None:
        if pygad is None:
            raise ImportError("Pachetul `pygad` nu este instalat. Ruleaza: pip install pygad")
        self.env = env
        self.pop_size = pop_size
        self.n_generations = n_generations
        self.mutation_percent_genes = mutation_percent_genes
        self.keep_elitism = keep_elitism
        self.k_tournament = k_tournament
        self.selection = selection
        self.n_rollouts_per_eval = n_rollouts_per_eval
        self.seed = seed
        self.ga_instance = None
        self.stats = GAStats()
        # Best chromosome incarcat dupa run()
        self.best_chromo: np.ndarray | None = None

    def _build_initial_population(self) -> np.ndarray:
        n_genes = self.env.grid.width * self.env.grid.height
        n_actions = self.env.n_actions
        rng = np.random.default_rng(self.seed)
        return rng.integers(0, n_actions, size=(self.pop_size, n_genes)).astype(np.int8)

    def run(self, on_generation: Callable[[int, GAStats], None] | None = None,
            should_stop: Callable[[], bool] | None = None) -> GAStats:
        """Antreneaza populatia. Returneaza GAStats."""
        import time
        rng = random.Random(self.seed)

        init_pop = self._build_initial_population()
        env = self.env
        n_rollouts = self.n_rollouts_per_eval

        # Cache pentru success_rate pe generatie
        gen_state = {"reached_count": 0, "evaluated": 0}

        def fitness_func(ga_instance, sol, _idx):
            fit, reached = _evaluate(np.asarray(sol, dtype=np.int8), env, n_rollouts)
            if reached:
                gen_state["reached_count"] += 1
            gen_state["evaluated"] += 1
            return float(fit)

        def on_gen(ga_instance):
            self.stats.generations += 1
            best = float(np.max(ga_instance.last_generation_fitness))
            mean = float(np.mean(ga_instance.last_generation_fitness))
            sr = (gen_state["reached_count"] / max(1, gen_state["evaluated"]))
            self.stats.best_fitness.append(best)
            self.stats.mean_fitness.append(mean)
            self.stats.success_rate.append(sr)
            gen_state["reached_count"] = 0
            gen_state["evaluated"] = 0
            if on_generation is not None:
                on_generation(self.stats.generations, self.stats)
            if should_stop is not None and should_stop():
                return "stop"   # PyGAD opreste la string non-None
            return None

        t0 = time.perf_counter()
        ga = pygad.GA(
            num_generations=self.n_generations,
            num_parents_mating=max(2, self.pop_size // 3),
            fitness_func=fitness_func,
            initial_population=init_pop,
            gene_type=int,
            crossover_type=_uniform_crossover,
            mutation_type=_random_mutation,
            mutation_percent_genes=self.mutation_percent_genes,
            parent_selection_type=self.selection,
            K_tournament=self.k_tournament,
            keep_elitism=self.keep_elitism,
            keep_parents=0,
            random_seed=self.seed,
            on_generation=on_gen,
            suppress_warnings=True,
        )
        # Inject n_actions (folosit de mutatia noastra)
        ga._n_actions = env.n_actions

        ga.run()
        self.ga_instance = ga
        self.stats.elapsed_s = time.perf_counter() - t0

        best_sol, best_fit, _ = ga.best_solution()
        self.best_chromo = np.asarray(best_sol, dtype=np.int8)
        log.info("[genetic] Best fitness=%.2f dupa %d generatii (%.2fs).",
                 best_fit, self.stats.generations, self.stats.elapsed_s)
        return self.stats

    def policy(self) -> Policy:
        if self.best_chromo is None:
            raise RuntimeError("Apeleaza .run() inainte de policy().")
        return chromosome_to_policy(self.best_chromo, self.env.grid.width,
                                    self.env.grid.height)
