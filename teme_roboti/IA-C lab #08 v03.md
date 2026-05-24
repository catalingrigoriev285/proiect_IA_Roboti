# Laborator 08 - Călirea Simulată & Problema Comis-Voiajorului

---

## Cuprins

1. [Obiectivele lucrării de laborator](#1-obiectivele-lucrării-de-laborator)
2. [Călirea simulată - fundamente teoretice](#2-călirea-simulată--fundamente-teoretice)
   - 2.1 [Analogia fizică](#21-analogia-fizică)
   - 2.2 [Explicație intuitivă](#22-explicație-intuitivă)
   - 2.3 [Probabilitatea de acceptare](#23-probabilitatea-de-acceptare)
   - 2.4 [Pașii algoritmului](#24-pașii-algoritmului)
   - 2.5 [Metode de răcire (cooling schedules)](#25-metode-de-răcire-cooling-schedules)
   - 2.6 [Criterii de terminare](#26-criterii-de-terminare)
3. [Starea inițială - impact](#3-starea-inițială--impact)
   - 3.1 [Stare inițială aleatoare](#31-stare-inițială-aleatoare)
   - 3.2 [Stare inițială construită prin „cel mai apropiat vecin"](#32-stare-inițială-construită-prin-cel-mai-apropiat-vecin)
   - 3.3 [Comparație și recomandare practică](#33-comparație-și-recomandare-practică)
4. [Pseudocod - Simulated Annealing general](#4-pseudocod--simulated-annealing-general)
5. [Aplicarea SA la problema comis-voiajorului (TSP)](#5-aplicarea-sa-la-problema-comis-voiajorului-tsp)
   - 5.1 [Definiția TSP](#51-definiția-tsp)
   - 5.2 [Reprezentarea soluției și operatorul de vecinătate](#52-reprezentarea-soluției-și-operatorul-de-vecinătate)
   - 5.3 [Pseudocod SA-TSP](#53-pseudocod-sa-tsp)
   - 5.4 [Diagrama fluxului - MermaidJS](#54-diagrama-fluxului--mermaidjs)
6. [Implementare cu biblioteca `simanneal` (Python)](#6-implementare-cu-biblioteca-simanneal-python)
7. [Cerință practică - Implementare Python pur (temă)](#7-cerință-practică--implementare-python-pur-temă)
8. [Vizualizări recomandate](#8-vizualizări-recomandate)
9. [Referințe](#9-referințe)

---

## 1. Obiective

- Înțelegerea principiilor **călirii simulate** (*Simulated Annealing* - SA) ca strategie de căutare locală informată.
- Analiza influenței **stării inițiale** asupra calității soluției finale.
- Studiul **parametrilor algoritmului**: temperatură inițială, rată de răcire, număr de iterații.
- Aplicarea SA pentru rezolvarea **problemei comis-voiajorului** (*Travelling Salesman Problem* - TSP).
- Implementarea TSP-SA utilizând **biblioteca `simanneal`** în mediu virtual Python.
- Implementarea TSP-SA în **Python pur**, fără biblioteci de optimizare externe (temă individuală/echipă).
- Proiectarea și interpretarea **vizualizărilor** relevante pentru SA și TSP.

---

## 2. Călirea simulată - fundamente teoretice

### 2.1 Analogia fizică

Călirea simulată (*Simulated Annealing*, SA) este inspirată din **procesul metalurgic de călire**: un metal topit este încălzit la temperaturi foarte ridicate, după care este răcit *lent și controlat*. La temperaturi mari, atomii se mișcă haotic, explorând un spațiu larg de configurații; pe măsură ce temperatura scade, sistemul se „instalează" într-o stare de energie minimă - ideal, **minimul global**.

Dacă răcirea este *prea bruscă* (călire rapidă, *quenching*), atomii rămân blocați în configurații de energie ridicată - echivalentul unui **optim local** în optimizare. Răcirea lentă favorizează atingerea optimului global.

Algoritmul a fost introdus formal de **Kirkpatrick, Gelatt și Vecchi (1983)** și, independent, de **Černý (1985)**, devenind unul dintre cele mai studiate metaeuristici de optimizare.

### 2.2 Explicație intuitivă

SA este o extensie a **căutării locale** (*hill climbing*), cu un mecanism cheie care îi conferă avantaj: **acceptarea cu o anumită probabilitate a soluțiilor mai proaste**. Aceasta permite algoritmului să *scape din optimele locale*.

| Caracteristică               | Hill Climbing | Simulated Annealing                  |
| ---------------------------- | ------------- | ------------------------------------ |
| Acceptă soluții mai proaste? | ❌ Nu          | ✅ Da (cu prob. `P`)                  |
| Poate scăpa din optim local? | ❌ Nu          | ✅ Da                                 |
| Garantează optim global?     | ❌ Nu          | ✅ Teoretic (răcire infinit de lentă) |
| Cost computațional           | Mic           | Mediu–Mare                           |

### 2.3 Probabilitatea de acceptare

Probabilitatea de a accepta o soluție *mai proastă* este dată de **criteriul Metropolis**:

P(ΔE,T)=e^(−ΔE/T)

unde:

- `ΔE = Cost(S_nou) - Cost(S_curent)` - diferența de cost (pozitivă dacă soluția nouă e mai proastă)
- `T` - temperatura curentă

**Interpretare:**

- La **T mare** (început): `P → 1`, aproape orice soluție este acceptată → *explorare largă*
- La **T mic** (sfârșit): `P → 0`, doar soluțiile mai bune sunt acceptate → *exploatare locală*
- Cu cât `ΔE` este mai mare (soluție mult mai proastă), cu atât probabilitatea de acceptare este mai mică

### 2.4 Pași de implementare

1. **Inițializare**: generează o soluție inițială `S`; setează temperatura inițială `T = T_max`.
2. **Buclă principală** (cât timp condiția de terminare nu este îndeplinită):
   a. Generează un **vecin** `S'` al soluției curente `S`.
   b. Calculează `ΔE = Cost(S') - Cost(S)`.
   c. Dacă `ΔE ≤ 0` → **acceptă** `S'` (soluție mai bună sau egală).
   d. Dacă `ΔE > 0` → acceptă `S'` cu probabilitatea `P = e^(-ΔE/T)` (soluție mai proastă).
   e. Actualizează **cea mai bună soluție găsită** `S_best`.
   f. **Răcește** temperatura: `T = α × T`.
3. **Returnează** `S_best`.

### 2.5 Metode de răcire (cooling schedules)

#### a) Răcire geometrică (exponențială) - cea mai utilizată

T(i+1) = α × T(i),   unde α ∈ (0, 1), de obicei α ∈ [0.90, 0.99]

- `α` tipic: `0.90 – 0.99` (cu cât mai mare, cu atât răcirea e mai lentă și rezultatele mai bune).
- Temperatura inițială: `T_0 ∈ [100, 10000]` - depinde de domeniu.
- **Avantaj**: simplă, eficientă în practică.
- **Dezavantaj**: cu scădere geometrică, `T` nu atinge niciodată 0.

#### b) Răcire liniară

Ti+1​=Ti​−δ, δ>0 constant

- Mai puțin utilizată; riscul de a rata regiuni importante ale spațiului de căutare.

#### c) Răcire logaritmică (teoretică)

Ti​=c/ln(1+i)c, unde c este o constantă pozitivă iar i este numărul iterației curente

- Garantează optimalitatea globală, dar extrem de lentă - impractică pentru probleme reale.

#### d) Strategie adaptivă (warm restart)

- Se pornește cu `T` foarte mare → se răcește rapid până când ~60% din soluțiile mai proaste sunt acceptate.
- Aceasta devine „temperatura reală de start"; de aici, răcirea se face lent (amortizat).

### 2.6 Criterii de terminare

1. **Temperatura minimă atinsă**: `T < T_min` (ex. `T_min = 0.01` sau `1e-6`)
2. **Număr maxim de iterații**: `i = iterations_max`
3. **Stagnare**: nicio îmbunătățire a `S_best` în ultimele `k` iterații
4. **Convergență completă**: nicio tranziție acceptată (nici spre soluții mai bune, nici spre cele mai proaste) - algoritmul este „înghețat"

---

## 3. Starea inițială - impact

Aceasta este una dintre întrebările practice cele mai importante în utilizarea SA.

### 3.1 Stareinițială aleatoare

**Metodă**: se generează o permutare aleatoare a orașelor (pentru TSP).

```python
import random
tour = list(range(num_cities))
random.shuffle(tour)
```

**Avantaje:**

- Simplă de implementat.
- La temperaturi inițiale mari, SA explorează oricum spațiul larg → starea de start are influență redusă.
- Evită bias-ul de inițializare.

**Dezavantaje:**

- Poate porni dintr-o zonă foarte îndepărtată de optim → necesită mai multe iterații.

### 3.2 Stare inițială construită prin algoritmul „cel mai apropiat vecin"

**Metoda *Nearest Neighbour* (NN)**: un algoritm greedy care construiește un tur TSP pornind dintr-un oraș ales și adăugând la fiecare pas cel mai apropiat oraș nevizitat.

```python
def nearest_neighbour(distances, start=0):
    n = len(distances)
    visited = [False] * n
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        last = tour[-1]
        nearest = min(
            (distances[last][j], j)
            for j in range(n) if not visited[j]
        )[1]
        tour.append(nearest)
        visited[nearest] = True
    return tour
```

**Avantaje:**

- Oferă o soluție de start rezonabilă (~20–25% supraoptimală față de optim).
- SA pornește deja dintr-o „zonă bună" a spațiului de căutare.
- Poate reduce semnificativ timpul necesar pentru a atinge soluții de calitate.

**Dezavantaje:**

- Introduce un bias față de soluțiile din vecinătatea construcției greedy.
- La temperaturi inițiale mari, avantajul se diminuează (SA „uită" oricum starea inițială).

### 3.3 Comparație și recomandare practică

| Criteriu                                            | Start Aleator   | Start NN                    |
| --------------------------------------------------- | --------------- | --------------------------- |
| Ușurință implementare                               | ✅ Foarte simplă | ⚠️ Necesită cod suplimentar |
| Calitate soluție finale (T_max mare)                | ≈ egală         | ≈ egală                     |
| Calitate soluție finale (T_max mic / buget limitat) | ⬇️ Mai slabă    | ✅ Mai bună                  |
| Timp până la convergență                            | Mai lung        | Mai scurt                   |
| Diversitate explorare                               | ✅ Mai mare      | ⬇️ Mai mică                 |

**Recomandare**: pentru probleme TSP cu `N > 50` și buget de iterații limitat, **combinarea NN + SA** produce rezultate mai bune decât SA pur cu start aleator. Pentru analize comparative (ex. în laborator), veți rula ambele variante.

> 💡 **Regulă empirică**: dacă `T_max` este suficient de mare (acceptă inițial >80% din mutații), diferența dintre stările de start se atenuează considerabil. Dacă bugetul computațional este redus, starea NN oferă un avantaj clar.

---

## 4. Pseudocod - călirea simulată

```
Input:  ProblemSize, iterations_max, T_max, α
Output: S_best

 1  S_current ← CreateInitialSolution(ProblemSize)  // aleator sau NN
 2  S_best    ← S_current
 3  T         ← T_max

 4  for i = 1 to iterations_max do
 5      S_new      ← CreateNeighborSolution(S_current)
 6      ΔE         ← Cost(S_new) - Cost(S_current)

 7      if ΔE ≤ 0 then                               // soluție mai bună sau egală
 8          S_current ← S_new
 9          if Cost(S_new) < Cost(S_best) then
10              S_best ← S_new
11          end if

12      else                                          // soluție mai proastă
13          P ← exp(-ΔE / T)
14          if Random(0,1) < P then
15              S_current ← S_new                   // acceptare probabilistică
16          end if
17      end if

18      T ← α × T                                    // răcire geometrică
19  end for

20  return S_best
```

**Note**:

- `CreateNeighborSolution` - pentru TSP: swap de 2 orașe, inversarea unui subsegment (*2-opt*), etc.
- `Cost` - pentru TSP: lungimea totală a traseului
- `Random(0,1)` - număr uniform aleator din intervalul `[0, 1)`

---

## 5. Aplicarea SA la problema comis-voiajorului (TSP)

### 5.1 Definiția TSP

**Problema Comis-Voiajorului** (*Travelling Salesman Problem*): dat un graf complet cu `n` noduri (orașe) și distanțele dintre ele, găsește **turul hamiltonean de cost minim** - adică traseul care vizitează fiecare oraș exact o dată și se întoarce la punctul de plecare.

- TSP este **NP-hard** → nu există algoritm polinomial cunoscut pentru soluția exactă
- Pentru `n = 20` există `19!/2 ≈ 6 × 10^16` tururi posibile
- SA oferă soluții **aproape-optime** în timp rezonabil

### 5.2 Reprezentarea soluției și operatorul de vecinătate

**Reprezentare**: o permutare a orașelor `[c0, c1, c2, ..., c_{n-1}]`, unde `c_i` este al `i`-lea oraș vizitat.

**Operatori de vecinătate** (pentru generarea unei noi soluții `S_new`):

| Operator   | Descriere                                         | Complexitate |
| ---------- | ------------------------------------------------- | ------------ |
| **Swap**   | Inversează pozițiile a 2 orașe aleatoare          | O(1)         |
| **2-opt**  | Inversează un subsegment al turului               | O(n)         |
| **Or-opt** | Mută 1, 2 sau 3 orașe consecutive în altă poziție | O(n)         |
| **3-opt**  | Reconectează 3 muchii simultan                    | O(n²)        |

Pentru TSP cu SA, **2-opt** este cel mai utilizat datorită echilibrului dintre calitate și cost computațional.

```python
def two_opt_swap(tour, i, j):
    """Inversează subsegmentul tour[i:j+1]"""
    new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
    return new_tour
```

### 5.3 Pseudocod SA-TSP

```
Input:  cities[], iterations_max, T_max, α
Output: best_tour[]

 1  current_tour ← NearestNeighbour(cities)   // sau RandomPermutation(cities)
 2  best_tour    ← current_tour
 3  T            ← T_max

 4  for i = 1 to iterations_max do
 5      // Generare vecin prin 2-opt
 6      (a, b)   ← RandomPair(0, |cities|-1) cu a < b
 7      new_tour ← Reverse(current_tour, a, b)

 8      ΔD ← TourCost(new_tour) - TourCost(current_tour)

 9      if ΔD ≤ 0 then
10          current_tour ← new_tour
11          if TourCost(new_tour) < TourCost(best_tour) then
12              best_tour ← new_tour
13          end if
14      else
15          if exp(-ΔD / T) > Random(0, 1) then
16              current_tour ← new_tour
17          end if
18      end if

19      T ← α × T
20  end for

21  return best_tour
```

### 5.4 Diagrama de flux - MermaidJS

Diagrama MermaidJS a algoritmului SA este prezentată mai jos. Folosiți un viewer MermaidJS pentru a consulta diagrama.

```
flowchart TD
    A([START]) --> B[Inițializează turul curent\nNN sau aleator]
    B --> C[best_tour ← current_tour\nT ← T_max]
    C --> D{i ≤ iterations_max\nȘI T > T_min ?}

    D -- Da --> E[Generează new_tour\nprin swap 2-opt]
    E --> F[Calculează ΔD =\nCost_nou − Cost_curent]
    
    F --> G{ΔD ≤ 0 ?}
    
    G -- Da / soluție mai bună --> H[current_tour ← new_tour]
    H --> I{Cost_nou < Cost_best ?}
    I -- Da --> J[best_tour ← new_tour]
    I -- Nu --> K[T ← α × T\ni ← i + 1]
    J --> K
    
    G -- Nu / soluție mai proastă --> L[Calculează P = e^−ΔD/T]
    L --> M{Random0,1 < P ?}
    M -- Da --> N[current_tour ← new_tour\nacceptare probabilistică]
    M -- Nu --> O[Respinge new_tour]
    N --> K
    O --> K
    
    K --> D
    D -- Nu --> P([🏁 Returnează best_tour])
    
    style A fill:#4CAF50,color:#fff
    style P fill:#2196F3,color:#fff
    style G fill:#FF9800,color:#fff
    style M fill:#FF9800,color:#fff
    style J fill:#8BC34A,color:#fff
    style N fill:#FFC107,color:#333
```
---

## 6. Implementare folosind biblioteca `simanneal` (Python)

### Instalare în mediu virtual

```bash
# Creare și activare mediu virtual
python -m venv venv_sa
source venv_sa/bin/activate        # Linux / macOS
# sau: venv_sa\Scripts\activate    # Windows

# Instalare dependențe
pip install simanneal matplotlib numpy
```

### Implementare TSP cu `simanneal`

```python
"""
TSP rezolvat cu biblioteca simanneal
Referință: https://github.com/perrygeo/simanneal
"""

import math
import random
from simanneal import Annealer
import matplotlib.pyplot as plt
import numpy as np


# ─── Generare date ────────────────────────────────────────────────────────────

def generate_cities(n: int, seed: int = 42) -> list[tuple[float, float]]:
    """Generează n orașe cu coordonate aleatoare în [0, 100]."""
    random.seed(seed)
    return [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n)]


def euclidean_distance(c1: tuple, c2: tuple) -> float:
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def build_distance_matrix(cities: list) -> list[list[float]]:
    n = len(cities)
    return [[euclidean_distance(cities[i], cities[j]) for j in range(n)]
            for i in range(n)]


def tour_cost(tour: list, dist: list[list[float]]) -> float:
    return sum(dist[tour[i]][tour[(i + 1) % len(tour)]] for i in range(len(tour)))


# ─── Stare inițială: Nearest Neighbour ────────────────────────────────────────

def nearest_neighbour_tour(dist: list[list[float]], start: int = 0) -> list[int]:
    n = len(dist)
    visited = [False] * n
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        last = tour[-1]
        nearest = min((dist[last][j], j) for j in range(n) if not visited[j])[1]
        tour.append(nearest)
        visited[nearest] = True
    return tour


# ─── Clasa Annealer pentru TSP ────────────────────────────────────────────────

class TSPSolver(Annealer):
    """
    Subclasă a Annealer din simanneal.
    Starea (self.state) este un tur - o listă de indici ai orașelor.
    """

    def __init__(self, state: list[int], distance_matrix: list[list[float]]):
        self.distance_matrix = distance_matrix
        super().__init__(state)

    def move(self):
        """Operator de vecinătate: 2-opt swap."""
        n = len(self.state)
        i, j = sorted(random.sample(range(n), 2))
        self.state[i:j + 1] = self.state[i:j + 1][::-1]

    def energy(self) -> float:
        """Funcția de cost - lungimea totală a turului."""
        return tour_cost(self.state, self.distance_matrix)


# ─── Vizualizare tur ──────────────────────────────────────────────────────────

def plot_tour(cities: list, tour: list[int], title: str = "TSP Tour"):
    coords = [cities[i] for i in tour] + [cities[tour[0]]]
    xs, ys = zip(*coords)
    plt.figure(figsize=(8, 6))
    plt.plot(xs, ys, 'b-o', markersize=8, linewidth=1.5)
    for idx, (x, y) in enumerate(cities):
        plt.annotate(str(idx), (x, y), textcoords="offset points",
                     xytext=(5, 5), fontsize=9)
    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{title.replace(' ', '_')}.png", dpi=150)
    plt.show()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    N = 20                       # număr de orașe
    cities = generate_cities(N)
    dist = build_distance_matrix(cities)

    # Stare inițială: Nearest Neighbour
    init_tour = nearest_neighbour_tour(dist)
    print(f"Cost tur inițial (NN):  {tour_cost(init_tour, dist):.2f}")

    # Configurare SA
    solver = TSPSolver(init_tour[:], dist)   # copie a stării inițiale
    solver.Tmax = 10000.0    # temperatura maximă
    solver.Tmin = 1.0        # temperatura minimă
    solver.steps = 50000     # număr total de pași
    solver.updates = 100     # numărul de actualizări afișate în consolă

    # Rulare SA
    best_tour, best_cost = solver.anneal()

    print(f"Cost tur optim (SA):    {best_cost:.2f}")
    print(f"Tur: {best_tour}")

    # Vizualizare
    plot_tour(cities, init_tour, "Tur Initial NN")
    plot_tour(cities, best_tour, "Tur Optim SA simanneal")
```

### Explicarea parametrilor `simanneal`

| Parametru | Descriere                      | Valoare tipică   |
| --------- | ------------------------------ | ---------------- |
| `Tmax`    | Temperatura inițială (maximă)  | `1000 – 50000`   |
| `Tmin`    | Temperatura finală (minimă)    | `0.1 – 10`       |
| `steps`   | Numărul total de iterații      | `10000 – 500000` |
| `updates` | Frecvența afișării progresului | `50 – 200`       |

> 💡 `simanneal` ajustează automat `α` pe baza `Tmax`, `Tmin` și `steps`, calculând un factor de răcire geometric intern.

---

## 7. Temă - Implementare Python pură

### Posibilă structură a modulului (folosiți obligatoriu `__init__.py`)

```
tsp_sa/
├── __init__.py
├── annealer.py        # clasa principală SA
├── tsp_utils.py       # generare orașe, calcul cost, NN
├── cooling.py         # strategii de răcire
├── visualization.py   # grafice matplotlib
└── main.py            # punct de intrare
```

---

## 8. Vizualizări recomandate

Vizualizările enumerate mai jos sunt **cerințe de implementare** pentru laborator. Fiecare echipă trebuie să le includă în aplicația finală.

### V1 - Traseul TSP

**Ce afișează**: traseul curent pe un plan 2D, cu orașele ca noduri și muchiile ca segmente.

**Utilitate**: confirmă vizual calitatea soluției; permite observarea încrucișărilor (un tur cu încrucișări este evident suboptimal).

```python
# Apel: plot_tour(cities, best_tour, "Tur optim SA")
```

### V2 - Evoluția costului pe parcursul iterațiilor

**Ce afișează**: costul turului curent (linie subțire, semitransparentă) și costul celei mai bune soluții găsite (linie îngroșată) în funcție de numărul iterației.

**Utilitate**: permite analiza vitezei de convergență; oscilațiile mari la început sunt normale (temperatură mare); linia „best" trebuie să fie monoton descrescătoare.

```python
# Apel: plot_cost_history(sa.cost_history, sa.best_history)
```

### V3 - Programul de răcire

**Ce afișează**: evoluția temperaturii `T` în funcție de iterație, pe scală logaritmică.

**Utilitate**: verifică că răcirea are loc conform parametrilor; scala logaritmică evidențiază comportamentul exponențial al scăderii geometrice.

```python
# Apel: plot_temperature_schedule(sa.temp_history)
```

### V4 - Probabilitatea de acceptare Metropolis

**Ce afișează**: curbele `P = exp(-ΔE/T)` pentru mai multe valori de temperatură, în funcție de deteriorarea `ΔE`.

**Utilitate**: ilustrează intuitiv cum temperatura controlează explorarea; la `T` mare, chiar deteriorări semnificative sunt acceptate cu probabilitate ridicată.

```python
# Apel: plot_acceptance_probability(temps=[5000, 1000, 200, 50, 10])
```

### V5 - Comparație NN simplu vs. SA

**Ce afișează**: două subgrafice alăturate - turul obținut prin Nearest Neighbour și turul obținut prin SA, cu costurile afișate în titlu.

**Utilitate**: evidențiază îmbunătățirea adusă de SA față de soluția greedy de referință.

```python
# Apel: plot_comparison(cities, tour_nn, tour_sa, cost_nn, cost_sa)
```

### V6 - Timp de execuție vs. N

**Ce afișează**: grafic bar sau linie cu timpii de execuție (în secunde) pentru `N ∈ {8, 12, 20, 25}`, comparând implementarea `simanneal` cu implementarea proprie.

**Utilitate**: analiză empirică a scalabilității; permite identificarea overhead-ului bibliotecii față de implementarea nativă.

```python
import time
import matplotlib.pyplot as plt

sizes = [8, 12, 20, 25]
times_lib, times_own = [], []
costs_lib, costs_own = [], []

for n in sizes:
    cities = generate_cities(n)
    dist = build_distance_matrix(cities)

    # --- simanneal ---
    t0 = time.time()
    solver = TSPSolver(nearest_neighbour_tour(dist)[:], dist)
    solver.Tmax, solver.Tmin, solver.steps = 10000, 1, 50000
    _, cost = solver.anneal()
    times_lib.append(time.time() - t0)
    costs_lib.append(cost)

    # --- implementare proprie ---
    t0 = time.time()
    sa = SimulatedAnnealing(dist, T_max=10000, T_min=1, alpha=0.995,
                             iterations_per_temp=100)
    _, cost = sa.solve()
    times_own.append(time.time() - t0)
    costs_own.append(cost)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
x = range(len(sizes))
width = 0.35

ax1.bar([i - width/2 for i in x], times_lib, width, label="simanneal", color="steelblue")
ax1.bar([i + width/2 for i in x], times_own, width, label="Python pur", color="seagreen")
ax1.set_xticks(list(x)); ax1.set_xticklabels([str(n) for n in sizes])
ax1.set_xlabel("N (număr de orașe)"); ax1.set_ylabel("Timp (s)")
ax1.set_title("Timp de execuție vs. N"); ax1.legend(); ax1.grid(axis="y", alpha=0.3)

ax2.plot(sizes, costs_lib, 'o-', color="steelblue", label="simanneal")
ax2.plot(sizes, costs_own, 's--', color="seagreen", label="Python pur")
ax2.set_xlabel("N (număr de orașe)"); ax2.set_ylabel("Cost tur")
ax2.set_title("Calitatea soluției vs. N"); ax2.legend(); ax2.grid(True, alpha=0.3)

plt.suptitle("Comparație simanneal vs. implementare proprie", fontweight="bold")
plt.tight_layout()
plt.savefig("benchmark_comparison.png", dpi=150)
plt.show()
```

### V7 - Heatmap distanțe

**Ce afișează**: matricea distanțelor dintre orașe, reprezentată ca heatmap.

**Utilitate**: permite identificarea vizuală a clusterelor de orașe apropiate - informație utilă pentru analiza calității turului.

```python
import seaborn as sns  # pip install seaborn

def plot_distance_heatmap(dist_matrix, title="Matricea distanțelor"):
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(dist_matrix, annot=len(dist_matrix) <= 15,
                fmt=".0f", cmap="YlOrRd", ax=ax)
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig("distance_heatmap.png", dpi=150)
    plt.show()
```

---

## 9. Referințe

### Articole

1. **Kirkpatrick, S., Gelatt Jr., C. D., & Vecchi, M. P. (1983)**. *Optimization by Simulated Annealing*. Science, 220(4598), 671–680. [https://doi.org/10.1126/science.220.4598.671](https://doi.org/10.1126/science.220.4598.671)

2. **Černý, V. (1985)**. *Thermodynamical approach to the traveling salesman problem: An efficient simulation algorithm*. Journal of Optimization Theory and Applications, 45(1), 41–51. [https://doi.org/10.1007/BF00940812](https://doi.org/10.1007/BF00940812)

### Cărți de referință

4. **Russell, S., & Norvig, P. (2020)**. *Artificial Intelligence: A Modern Approach* (4th ed.), cap. 4 - *Search in Complex Environments*. Pearson.

5. **Aarts, E., & Korst, J. (1989)**. *Simulated Annealing and Boltzmann Machines*. Wiley.

6. **Laarhoven, P. J. M., & Aarts, E. H. L. (Eds.) (1987)**. *Simulated Annealing: Theory and Applications*. D. Reidel Publishing.

### Resurse online

7. **simanneal** - bibliotecă Python open-source pentru SA:
   
   - GitHub: [https://github.com/perrygeo/simanneal](https://github.com/perrygeo/simanneal)
   - PyPI: [https://pypi.org/project/simanneal/](https://pypi.org/project/simanneal/)

8. **TSPLIB** - colecție de instanțe TSP de referință pentru benchmarking:
   [http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/)

9. **Matplotlib** - vizualizare Python:
   [https://matplotlib.org/stable/gallery/index.html](https://matplotlib.org/stable/gallery/index.html)

10. **Wikipedia - Simulated Annealing**:
    [https://en.wikipedia.org/wiki/Simulated_annealing](https://en.wikipedia.org/wiki/Simulated_annealing)

---
