# Laborator \#04

## Euristica celui mai apropiat vecin (Nearest Neighbour Algorithm)

---

> **lucrare de laborator**

---

## Cuprins

- [Laborator #04](#laborator-04)
  - [Euristica celui mai apropiat vecin (Nearest Neighbour Algorithm)](#euristica-celui-mai-apropiat-vecin-nearest-neighbour-algorithm)
  - [Cuprins](#cuprins)
  - [1. Obiectivele lucrării de laborator](#1-obiectivele-lucrării-de-laborator)
  - [2. Euristica celui mai apropiat vecin](#2-euristica-celui-mai-apropiat-vecin)
    - [2.1 Clasificare: căutare informată constructivă (greedy)](#21-clasificare-căutare-informată-constructivă-greedy)
    - [2.2 Cum funcționează algoritmul](#22-cum-funcționează-algoritmul)
    - [2.3 Pseudocod](#23-pseudocod)
    - [2.4 Avantaje și limitări](#24-avantaje-și-limitări)
  - [3. Implementare - problema comis-voiajorului (TSP)](#3-implementare---problema-comis-voiajorului-tsp)
    - [3.1 Descrierea problemei și complexitatea](#31-descrierea-problemei-și-complexitatea)
    - [3.2 Matricea de distanțe și formatul fișierului](#32-matricea-de-distanțe-și-formatul-fișierului)
  - [4. Implementare de referință: Backtracking cu moduri de oprire](#4-implementare-de-referință-backtracking-cu-moduri-de-oprire)
    - [4.1 Descrierea celor 4 moduri de oprire](#41-descrierea-celor-4-moduri-de-oprire)
    - [4.2 Pseudocod extins](#42-pseudocod-extins)
    - [4.3 Cod Python complet (implementare de referință backtracking)](#43-cod-python-complet-implementare-de-referință-backtracking)
  - [5. Implementarea manuală a euristicii celui mai apropiat vecin](#5-implementarea-manuală-a-euristicii-celui-mai-apropiat-vecin)
    - [5.1 Pseudocod NN](#51-pseudocod-nn)
    - [5.2 Cod Python complet](#52-cod-python-complet)
  - [6. Rezolvarea TSP cu biblioteca `aima-python`](#6-rezolvarea-tsp-cu-biblioteca-aima-python)
    - [6.1 Alegerea bibliotecii](#61-alegerea-bibliotecii)
    - [6.2 Instalare și funcții disponibile](#62-instalare-și-funcții-disponibile)
    - [6.3 Exemplu de utilizare aima-python](#63-exemplu-de-utilizare-aima-python)
  - [7. Cerințele temei](#7-cerințele-temei)
    - [7.1 Sarcina A - Backtracking cu 4 moduri de oprire](#71-sarcina-a---backtracking-cu-4-moduri-de-oprire)
    - [7.2 Sarcina B - Nearest neighbor manual și aima-python în același proiect](#72-sarcina-b---nearest-neighbor-manual-și-aima-python-în-același-proiect)
    - [7.3 Sarcina C - Grafice de performanță](#73-sarcina-c---grafice-de-performanță)
  - [8. Bibliografie](#8-bibliografie)

---

## 1. Obiectivele lucrării de laborator

- Înțelegerea și implementarea **euristicii celui mai apropiat vecin** (*Nearest Neighbor*, NN) pentru rezolvarea problemei comis-voiajorului (TSP).
- Clasificarea corectă a algoritmului NN ca strategie de **căutare informată constructivă (greedy)**, distinctă atât de backtracking, cât și de căutarea locală.
- Extinderea implementării de backtracking din laboratorul anterior cu **4 moduri configurabile de oprire**.
- Utilizarea bibliotecii Python `aima3` pentru implementarea euristicii celui mai apropiat vecin.
- Compararea experimentală a performanței algoritmilor prin **grafice de performanță** generate cu `matplotlib`.

---

## 2. Euristica celui mai apropiat vecin

### 2.1 Clasificare: căutare informată constructivă (greedy)

> **Notă importantă privind clasificarea algoritmului:**
>
> Euristica celui mai apropiat vecin (*Nearest Neighbor*, NN) este un algoritm de **căutare informată constructivă**, cunoscut și sub denumirea de algoritm **greedy**. Această clasificare este esențială și trebuie distinsă clar de categoriile vecine:
>
> - **Nu** este căutare neinformată (BFS, DFS, backtracking pur): NN folosește o funcție euristică (distanța la vecinul cel mai apropiat) pentru a ghida construcția soluției.
> - **Nu** este căutare locală (hill climbing, din laboratorul precedent): NN construiește soluția **de la zero, pas cu pas**, adăugând câte un element la fiecare iterație, fără a porni dintr-o soluție completă și a o modifica.
> - Este un algoritm **constructiv**: soluția este construită incremental, luând la fiecare pas decizia care pare cea mai bună **local** (cel mai aproape vecin nevizitat), fără a reconsidera deciziile anterioare.
>
> Clasificarea corectă, conform lucrării de referință *Artificial Intelligence: A Modern Approach* (Russell & Norvig), plasează algoritmii greedy constructivi în categoria strategiilor de **căutare informată** - ei folosesc cunoaștere specifică problemei (funcția euristică *specifică domeniului*) pentru a lua decizii de construcție, dar o fac ireversibil și local.

Tabelul următor compară cele trei strategii studiate în cadrul laboratoarelor:

| Criteriu | Backtracking | Hill Climbing | Nearest Neighbor |
|---|---|---|---|
| Tip strategie | Sistematică, exhaustivă | Căutare locală | Constructivă greedy |
| Pornește de la | Soluție goală | Soluție completă | Soluție goală |
| Construiește soluția | Recursiv, cu revenire | Modificând soluția curentă | Pas cu pas, ireversibil |
| Folosește euristică | Nu (prunere B&B) | **Da** (funcție de evaluare) | **Da** (distanța minimă) |
| Revine asupra deciziilor | **Da** (backtrack) | Nu | **Nu** |
| Garantează optimul global | **Da** (exhaustiv) | Nu | Nu |
| Complexitate timp | O((N-1)!) | Depinde de vecinătate | **O(N²)** |
| Complexitate spațiu | O(N) | O(1) | **O(N)** |

---

### 2.2 Cum funcționează algoritmul

Ideea centrală a euristicii celui mai apropiat vecin este intuitivă: **la fiecare pas, mergem în cel mai aproape oraș nevizitat**.

**Analogia:** Un comis-voiajor care nu cunoaște harta decide, din fiecare oraș în care se află, să meargă la cel mai aproape oraș nevizitat - fără a planifica traseul în avans și fără a reveni asupra deciziilor deja luate.

**Exemplu numeric ilustrativ - matrice 4×4**

```
        0    1    2    3
   0  [ 0   10   15   20 ]
   1  [10    0   35   25 ]
   2  [15   35    0   30 ]
   3  [20   25   30    0 ]
```

Aplicarea NN cu startul în orașul 0:

| Pas | Oraș curent | Nevizitați | Distanțe la nevizitați | Ales | Cost parțial |
|---|---|---|---|---|---|
| 1 | 0 | {1, 2, 3} | 10, 15, 20 | **1** (min=10) | 10 |
| 2 | 1 | {2, 3} | 35, 25 | **3** (min=25) | 35 |
| 3 | 3 | {2} | 30 | **2** (unic) | 65 |
| 4 | 2 | {} | - | *retur la 0*: 15 | **80** |

Traseul NN: **0 → 1 → 3 → 2 → 0**, cost = **80**.

Acesta coincide cu **traseul optim** găsit de backtracking în laboratorul precedent. NN a avut noroc în acest caz - alegerile greedy au condus la soluția optimă.

---

**Exemplu numeric - matricea 5×5 unde NN nu găsește optimul:**

```
        0    1    2    3    4
   0  [ 0    5    2    8    9 ]
   1  [ 5    0    3    1    7 ]
   2  [ 2    3    0    6    4 ]
   3  [ 8    1    6    0    2 ]
   4  [ 9    7    4    2    0 ]
```

Aplicarea NN cu startul în orașul 0:

| Pas | Oraș curent | Nevizitați | Distanțe la nevizitați | Ales | Cost parțial |
|---|---|---|---|---|---|
| 1 | 0 | {1, 2, 3, 4} | 5, **2**, 8, 9 | **2** (min=2) | 2 |
| 2 | 2 | {1, 3, 4} | **3**, 6, 4 | **1** (min=3) | 5 |
| 3 | 1 | {3, 4} | **1**, 7 | **3** (min=1) | 6 |
| 4 | 3 | {4} | **2** | **4** (unic) | 8 |
| 5 | 4 | {} | - | *retur la 0*: 9 | **17** |

Traseul NN: **0 → 2 → 1 → 3 → 4 → 0**, cost = **17**.

**Traseul optim** (găsit prin backtracking exhaustiv): **0 → 2 → 4 → 3 → 1 → 0**, cost = **14**.

La pasul 2, NN a ales orașul 1 (d=3) în locul orașului 4 (d=4), decizie care părea mai bună local - dar a condus la un tur cu costul final 17 față de 14. **Prețul vitezei**: NN a executat în O(N²) operații, backtracking în O(N!) - dar a sacrificat 21.4% din calitate.

*gap față de optim*
```
gap% = (cost_NN - cost_optim) / cost_optim × 100
gap% = (17 - 14) / 14 × 100 ≈ 21.4%
```

---

### 2.3 Pseudocod

**Nearest Neighbor - variantă de bază (un singur punct de start):**

```
funcție NEAREST-NEIGHBOR(matrice, n, start):
    traseu ← [start]
    vizitat ← {start}
    oras_curent ← start
    cost_total ← 0

    repetă de n-1 ori:
        cel_mai_aproape ← -1
        dist_min ← ∞

        pentru fiecare oras de la 0 la n-1:
            dacă oras ∉ vizitat și matrice[oras_curent][oras] < dist_min:
                dist_min ← matrice[oras_curent][oras]
                cel_mai_aproape ← oras

        cost_total ← cost_total + dist_min
        traseu.adaugă(cel_mai_aproape)
        vizitat.adaugă(cel_mai_aproape)
        oras_curent ← cel_mai_aproape

    // Inchidem turul - revenim la orasul de start
    cost_total ← cost_total + matrice[oras_curent][start]
    returnează (traseu, cost_total)
```

**Nearest Neighbor Multistart - toate punctele de start (modul Y soluții / timp):**

```
funcție NEAREST-NEIGHBOR-MULTISTART(matrice, n):
    best_traseu ← Nul
    best_cost ← ∞
    toate_costurile ← []

    pentru fiecare start de la 0 la n-1:
        (traseu, cost) ← NEAREST-NEIGHBOR(matrice, n, start)
        toate_costurile.adaugă(cost)
        dacă cost < best_cost:
            best_cost ← cost
            best_traseu ← traseu

    returnează (best_traseu, best_cost, toate_costurile)
```

---

### 2.4 Avantaje și limitări

**Avantaje:**

- **Eficiență foarte bună** - complexitate O(N²), aplicabil pentru N = sute sau mii de orașe.
- **Implementare simplă** - un singur ciclu extern de N pași, fiecare cu un minim liniar.
- **Soluție imediată** - nu necesită timp de "convergență"; soluția este construită într-o singură trecere.
- **Calitate rezonabilă** - în practică, soluțiile NN sunt, de regulă, cu 20–25% mai scumpe decât optimul, ceea ce este acceptabil pentru multe aplicații.
- **Bază pentru algoritmi mai avansați** - soluția NN poate fi îmbunătățită ulterior prin optimizări locale (2-opt, 3-opt, Lin-Kernighan).

**Limitări:**

- **Fără garanție de optimalitate** - decizia greedy la fiecare pas poate duce la soluții departe de optim (vorbim aici de optimul global!).
- **Efectul "ultimei margini"** - traseul construit adesea se termină cu o muchie scumpă de retur, deoarece penultimul și ultimul oraș vizitat pot fi departe de punctul de start.
- **Sensibil la punctul de start** - traseele obținute pornind din orașe diferite pot varia semnificativ în calitate. Soluție: **multistart NN** - rularea din toate sau mai multe puncte de start și păstrarea celui mai bun traseu.
- **Nu poate ieși din decizii proaste** - spre deosebire de backtracking, NN nu revine niciodată asupra alegerilor anterioare.

---

## 3. Implementare - problema comis-voiajorului (TSP)

### 3.1 Descrierea problemei și complexitatea

> Această secțiune sintetizează elementele esențiale din laboratorul precedent.

**Enunț:** Un comis-voiajor trebuie să viziteze `N` orașe, fiecare exact o singură dată, și să se întoarcă la orașul de plecare. Costul deplasării între oricare două orașe este cunoscut. Se cere determinarea ordinii de vizitare cu **costul total minim**.

**Complexitate:** Numărul de tururi distincte pentru TSP simetric este `(N − 1)! / 2`, ceea ce face TSP o problemă **NP-hard**. Tabelul de mai jos justifică necesitatea algoritmilor euristici pentru N mare:

| N (orașe) | Tururi posibile | Timp BT (estimat) | Timp NN |
|---|---|---|---|
| 5 | 12 | < 1 ms | < 1 ms |
| 10 | 181.440 | ~10 ms | < 1 ms |
| 12 | ~20 milioane | ~1–2 s | < 1 ms |
| 15 | ~43 miliarde | zeci de minute | < 1 ms |
| 20 | ~6 × 10¹⁶ | prohibitiv | < 1 ms |
| 50 | ~10⁶² | imposibil | < 1 ms |
| 100 | ~10¹⁵⁷ | imposibil | < 1 ms |

---

### 3.2 Matricea de distanțe și formatul fișierului

Formatul fișierului de intrare este identic cu cel din Laboratorul \#03:

```
N
D[0][0]  D[0][1]  ...  D[0][N-1]
D[1][0]  D[1][1]  ...  D[1][N-1]
...
D[N-1][0]  D[N-1][1]  ...  D[N-1][N-1]
```

**Exemplu (`orase.txt`, N=4):**

```text
4
0 10 15 20
10 0 35 25
15 35 0 30
20 25 30 0
```

**Exemplu (`orase5.txt`, N=5 - exemplul cu gap):**

```text
5
0 5 2 8 9
5 0 3 1 7
2 3 0 6 4
8 1 6 0 2
9 7 4 2 0
```

Proprietățile matricei:
- `D[i][i] = 0` - distanța unui oraș față de el însuși este zero.
- `D[i][j] > 0` pentru `i ≠ j` - toate drumurile au cost strict pozitiv.
- `D[i][j] = D[j][i]` - TSP simetric (costul nu depinde de direcție).

---

## 4. Implementare de referință: Backtracking cu moduri de oprire

### 4.1 Descrierea celor 4 moduri de oprire

Implementarea de referință extinde backtracking-ul din Laboratorul \#03 cu posibilitatea de a **configura condiția de oprire**. Există patru moduri:

---

**Modul `prima` - Prima soluție găsită**

- **Comportament:** Algoritmul se oprește imediat ce a găsit primul tur complet valid (indiferent de calitate).
- **Când se folosește:** Verificare rapidă că implementarea funcționează; cazuri unde orice soluție acceptabilă este suficientă.
- **Avantaje:** Extrem de rapid pentru N mare; nu necesită explorare exhaustivă.
- **Limitări:** Calitatea soluției este imprevizibilă - poate fi departe de optim.

---

**Modul `toate` - Toate soluțiile (exhaustiv)**

- **Comportament:** Algoritmul explorează **întreg** spațiul de soluții și garantează returnarea traseului de cost minim.
- **Când se folosește:** Instanțe mici (N ≤ 12–13) unde se dorește soluția optimă certă; generarea setului complet de soluții pentru analiză.
- **Avantaje:** Garanție de optimalitate globală; prunerea branch-and-bound reduce semnificativ spațiul explorat.
- **Limitări:** Timp exponențial; prohibitiv pentru N > 13–14.

---

**Modul `timp` - Oprire după T secunde**

- **Comportament:** Algoritmul rulează cel mult `timp_max` secunde. La expirarea timpului, se returnează cel mai bun tur complet găsit până la acel moment.
- **Când se folosește:** Scenarii cu constrângeri de timp reale; compararea cu NN care găsește o soluție instantaneu.
- **Avantaje:** Controlul timpului de execuție; backtracking-ul îmbunătățește progresiv soluția pe măsură ce explorează.
- **Limitări:** Soluția finală depinde de noroc (ce ramuri au fost explorate în fereastra de timp); fără garanție de optimalitate.

---

**Modul `y_solutii` - Oprire după Y soluții complete**

- **Comportament:** Algoritmul se oprește după ce a găsit `y_max` soluții complete (tururi valide). Se returnează cel mai bun tur din setul găsit.
- **Când se folosește:** Compararea directă cu NN multistart (ambii generează Y soluții, se compară calitatea celei mai bune); analiza diversității soluțiilor.
- **Avantaje:** Soluțiile BT se îmbunătățesc monoton (fiecare soluție nouă găsită este mai bună sau egală cu precedenta, datorită prunerii); comparație echitabilă cu NN multistart.
- **Limitări:** Nu garantează că primele Y soluții acoperă uniform spațiul de stări.

---

### 4.2 Pseudocod extins

```
// Variabile partajate (accesibile din funcția recursivă)
cost_minim ← ∞
traseu_optim ← []
nr_solutii ← 0
oprire ← Fals

funcție BACKTRACKING-EXTINS(matrice, n, oras_curent, vizitat, traseu, cost,
                              mod, timp_max, timp_start, y_max):
    dacă oprire:
        returnează

    dacă lungime(traseu) == n:
        cost_total ← cost + matrice[oras_curent][traseu[0]]
        nr_solutii ← nr_solutii + 1

        dacă cost_total < cost_minim:
            cost_minim ← cost_total
            traseu_optim ← copie(traseu)

        // Verificam conditia de oprire dupa gasirea solutiei
        dacă mod == 'prima':
            oprire ← Adevărat
        dacă mod == 'y_solutii' și nr_solutii >= y_max:
            oprire ← Adevărat
        returnează

    pentru fiecare urmator de la 0 la n-1:
        dacă oprire:
            returnează
        dacă vizitat[urmator]:
            continuă

        // Verificam limita de timp
        dacă mod == 'timp' și timp_curent() - timp_start >= timp_max:
            oprire ← Adevărat
            returnează

        cost_nou ← cost + matrice[oras_curent][urmator]
        dacă mod in {'toate', 'prima', 'y_solutii'} și cost_nou >= cost_minim:
            continuă  // prunere branch-and-bound

        vizitat[urmator] ← Adevărat
        traseu.adaugă(urmator)
        BACKTRACKING-EXTINS(matrice, n, urmator, vizitat, traseu, cost_nou, ...)
        traseu.elimină_ultimul()
        vizitat[urmator] ← Fals
```

---

### 4.3 Cod Python complet (implementare de referință backtracking)

**Ieșire așteptată pentru exemplul cu N=4 (`orase.txt`), modul `toate`:**

```
Traseu optim:   0 -> 1 -> 3 -> 2 -> 0
Cost minim:     80
Solutii gasite: 3
Timp de executie: 0.000045 secunde
```

**Ieșire așteptată pentru N=5 (`orase5.txt`), modul `toate`:**

```
Traseu optim:   0 -> 2 -> 4 -> 3 -> 1 -> 0
Cost minim:     14
Solutii gasite: 12
Timp de executie: 0.000120 secunde
```

---

## 5. Implementarea manuală a euristicii celui mai apropiat vecin

### 5.1 Pseudocod NN

Pseudocodul detaliat este prezentat în Secțiunea 2.3. Recapitulare:

```
funcție NEAREST-NEIGHBOR(matrice, n, start=0):
    construieste traseul adaugand la fiecare pas
    cel mai aproape oras nevizitat
    returnează (traseu, cost_total)

funcție NEAREST-NEIGHBOR-MULTISTART(matrice, n):
    ruleaza NEAREST-NEIGHBOR din fiecare oras ca punct de start
    returnează (best_traseu, best_cost, toate_costurile)
```

---

### 5.2 Cod Python complet

**Ieșire așteptată pentru exemplul cu N=4:**

```
=== Nearest Neighbor (start=0) ===
Traseu: 0 -> 1 -> 3 -> 2 -> 0
Cost:   80

=== Nearest Neighbor Multistart ===
Start 0: 0 -> 1 -> 3 -> 2 -> 0  (cost=80)
Start 1: 1 -> 0 -> 3 -> 2 -> 1  (cost=80)
Start 2: 2 -> 0 -> 1 -> 3 -> 2  (cost=80)
Start 3: 3 -> 0 -> 1 -> 2 -> 3  (cost=80)
Cel mai bun: cost=80
```

**Ieșire așteptată pentru exemplul cu N=5:**

```
=== Nearest Neighbor (start=0) ===
Traseu: 0 -> 2 -> 1 -> 3 -> 4 -> 0
Cost:   17   ← nu este optim (optimul este 14)

=== Nearest Neighbor Multistart ===
Start 0: cost=17
Start 1: cost=14   ← gaseste optimul pornind din 1
Start 2: cost=16
Start 3: cost=14
Start 4: cost=17
Cel mai bun: cost=14
```

*Observație:* Multistart NN găsește în acest caz soluția optimă (14) pornind din orașele 1 sau 3, chiar dacă pornind din 0 dădea 17.

---

## 6. Rezolvarea TSP cu biblioteca `aima-python`

### 6.1 Alegerea bibliotecii

Pentru implementarea euristicii celui mai apropiat vecin cu o bibliotecă externă, se recomandă **`aima3`** (pachetul PyPI al proiectului aima-python), față de alternativa `simpleai` utilizată în laboratorul precedent.

| Criteriu | `simpleai` | `aima3` (aima-python) |
|---|---|---|
| Instalare | `pip install simpleai` | `pip install aima3` |
| Versiuni PyPI | Da | Da (pachet neoficial) |
| Algoritmi NN | Nu - fără implementare NN built-in | **Da** - `nearest_neighbor_tsp` |
| Algoritmi locali | `hill_climbing`, `simulated_annealing` | Similari + algoritmi genetici |
| Potrivit pentru Lab \#03 | **Da** (hill climbing) | Opțional |
| Potrivit pentru Lab \#04 | Nu (fără NN built-in) | **Da** (NN nativ) |
| Documentație | Dedicată, online | Cod sursă + carte AIMA |
| Recomandare | Lab \#03 (HC) | **Lab \#04 (NN)** |

`aima3` este implementarea Python a algoritmilor din cartea de referință *Artificial Intelligence: A Modern Approach* (Russell & Norvig) și include `nearest_neighbor_tsp` ca funcție nativă în modulul `search`.

---

### 6.2 Instalare și funcții disponibile

**Instalare (varianta recomandată - pachet PyPI):**

```bash
pip install aima3
```

**Instalare alternativă (clonare GitHub pentru acces la cod sursă complet):**

```bash
git clone https://github.com/aimacode/aima-python.git
cd aima-python
pip install -e .
```

**Funcții relevante disponibile în `aima3`:**

| Funcție / Clasă | Modul | Descriere |
|---|---|---|
| `nearest_neighbor_tsp(start, cities, distances)` | `search` | Euristica NN pentru TSP |
| `ProblemSolvingAgent` | `agents` | Agent generic de rezolvare probleme |
| `Graph` | `search` | Graf cu noduri și muchii ponderate |
| `hill_climbing(problem)` | `search` | Hill climbing steepest ascent |
| `simulated_annealing(problem, schedule)` | `search` | Recoacere simulată |

**Semnătura `nearest_neighbor_tsp`** (din sursa aima-python):

```python
def nearest_neighbor_tsp(start, cities, distances):
    """
    Construieste un tur TSP prin euristica celui mai apropiat vecin.

    Args:
        start    : numele/indexul orasului de start
        cities   : lista cu toate orasele (list)
        distances: dictionar de dictionare; distances[a][b] = distanta de la a la b

    Returns:
        Lista de orase in ordinea vizitarii (list), incepand cu start.
        Turul este ciclic - ultimul oras revine la start (neinclus explicit).
    """
```

---

### 6.3 Exemplu de utilizare aima-python

**Ieșire așteptată:**

```
=== Exemplu N=4 (din lab 03) ===
Traseu NN (start=0): 0 -> 1 -> 3 -> 2 -> 0
Cost:                80

=== Exemplu N=5 (cu gap fata de optim) ===
  Start 0: cost=17
  Start 1: cost=14
  Start 2: cost=16
  Start 3: cost=14
  Start 4: cost=17
Cel mai bun traseu: 1 -> 3 -> 4 -> 2 -> 0 -> 1
Cost minim NN:      14
Cost optim (BT):    14
Gap%:               0.0%
```

---

## 7. Cerințele temei

Tema se rezolvă ca un **proiect Python structurat** local, organizat în module distincte. Toate funcțiile publice vor fi documentate cu **docstrings în stil Google** (secțiunile `Args:`, `Returns:`, `Raises:` acolo unde este cazul). Comentariile din codul Python nu vor conține diacritice.

### 7.1 Sarcina A - Backtracking cu 4 moduri de oprire

Implementați algoritmul de backtracking ca proiect structurat cu **4 moduri de oprire** configurabile:

```
tsp_proiect/
├── main.py               # Punct de intrare: parsare argumente, apel functii, afisare
├── io_utils.py           # citeste_matrice(cale), genereaza_matrice_aleatorie(n, seed)
├── backtracking.py       # rezolva_tsp_backtracking(n, matrice, mod, timp_max, y_max)
├── nearest_neighbor.py   # rezolva_tsp_nn, rezolva_tsp_nn_multistart, rezolva_tsp_nn_timp
├── nn_aima.py            # rezolva_tsp_nn_aima, rezolva_tsp_nn_aima_multistart
└── performance.py        # ruleaza_experiment(), genereaza_grafice()
```

**Exemple de apel din linia de comandă:**

```bash
# Modul 'prima' - prima solutie gasita
python main.py orase.txt --mod prima

# Modul 'toate' - solutie optima garantata
python main.py orase.txt --mod toate

# Modul 'timp' - cea mai buna solutie dupa 60 secunde
python main.py orase.txt --mod timp --timp 60

# Modul 'y_solutii' - cea mai buna din primele 10 solutii
python main.py orase.txt --mod y_solutii --y 10
```

**Cerințe specifice:**

- Afișarea finală va include: mărimea problemei N, traseul optim găsit, costul minim, numărul de soluții găsite și timpul de execuție.

---

### 7.2 Sarcina B - Nearest neighbor manual și aima-python în același proiect

Adăugați în proiectul de la Sarcina A modulele `nearest_neighbor.py` și `nn_aima.py`:

**`nearest_neighbor.py`** va conține:
- `rezolva_tsp_nn(n, matrice, start=0)` - varianta de bază (modul `prima` / prima soluție)
- `rezolva_tsp_nn_multistart(n, matrice)` - modul `y_solutii` cu Y = N starturi
- `rezolva_tsp_nn_timp(n, matrice, timp_max)` - modul `timp`

**`nn_aima.py`** va conține:
- `rezolva_tsp_nn_aima(n, matrice, start=0)` - wrapper peste `nearest_neighbor_tsp` din aima3
- `rezolva_tsp_nn_aima_multistart(n, matrice)` - multistart cu aima3

**Cerințe specifice:**

- Toate funcțiile publice vor returna tupluri `(traseu, cost)` sau `(best_traseu, best_cost, ...)` pentru a permite compararea directă cu backtracking.
- Verificați că implementarea manuală (NN) și cea din aima3 returnează aceleași rezultate pe aceleași instanțe.
- Adăugați la `main.py` opțiunea `--algoritm [bt|nn|nn_aima]` pentru a selecta algoritmul.

---

### 7.3 Sarcina C - Grafice de performanță

Implementați în `performance.py` un experiment comparativ - **o diagramă XY sau bar chart** care compară **timpul de rezolvare** pentru **4 valori ale lui N** pentru **cazurile a) și c)** din ambele implementări.

**Protocol experimental:**

- Generați instanțe TSP aleatoare pentru N: `5, 8, 10, 12` (valori unde ambii algoritmi sunt comparabili).
- Adăugați `15, 20, 30, 50` **exclusiv** pentru NN (backtracking devine prohibitiv).
- Distanțele se generează aleatoriu ca întregi în `[1, 100]`, matrice simetrică. Folosiți un seed fix (`random.seed(42)`) pentru reproductibilitate.
- Măsurați timpii cu `time.perf_counter()`.

---

**Grafic 1 - Timp de rulare (cerință minimă)**

Graficul principal: compararea timpilor de execuție pentru cazul **a) (prima soluție / un singur start)** și cazul **c) (Y soluții / multistart cu Y=N)**.

```python
def ruleaza_experiment():
    """Ruleaza experimentul comparativ si genereaza graficul de performanta.

    Masoara timpii de executie pentru backtracking (modurile 'prima' si 'y_solutii')
    si NN (varianta de baza si multistart) pe instante aleatoare de dimensiuni variabile.
    Genereaza un grafic XY cu doua subploturi (scala liniara si logaritmica).
    """
    import random
    import time
    import matplotlib.pyplot as plt
    from backtracking import rezolva_tsp_backtracking
    from nearest_neighbor import rezolva_tsp_nn, rezolva_tsp_nn_multistart

    valori_n_bt = [5, 8, 10, 12]
    valori_n_nn = [5, 8, 10, 12, 15, 20, 30, 50]

    random.seed(42)     # :)

    # Genereaza instante si masoara timpii
    # ...
    # Genereaza grafic cu doua subploturi (linear + logaritmic)
    # Salveaza ca 'comparare_performanta.png'
```

---

**Grafic 2 - Calitate pentru timp fix T (analiză suplimentară)**

Ambii algoritmi rulează T minute (ex. T = 1, 2, 5 min) pe aceeași instanță (N = 15–20). Se compară costul soluției obținute.

- Backtracking: returnează cel mai bun tur găsit în T minute (îmbunătățire progresivă).
- NN multistart: returnează cel mai bun tur din runurile efectuate în T minute (instantaneu pentru NN).
- Grafic de tip bar chart: axă X = T (minute), axă Y = costul soluției. Demonstrează că NN obține o soluție bună imediat, iar backtracking-ul îmbunătățește progresiv.

---

**Grafic 3 - Gap față de optim (analiză suplimentară)**

Calculabil pentru N mic unde backtracking exhaustiv garantează optimul: N = 5, 7, 8, 10, 12.

```
gap% = (cost_NN - cost_BT_optim) / cost_BT_optim × 100
```

- Rulați BT (modul `toate`) și NN multistart pe aceleași instanțe.
- Grafic XY: axă X = N, axă Y = gap%.
- **De ce este util:** cuantifică "prețul vitezei" - cât sacrificăm din calitate pentru câștigul exponențial de viteză al NN față de BT exhaustiv.
- **Ce să observați:** gap% variază în funcție de instanță; pentru unele instanțe NN găsește optimul (gap=0%), pentru altele gap poate fi 20–30%.

---

**Structura funcțiilor din `performance.py`:**

```python
def genereaza_matrice_aleatorie(n, seed=None):
    """Genereaza o matrice de distante NxN simetrica cu valori in [1, 100]."""

def masoara_timp_bt(n, matrice, mod, **kwargs):
    """Masoara timpul de executie pentru backtracking pe o instanta data."""

def masoara_timp_nn(n, matrice, multistart=False):
    """Masoara timpul de executie pentru NN pe o instanta data."""

def ruleaza_experiment():
    """Ruleaza experimentul principal: timpi de executie pentru mai multe N."""

def genereaza_grafic_timpi(date):
    """Genereaza graficul 1 (timpi de rulare) si il salveaza ca PNG."""

def genereaza_grafic_calitate(date):
    """Genereaza graficul 2 (calitate la timp fix) si il salveaza ca PNG."""

def genereaza_grafic_gap(date):
    """Genereaza graficul 3 (gap% fata de optim) si il salveaza ca PNG."""
```

---

## 8. Bibliografie

\[1\] Stuart Russell, Peter Norvig - *Artificial Intelligence: A Modern Approach*, ediția a 4-a, Pearson, 2020.
ISBN 978-0-13-468599-1. *(Capitolul 4: Search in Complex Environments - algoritmii de căutare locală și constructivă)*

\[2\] Gilles Reinelt - *The Traveling Salesman: Computational Solutions for TSP Applications*, Springer, 1994.
ISBN 978-3-540-58334-0. *(Referință pentru euristici TSP, inclusiv Nearest Neighbor și analiza gap-ului)*

\[3\] Sursa GitHub aima-python (implementarea oficială AIMA):
https://github.com/aimacode/aima-python

\[4\] Documentație `aima3` (pachet PyPI):
https://pypi.org/project/aima3/

\[5\] Nils J. Nilsson - *Principles of Artificial Intelligence*, Tioga Publishing Co., Palo Alto, CA, 1980, 476 pagini. ISBN 0-935382-01.
Online: https://archive.org/details/principlesofarti00nils

\[6\] Laborator \#03 - *Problema Comis-Voiajorului: Backtracking și Algoritmul Alpinistului* (`ia_lab_03_hc.md`).
*(Referință pentru formatul fișierului de intrare, implementarea de backtracking de bază și compararea cu hill climbing)*
