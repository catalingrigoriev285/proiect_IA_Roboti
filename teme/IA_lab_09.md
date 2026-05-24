# Laborator 09 - Algoritmi genetici: Rezolvarea problemei comis-voiajorului (TSP)

---

## Cuprins

- [Laborator 09 - Algoritmi genetici: rezolvarea problemei comis-voiajorului (TSP)](#laborator-09---algoritmi-genetici-rezolvarea-problemei-comis-voiajorului-tsp)
  - [Cuprins](#cuprins)
  - [1. Obiectivele lucrării](#1-obiectivele-lucrării)
  - [2. Algoritmi evolutivi și genetici](#2-algoritmi-evolutivi-și-genetici)
    - [2.1 Concepte de bază](#21-concepte-de-bază)
    - [2.2 Etapele unui algoritm genetic](#22-etapele-unui-algoritm-genetic)
    - [2.3 Problema comis-voiajorului (TSP)](#23-problema-comis-voiajorului-tsp)
    - [2.4 Reprezentarea TSP în algoritmi genetici](#24-reprezentarea-tsp-în-algoritmi-genetici)
      - [Cromozomul - codificarea ca permutare](#cromozomul---codificarea-ca-permutare)
      - [Funcția de fitness pentru TSP](#funcția-de-fitness-pentru-tsp)
  - [3. Pseudocod și schemă logică](#3-pseudocod-și-schemă-logică)
  - [4. Parametrii unui AG și impactul lor](#4-parametrii-unui-ag-și-impactul-lor)
    - [`sol_per_pop` - Mărimea populației](#sol_per_pop---mărimea-populației)
    - [`num_generations` - Numărul de generații](#num_generations---numărul-de-generații)
    - [`mutation_percent_genes` - Rata de mutație](#mutation_percent_genes---rata-de-mutație)
    - [`crossover_type` - Tipul de crossover](#crossover_type---tipul-de-crossover)
    - [`parent_selection_type` - Tipul de selecție a părinților](#parent_selection_type---tipul-de-selecție-a-părinților)
    - [`keep_elitism` - Elitismul](#keep_elitism---elitismul)
    - [`K_tournament` - Dimensiunea turneului](#k_tournament---dimensiunea-turneului)
    - [`crossover_probability` - Probabilitatea de crossover](#crossover_probability---probabilitatea-de-crossover)
  - [5. Curba de convergență](#5-curba-de-convergență)
    - [Cum se construiește](#cum-se-construiește)
    - [Cum se interpretează](#cum-se-interpretează)
    - [Utilitate pedagogică](#utilitate-pedagogică)
  - [6. Implementare cu PyGAD](#6-implementare-cu-pygad)
    - [6.1 Instalare și prezentare generală](#61-instalare-și-prezentare-generală)
    - [6.2 Strategii pentru TSP: crossover personalizat vs. penalizare fitness](#62-strategii-pentru-tsp-crossover-personalizat-vs-penalizare-fitness)
      - [Abordarea recomandată: Crossover personalizat - Order Crossover (OX)](#-abordarea-recomandată-crossover-personalizat---order-crossover-ox)
      - [Abordarea alternativă: Penalizare în funcția de fitness](#️-abordarea-alternativă-penalizare-în-funcția-de-fitness)
    - [6.3 Exemplu complet de implementare](#63-exemplu-complet-de-implementare)
  - [7. Sarcini practice](#7-sarcini-practice)
    - [Sarcina 1 - Rulare primară](#sarcina-1---rulare-primară)
    - [Sarcina 2 - Studiul mărimii populației](#sarcina-2---studiul-mărimii-populației)
    - [Sarcina 3 - Studiul ratei de mutație](#sarcina-3---studiul-ratei-de-mutație)
    - [Sarcina 4 - Studiul tipului de selecție](#sarcina-4---studiul-tipului-de-selecție)
    - [Sarcina 5 - Scalabilitate](#sarcina-5---scalabilitate)
    - [Sarcina 6 (opțional) - Heatmap de parametri](#sarcina-6-opțional---heatmap-de-parametri)
  - [8. Notă: biblioteca DEAP](#8-notă-biblioteca-deap)
  - [9. Bibliografie](#9-bibliografie)

---

## 1. Obiectivele lucrării

Prin parcurgerea acestui laborator veți:

- înțelege principiile **algoritmilor evolutivi** și genetici;
- cunoaște etapele unui algoritm genetic: reprezentare, fitness, selecție, crossover, mutație;
- implementa rezolvarea **Problemei Comis-Voiajorului (TSP)** cu biblioteca **PyGAD**;
- analiza impactul parametrilor (mărimea populației, rata de mutație, tipul de crossover/selecție, numărul de generații) asupra calității soluției și a timpului de execuție;
- genera și interpreta **grafice de convergență** și de comparație a performanței.

---

## 2. Algoritmi evolutivi și genetici

### 2.1 Concepte de bază

**Algoritmii evolutivi** sunt o familie de metaheuristici inspirate din procesele biologice de evoluție naturală. Ei nu garantează soluția optimă globală, dar oferă soluții de bună calitate în timp rezonabil pentru probleme NP-dificile, unde metodele exacte (backtracking, programare dinamică) devin impracticabile.

**Algoritmul genetic (AG)** este cel mai cunoscut tip de algoritm evolutiv. Modelul său urmează teoria evoluției propusă de Darwin: indivizii mai bine adaptați au șanse mai mari de a supraviețui și de a se reproduce, transmițând caracteristicile lor urmașilor.

| Concept biologic | Corespondent în algoritmul genetic |
|---|---|
| Individ | Soluție candidată la problemă |
| Cromozom | Codificarea completă a soluției (vector/listă) |
| Genă | O componentă elementară a soluției |
| Populație | Mulțimea soluțiilor candidate din iterația curentă |
| Fitness | Scorul de calitate al unei soluții |
| Selecție | Alegerea soluțiilor-părinți cu fitness ridicat |
| Crossover | Recombinarea a doi cromozomi pentru a produce urmași |
| Mutație | Modificare aleatoare a unor gene ale urmașilor |
| Generație | O iterație completă a algoritmului |

Ideea centrală: **soluțiile mai bune au șanse mai mari să se reproducă**, transmițând genele lor generațiilor viitoare. Treptat, calitatea medie a populației crește, până când se găsește o soluție suficient de bună (sau se atinge condiția de oprire).

Spre deosebire de metodele de căutare exhaustivă, un AG explorează simultan multiple zone ale spațiului de soluții prin intermediul populației, evitând (parțial) blocarea în optimi locali. Totuși, convergența prematură într-un optim local rămâne un risc care se gestionează prin mutație și diversitate genetică adecvată.

### 2.2 Etapele unui algoritm genetic

1. **Inițializare** - Generarea aleatoare a unei populații inițiale de soluții candidate.
2. **Evaluare** - Calculul valorii de fitness pentru fiecare individ din populație.
3. **Selecție** - Alegerea indivizilor cu fitness mai bun ca părinți pentru generația următoare.
4. **Crossover (recombinare)** - Combinarea a doi părinți pentru a produce urmași (descendenți).
5. **Mutație** - Modificarea aleatoare a unor gene ale descendenților (menținând diversitatea genetică).
6. **Înlocuire** - Formarea noii generații (de regulă: elitism + descendenți noi).
7. **Verificare condiție de oprire** - Dacă numărul maxim de generații sau pragul de fitness a fost atins, algoritmul se oprește; altfel, se revine la pasul 2.

### 2.3 Problema comis-voiajorului (TSP)

**Enunț:** Dat un set de N orașe și distanțele (sau costurile) dintre fiecare pereche de orașe, găsiți **ruta de cost minim** care vizitează fiecare oraș exact o dată și se întoarce la orașul de start.

**Complexitate:** TSP este o problemă **NP-completă**. Numărul de rute distincte posibile este (N−1)!/2, ceea ce face căutarea exhaustivă imposibilă pentru N mai mare de ~20:

| N (orașe) | Rute posibile | Fezabilitate brute-force |
|---|---|---|
| 10 | 181.440 | câteva secunde |
| 20 | ≈ 6 × 10¹⁶ | milioane de ani |
| 50 | astronomic | imposibil practic |

**Funcția obiectiv (de minimizat):**

```
distanță_totală(rută) = Σ dist(rută[i], rută[i+1])   pentru i = 0..N−2
                      + dist(rută[N−1], rută[0])       (întoarcere la start)
```

TSP modelează numeroase probleme reale: rutarea vehiculelor de livrare, planificarea traseelor de producție, secvențierea genomică, proiectarea circuitelor PCB etc.

### 2.4 Reprezentarea TSP în algoritmi genetici

#### Cromozomul - codificarea ca permutare

Pentru TSP, un cromozom este o **permutare** a indicilor celor N orașe. Fiecare genă este un indice de oraș; ordinea genelor definește ruta.

```
Exemplu (6 orașe: 0, 1, 2, 3, 4, 5):

Cromozom:   [2,  0,  4,  1,  3,  5]
Ruta:        2 → 0 → 4 → 1 → 3 → 5 → 2   (revenire la start)
```

**Constrângerea esențială:** fiecare oraș apare **exact o dată** în cromozom. Operatorii de crossover și mutație trebuie să respecte această constrângere; altfel, se produc rute invalide (cu orașe duplicate sau lipsă), care nu pot fi evaluate direct.

#### Funcția de fitness pentru TSP

Deoarece PyGAD **maximizează** fitness-ul, iar noi dorim să **minimizăm** distanța, definim:

```
fitness(cromozom) = −distanță_totală(ruta codificată de cromozom)
```

Cu cât distanța e mai mică, cu atât fitness-ul (negativ) e mai aproape de zero → mai bun.

---

## 3. Pseudocod și schemă logică

```
ALGORITM Genetic_TSP(orașe, pop_size, n_generații, rată_mutație, n_elită):

  PRELUCRARE INIȚIALĂ:
    dist_matrix ← calculează_matrice_distanțe(orașe)
    populație   ← generează_permutări_aleatoare(pop_size, |orașe|)
    evaluează_fitness(populație, dist_matrix)

  REPETĂ de n_generații ori:

    ┌─ SELECȚIE:
    │    părinți ← selectează_prin_turneu(populație, fitness)
    │
    ├─ CROSSOVER - Order Crossover (OX):
    │    pentru fiecare pereche (p1, p2) din părinți:
    │      (cx1, cx2) ← două puncte aleatoare de tăiere (cx1 < cx2)
    │      copil[cx1..cx2] ← p1[cx1..cx2]
    │      completează_restul_cu_gene_din(p2, omite_duplicatele)
    │      → copil este mereu o permutare validă
    │
    ├─ MUTAȚIE - Swap Mutation:
    │    pentru fiecare copil:
    │      dacă random() < rată_mutație:
    │        (i, j) ← două poziții aleatoare
    │        schimbă copil[i] ↔ copil[j]
    │        → constrângerea de permutare se menține
    │
    └─ ÎNLOCUIRE (elitism):
         noua_populație ← top_n_elită(populație_curentă) + descendenți
         evaluează_fitness(noua_populație, dist_matrix)

  RETURNEAZĂ cromozomul cu fitness maxim din populație
```

**Schemă logică:**

```
         [START]
            │
            ▼
  ┌─────────────────────────┐
  │  Generează populație    │
  │  inițială (permutări    │
  │  aleatoare)             │
  └─────────┬───────────────┘
            │
            ▼
  ┌─────────────────────────┐
  │  Evaluează fitness      │◄──────────────────────┐
  │  fiecărui individ       │                       │
  └─────────┬───────────────┘                       │
            │                                       │
            ▼                                       │
  ┌─────────────────────────┐    DA                 │
  │  Condiție de oprire?    │──────────────►  [STOP / Returnează]
  └─────────┬───────────────┘                  cel mai bun
            │ NU                               cromozom
            ▼
  ┌─────────────────────────┐
  │  Selecție părinți       │
  │  (turneu / ruletă)      │
  └─────────┬───────────────┘
            │
            ▼
  ┌─────────────────────────┐
  │  Crossover OX           │
  │  → offspring valizi     │
  └─────────┬───────────────┘
            │
            ▼
  ┌─────────────────────────┐
  │  Swap Mutation          │
  │  (cu probabilitate p)   │
  └─────────┬───────────────┘
            │
            ▼
  ┌─────────────────────────┐
  │  Înlocuire generație    │
  │  (elitism + offspring)  │
  └─────────┬───────────────┘
            │
            └──────────────────────────────────────►(înapoi la evaluare)
```

---

## 4. Parametrii unui AG și impactul lor

### `sol_per_pop` - Mărimea populației

**Ce controlează:** numărul total de soluții candidate menținute simultan în fiecare generație.

**Impact:**
- **Valori mici** (20–50): convergență rapidă per generație, dar **diversitate redusă** → risc crescut de blocare în optim local; soluția finală poate fi suboptimă.
- **Valori mari** (200–500): explorare mai bogată a spațiului de soluții, șanse mai bune de a evita optimele locale, dar **fiecare generație durează mai mult** → tradeoff cu timpul de execuție.
- **Recomandare:** 50–200 pentru probleme cu 10–50 de orașe.

---

### `num_generations` - Numărul de generații

**Ce controlează:** numărul total de iterații ale ciclului GA.

**Impact:**
- **Prea mic:** algoritmul se oprește înainte de convergență → soluții suboptime.
- **Prea mare:** timp irosit după atingerea platoului (nu mai există îmbunătățiri semnificative).
- **Recomandare:** Monitorizați curba de convergență și stabiliți numărul de generații astfel încât platoul să fie atins. Valori tipice: 300–2000 generații, în funcție de complexitatea problemei.

---

### `mutation_percent_genes` - Rata de mutație

**Ce controlează:** în contextul mutației swap personalizate implementate, este utilizat ca **probabilitatea că un cromozom primit va fi supus mutației** (valoare în interval 0–100, interpretată ca procent).

**Impact:**
- **Prea mică** (5–15%): algoritm greedy, fără diversificare suficientă → **convergență prematură** în optim local; curba de convergență stagnează devreme.
- **Optimă** (30–60%): echilibru bun între exploatare (îmbunătățirea soluțiilor bune) și explorare (diversificare).
- **Prea mare** (85–100%): comportament aproape aleatoriu; mutațiile frecvente distrug structuri bune → fitness-ul oscilează, fără progres sistematic.
- **Recomandare:** Testați în intervalul 20–70% și observați forma curbei de convergență.

---

### `crossover_type` - Tipul de crossover

**Ce controlează:** strategia de combinare a cromozomilor părinți pentru a produce urmași.

Operatorii **standard** din PyGAD (`single_point`, `two_points`, `uniform`) nu respectă constrângerea de permutare și **nu sunt utilizabili direct pentru TSP**. Pentru TSP se folosește un operator **personalizat** (detalii în secțiunea 6.2).

| Operator | Descriere | TSP-valid? |
|---|---|---|
| `single_point` | Un singur punct de tăiere | ✗ (produce duplicate) |
| `two_points` | Două puncte de tăiere | ✗ |
| `uniform` | Fiecare genă e aleasă de la un părinte | ✗ |
| **OX** (custom) | Order Crossover - păstrează ordinea relativă | ✓ |
| **PMX** (custom) | Partially Mapped Crossover - mapare parțială | ✓ |

**OX vs. PMX pentru TSP:** OX păstrează ordinea relativă a orașelor → exploatare mai eficientă a structurii rutelor; PMX introduce mai multă varianță genetică și poate fi mai util dacă OX converge prematur.

---

### `parent_selection_type` - Tipul de selecție a părinților

**Ce controlează:** cum sunt aleși părinții din populația curentă pentru a participa la crossover.

| Valoare | Metodă | Comportament |
|---|---|---|
| `"tournament"` | Turneu | Selectiv și robust; `K_tournament` controlează presiunea selectivă |
| `"rws"` | Roulette Wheel | Proporțional cu fitness-ul; risc de dominanță dacă fitness-urile variază mult |
| `"rank"` | Rank-based | Proporțional cu rangul (nu cu valoarea); mai stabil decât RWS |
| `"sus"` | Stochastic Universal Sampling | Variantă îmbunătățită a ruletei; distribuție mai uniformă a selecțiilor |
| `"sss"` | Steady-State | Înlocuire graduală; convergență lentă dar stabilă |

**Recomandare pentru TSP:** `"tournament"` cu `K_tournament=3` oferă un echilibru bun.

---

### `keep_elitism` - Elitismul

**Ce controlează:** numărul celor mai buni indivizi din generația curentă care trec **nemodificați** în generația următoare.

**Impact:**
- **0:** fără elitism → cea mai bună soluție descoperită poate fi pierdută între generații.
- **1–5:** protejează soluțiile de top; garantează că fitness-ul celei mai bune soluții nu scade niciodată.
- **Prea mare:** populația stagnează, diversitate redusă → convergență prematură.
- **Recomandare:** 1–3.

---

### `K_tournament` - Dimensiunea turneului

**Ce controlează:** numărul de candidați aleatori extrași din populație dintr-un singur turneu; câștigătorul (cel cu fitness mai bun) devine părinte.

**Impact:**
- **K=2:** presiune selectivă redusă → mai multă diversitate, convergență mai lentă.
- **K=5–10:** presiune ridicată → converge rapid spre elită, dar pierde diversitate.

---

### `crossover_probability` - Probabilitatea de crossover

**Ce controlează:** probabilitatea că o pereche de părinți selectată va produce efectiv un descendent prin crossover (vs. copie directă a unui părinte).

**Impact:** Valori tipice 0.7–0.95. Valoarea 1.0 înseamnă că crossover-ul se aplică mereu.

---

## 5. Curba de convergență

**Curba de convergență** (*convergence curve*) este un grafic care vizualizează **evoluția calității celei mai bune soluții** pe măsură ce algoritmul parcurge generațiile.

### Cum se construiește

- **Axa X (orizontală):** numărul generației (iterației).
- **Axa Y (verticală):** valoarea fitness-ului sau, mai intuitiv pentru TSP, **distanța totală a celei mai bune rute** din acea generație.

PyGAD salvează automat valorile fitness ale celei mai bune soluții per generație în atributul `ga_instance.best_solutions_fitness` - un vector cu `num_generations + 1` valori (include și starea populației inițiale, generația 0).

### Cum se interpretează

```
Distanță
totală
  ↑
  │ ●
  │  ●●
  │    ●●
  │      ●●●
  │         ●●●●
  │             ●●●●●●
  │                   ●●●●●●●●●●●●●●●●  ← platou
  └──────────────────────────────────────→ Generație
     [explorare]       [exploatare]  [stagnare]
```

- **Faza de descreștere rapidă (explorare):** în primele generații, algoritmul descoperă soluții semnificativ mai bune la fiecare pas - spațiul de căutare este explorat agresiv.
- **Faza de descreștere lentă (exploatare):** îmbunătățirile devin marginale; algoritmul rafinează soluțiile bune deja descoperite.
- **Platoul (stagnare):** nu mai există îmbunătățiri - algoritmul a converge. Dacă platoul apare devreme (ex. după 50 din 500 de generații), poate indica un **optim local** → creșteți rata de mutație sau mărimea populației.
- **Oscilații puternice:** rata de mutație e prea mare - algoritmul se comportă aleatoriu.

### Utilitate pedagogică

Suprapunând curbele de convergență pentru configurații diferite pe același grafic, puteți vizualiza imediat:
- care configurație **converge mai rapid**;
- care configurație ajunge la **soluții mai bune** (distanță finală mai mică);
- dacă un algoritm s-a **blocat în optim local** (platou prematur).

---

## 6. Implementare cu PyGAD

### 6.1 Instalare și prezentare generală

```bash
pip install pygad matplotlib numpy
```

**PyGAD** este o bibliotecă Python matură și bine documentată pentru algoritmi genetici. Permite configurarea completă a parametrilor GA și suportă funcții de fitness, crossover și mutație **personalizate** - esențiale pentru TSP.

Documentație oficială: https://pygad.readthedocs.io/en/latest/

### 6.2 Strategii pentru TSP: crossover personalizat vs. penalizare fitness

**Problema centrală:** TSP necesită cromozomi de tip **permutare** (fiecare oraș apare exact o dată). Operatorii standard de crossover nu respectă această constrângere și produc soluții invalide cu orașe duplicate sau lipsă.

Există două abordări pentru a rezolva această problemă:

---

#### Abordarea recomandată: Crossover personalizat - Order Crossover (OX)

Implementăm un operator OX care, **prin construcție**, produce mereu permutări valide - nu există soluții invalide în populație.

**Cum funcționează OX (pas cu pas):**

1. Se aleg două puncte de tăiere aleatorii `cx1` și `cx2` (unde `cx1 < cx2`).
2. Se copiază segmentul `parent1[cx1 .. cx2]` direct în copil, la aceleași poziții.
3. Pozițiile rămase libere se completează cu genele din `parent2`, în **ordinea în care apar** în `parent2`, **omițând** genele deja prezente în copil.

**Exemplu vizual:**

```
parent1:  [3,  1,  | 4,  0,  2 |  5]     cx1=2, cx2=4
parent2:  [5,  4,    2,  3,  0,   1]

Pasul 1 - copiez segmentul din parent1:
  copil:  [_,  _,    4,  0,  2,   _]

Pasul 2 - gene din parent2 în ordine: 5, 4, 2, 3, 0, 1
  Omit:  4 (deja în copil), 2 (deja), 0 (deja)
  Rămân: 5, 3, 1   → completez pozițiile libere (0, 1, 5)

Copil final:  [5,  3,  4,  0,  2,  1]   ← permutare validă ✓
```

**Avantaje:**
- Cromozomii descendenți sunt **mereu valizi** → nicio soluție invalidă nu intră în populație.
- Exploatare eficientă a structurii rutelor (ordinea relativă a orașelor este parțial păstrată).
- Operator recomandat pentru TSP în literatura de specialitate.

**Dezavantaj:** Necesită implementare manuală (nu e built-in în PyGAD pentru permutări).

---

#### Abordarea alternativă: Penalizare în funcția de fitness

Se permit cromozomii invalizi (cu duplicate), dar aceștia sunt **penalizați** prin funcția de fitness:

```python
def fitness_penalizare(ga_instance, solutie, idx):
    n_unice = len(set(solutie.astype(int)))
    nr_duplicate = N_ORASE - n_unice
    penalizare = nr_duplicate * 10_000   # factor de penalizare calibrat manual

    distanta = distanta_ruta_simpla(solutie)   # calculează chiar dacă e invalidă
    return -(distanta + penalizare)
```

**De ce nu este recomandată ca abordare principală:**

1. **Ineficiență:** Generațiile inițiale sunt populate cu soluții invalide → resurse computaționale irosite pentru evaluarea și procesarea lor.
2. **Calibrare dificilă:** Factorul de penalizare trebuie ales cu grijă. Prea mic → soluțiile invalide „trec" de filtru; prea mare → presiune selectivă distorsionată, algoritmul evită chiar soluțiile parțial bune cu un singur duplicat.
3. **Convergență mai lentă:** Algoritmul „pierde timp" eliminând soluțiile invalide în loc să exploreze direct spațiul soluțiilor valide.
4. **Risc de soluție finală invalidă:** Dacă penalizarea nu este suficient de mare, soluția returnată poate fi ea însăși invalidă.

**Când poate fi utilă:** prototipare rapidă, probleme unde constrângerea este „soft" sau când nu se dorește implementarea unui operator custom.

---

### 6.3 Exemplu complet de implementare

Salvați codul următor ca `tsp_genetic.py` și rulați-l cu `python tsp_genetic.py`.

```python
# tsp_genetic.py - Rezolvarea TSP cu algoritmi genetici (PyGAD)
import pygad
import numpy as np
import matplotlib.pyplot as plt
import random
import time

# ══════════════════════════════════════════════════════════════════
# 1. DEFINIREA PROBLEMEI - ORAȘE ȘI DISTANȚE
# ══════════════════════════════════════════════════════════════════

# Coordonate aproximative (x, y) în km față de un punct de referință
ORASE = {
    0: ("Cluj-Napoca",  (0,    0   )),
    1: ("Brasov",       (220, -130 )),
    2: ("Bucuresti",    (330, -175 )),
    3: ("Timisoara",    (-175, -75 )),
    4: ("Iasi",         (380,   55 )),
    5: ("Constanta",    (450, -225 )),
    6: ("Craiova",      (160, -230 )),
    7: ("Galati",       (430,  -55 )),
    8: ("Oradea",       (-95,   45 )),
    9: ("Sibiu",        (95,   -95 )),
}

N_ORASE = len(ORASE)
COORD = np.array([ORASE[i][1] for i in range(N_ORASE)], dtype=float)
NUME_ORASE = [ORASE[i][0] for i in range(N_ORASE)]


def calculeaza_matrice_distante(coord):
    """Calculează matricea de distanțe euclidiene între toate perechile de orașe."""
    n = len(coord)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dx = coord[i][0] - coord[j][0]
            dy = coord[i][1] - coord[j][1]
            dist[i][j] = np.sqrt(dx**2 + dy**2)
    return dist


DIST_MATRIX = calculeaza_matrice_distante(COORD)


def distanta_ruta(solutie):
    """Calculează distanța totală a unei rute (ciclu complet, revenire la start)."""
    total = 0.0
    n = len(solutie)
    for i in range(n):
        total += DIST_MATRIX[int(solutie[i])][int(solutie[(i + 1) % n])]
    return total


# ══════════════════════════════════════════════════════════════════
# 2. FUNCȚIA DE FITNESS
# ══════════════════════════════════════════════════════════════════

def fitness_func(ga_instance, solutie, solutie_idx):
    """PyGAD maximizează fitness-ul → returnăm negativul distanței."""
    return -distanta_ruta(solutie)


# ══════════════════════════════════════════════════════════════════
# 3. OPERATORI PERSONALIZAȚI - CROSSOVER ȘI MUTAȚIE
# ══════════════════════════════════════════════════════════════════

def ox_crossover(parinti, offspring_size, ga_instance):
    """
    Order Crossover (OX): produce mereu permutări valide din doi părinți.

    Algoritmul:
    1. Copiază segmentul [cx1..cx2] din parent1 în copil.
    2. Completează pozițiile libere cu genele din parent2 (în ordinea lor),
       omițând genele deja prezente în copil.
    """
    offspring = []
    idx = 0
    while len(offspring) < offspring_size[0]:
        p1 = parinti[idx % parinti.shape[0]].astype(int).tolist()
        p2 = parinti[(idx + 1) % parinti.shape[0]].astype(int).tolist()
        n = len(p1)

        cx1, cx2 = sorted(random.sample(range(n), 2))

        copil = [-1] * n
        copil[cx1:cx2 + 1] = p1[cx1:cx2 + 1]

        set_segment = set(copil[cx1:cx2 + 1])
        gene_ramase = [g for g in p2 if g not in set_segment]
        pozitii_libere = [i for i in range(n) if copil[i] == -1]

        for pos, gena in zip(pozitii_libere, gene_ramase):
            copil[pos] = gena

        offspring.append(copil)
        idx += 1

    return np.array(offspring, dtype=int)


def swap_mutation(offspring, ga_instance):
    """
    Swap Mutation: cu probabilitate rata_mutatie, schimbă două gene aleatoare.
    Constrângerea de permutare este menținută prin construcție.
    """
    rata = ga_instance.mutation_percent_genes / 100.0
    for i in range(offspring.shape[0]):
        if random.random() < rata:
            n = offspring.shape[1]
            idx1, idx2 = random.sample(range(n), 2)
            temp = int(offspring[i][idx1])
            offspring[i][idx1] = offspring[i][idx2]
            offspring[i][idx2] = temp
    return offspring


# ══════════════════════════════════════════════════════════════════
# 4. GENERARE POPULAȚIE INIȚIALĂ
# ══════════════════════════════════════════════════════════════════

def genereaza_populatie(pop_size, n_orase):
    """Generează pop_size permutări aleatoare distincte ale celor n_orase orașe."""
    pop = []
    for _ in range(pop_size):
        perm = list(range(n_orase))
        random.shuffle(perm)
        pop.append(perm)
    return np.array(pop, dtype=int)


# ══════════════════════════════════════════════════════════════════
# 5. RULAREA ALGORITMULUI GENETIC
# ══════════════════════════════════════════════════════════════════

def ruleaza_ga(pop_size=100, n_generatii=500, rata_mutatie=50,
               tip_selectie="tournament", k_tournament=3,
               keep_elitism=2, verbose=True):
    """
    Configurează și rulează GA pentru TSP cu parametrii specificați.
    Returnează: (instanța GA, distanța celei mai bune soluții, durata în secunde)
    """
    populatie_initiala = genereaza_populatie(pop_size, N_ORASE)

    ga_instance = pygad.GA(
        num_generations=n_generatii,
        num_parents_mating=max(2, pop_size // 2),
        fitness_func=fitness_func,
        initial_population=populatie_initiala,
        crossover_type=ox_crossover,
        mutation_type=swap_mutation,
        mutation_percent_genes=rata_mutatie,
        parent_selection_type=tip_selectie,
        K_tournament=k_tournament,
        keep_elitism=keep_elitism,
        keep_parents=0,
        suppress_warnings=True,
    )

    start = time.time()
    ga_instance.run()
    durata = time.time() - start

    solutie, fitness, _ = ga_instance.best_solution()
    distanta = -fitness

    if verbose:
        print(f"\n{'='*55}")
        print(f"Configurație: pop={pop_size}, gen={n_generatii}, mut={rata_mutatie}%")
        ruta_str = " → ".join(ORASE[int(c)][0] for c in solutie)
        print(f"Ruta: {ruta_str} → {ORASE[int(solutie[0])][0]}")
        print(f"Distanță totală: {distanta:.2f}")
        print(f"Timp execuție:   {durata:.2f}s")

    return ga_instance, distanta, durata


# ══════════════════════════════════════════════════════════════════
# 6. VIZUALIZARE
# ══════════════════════════════════════════════════════════════════

def plot_convergenta(ga_instance, titlu="Curba de convergență", ax=None):
    """
    Grafic: distanța celei mai bune soluții per generație (curba de convergență).
    Dacă ax este None, creează o figură nouă și o afișează.
    """
    distante = [-f for f in ga_instance.best_solutions_fitness]
    afiseaza_singur = ax is None
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(distante, color='steelblue', linewidth=1.5, label='Cea mai bună soluție')
    ax.set_xlabel("Generație")
    ax.set_ylabel("Distanță totală")
    ax.set_title(titlu)
    ax.grid(True, alpha=0.3)
    ax.legend()

    if afiseaza_singur:
        plt.tight_layout()
        plt.show()


def plot_ruta(solutie, titlu="Ruta găsită de AG"):
    """Grafic: harta orașelor cu ruta vizualizată prin săgeți."""
    solutie_int = [int(c) for c in solutie]
    ruta = solutie_int + [solutie_int[0]]

    fig, ax = plt.subplots(figsize=(12, 9))

    for i in range(len(ruta) - 1):
        x1, y1 = COORD[ruta[i]]
        x2, y2 = COORD[ruta[i + 1]]
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="steelblue", lw=2)
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, str(i + 1), fontsize=7, color='gray', ha='center')

    ax.scatter(COORD[:, 0], COORD[:, 1], s=150, c='tomato', zorder=5)
    for i in range(N_ORASE):
        x, y = COORD[i]
        ax.annotate(ORASE[i][0], (x, y),
                    textcoords="offset points", xytext=(10, 5), fontsize=9)

    distanta = distanta_ruta(solutie)
    ax.set_title(f"{titlu}\nDistanță totală: {distanta:.2f}")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 7. STUDIU DE PARAMETRI - EXEMPLU COMPLET
# ══════════════════════════════════════════════════════════════════

def studiu_parametri_populatie():
    """
    Sarcina 2: Compară configurații cu mărimi de populație diferite.
    Generează curbe de convergență suprapuse și grafic comparativ.
    """
    valori_pop = [20, 50, 100, 200]
    culori = ['tomato', 'steelblue', 'seagreen', 'darkorange']

    fig, axes = plt.subplots(1, 3, figsize=(22, 6))
    distante_finale = []
    durate = []

    for pop, culoare in zip(valori_pop, culori):
        ga, dist, durata = ruleaza_ga(
            pop_size=pop, n_generatii=300, rata_mutatie=40, verbose=False
        )
        distante_finale.append(dist)
        durate.append(durata)

        d = [-f for f in ga.best_solutions_fitness]
        axes[0].plot(d, color=culoare, linewidth=1.5, label=f"pop={pop}")

    axes[0].set_xlabel("Generație")
    axes[0].set_ylabel("Distanță totală")
    axes[0].set_title("Curbe de convergență - mărimi de populație diferite")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].bar([str(p) for p in valori_pop], distante_finale,
                color=culori, alpha=0.85)
    axes[1].set_xlabel("Mărimea populației (sol_per_pop)")
    axes[1].set_ylabel("Distanță finală (mai mică = mai bun)")
    axes[1].set_title("Distanță finală în funcție de mărimea populației")
    for j, (v, d) in enumerate(zip(valori_pop, distante_finale)):
        axes[1].text(j, d + 2, f"{d:.1f}", ha='center', va='bottom', fontsize=9)

    axes[2].bar([str(p) for p in valori_pop], durate, color=culori, alpha=0.85)
    axes[2].set_xlabel("Mărimea populației (sol_per_pop)")
    axes[2].set_ylabel("Timp de execuție (s)")
    axes[2].set_title("Timp de execuție în funcție de mărimea populației")
    for j, (v, t) in enumerate(zip(valori_pop, durate)):
        axes[2].text(j, t + 0.01, f"{t:.2f}s", ha='center', va='bottom', fontsize=9)

    plt.suptitle("Studiu: Impactul mărimii populației", fontsize=13)
    plt.tight_layout()
    plt.show()


def studiu_parametri_mutatie():
    """
    Sarcina 3: Compară configurații cu rate de mutație diferite.
    """
    valori_mut = [5, 20, 40, 60, 80, 95]
    culori = ['navy', 'royalblue', 'steelblue', 'seagreen', 'darkorange', 'tomato']

    fig, ax = plt.subplots(figsize=(12, 6))
    distante_finale = []

    for mut, culoare in zip(valori_mut, culori):
        ga, dist, _ = ruleaza_ga(
            pop_size=100, n_generatii=300, rata_mutatie=mut, verbose=False
        )
        distante_finale.append(dist)
        d = [-f for f in ga.best_solutions_fitness]
        ax.plot(d, color=culoare, linewidth=1.5, label=f"mut={mut}%")

    ax.set_xlabel("Generație")
    ax.set_ylabel("Distanță totală")
    ax.set_title("Curbe de convergență - rate de mutație diferite")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("\nRezultate studiu mutație:")
    for mut, dist in zip(valori_mut, distante_finale):
        print(f"  mut={mut:3d}%  →  distanță finală: {dist:.2f}")


def studiu_tip_selectie():
    """
    Sarcina 4: Compară strategii de selecție a părinților.
    """
    strategii = ["tournament", "rws", "rank", "sus"]
    culori = ['steelblue', 'tomato', 'seagreen', 'darkorange']

    fig, ax = plt.subplots(figsize=(12, 6))
    rezultate = []

    for strategie, culoare in zip(strategii, culori):
        ga, dist, durata = ruleaza_ga(
            pop_size=100, n_generatii=300, rata_mutatie=40,
            tip_selectie=strategie, verbose=False
        )
        rezultate.append({"strategie": strategie, "distanta": dist, "durata": durata})
        d = [-f for f in ga.best_solutions_fitness]
        ax.plot(d, color=culoare, linewidth=1.5, label=strategie)

    ax.set_xlabel("Generație")
    ax.set_ylabel("Distanță totală")
    ax.set_title("Curbe de convergență - strategii de selecție diferite")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("\n{:<15} {:>15} {:>12}".format("Strategie", "Distanță finală", "Timp (s)"))
    print("-" * 45)
    for r in rezultate:
        print(f"{r['strategie']:<15} {r['distanta']:>15.2f} {r['durata']:>12.2f}")


# ══════════════════════════════════════════════════════════════════
# 8. PUNCT DE INTRARE
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    print("=== Rulare de bază (pop=100, gen=500, mut=50%) ===")
    ga, dist, durata = ruleaza_ga(pop_size=100, n_generatii=500, rata_mutatie=50)
    solutie, _, _ = ga.best_solution()

    plot_convergenta(ga, titlu="Curba de convergență - configurație de bază")
    plot_ruta(solutie, titlu="Ruta găsită de algoritmul genetic")

    print("\n=== Studiu: impact mărime populație ===")
    studiu_parametri_populatie()

    print("\n=== Studiu: impact rată mutație ===")
    studiu_parametri_mutatie()

    print("\n=== Studiu: tip selecție părinți ===")
    studiu_tip_selectie()
```

---

## 7. Sarcini practice

Implementați și documentați toate sarcinile în Python (Jupyter Notebook sau script `.py`). Pentru fiecare sarcină, includeți codul, graficele generate și observațiile.

### Sarcina 1 - Rulare primară

Rulați codul de mai sus cu configurația implicită (`pop_size=100`, `n_generatii=500`, `rata_mutatie=50`). Raportați:
- Ruta găsită (cu numele orașelor)
- Distanța totală a rutei
- Timpul de execuție
- Graficul rutei vizualizate pe hartă
- Curba de convergență

### Sarcina 2 - Studiul mărimii populației

Rulați AG cu `n_generatii=300`, `rata_mutatie=40%`, variind `sol_per_pop` în: `[20, 50, 100, 200]`.

Generați:
- Grafic cu curbele de convergență suprapuse (câte o linie per configurație)
- Grafic cu distanța finală în funcție de `sol_per_pop`
- Grafic cu timpul de execuție în funcție de `sol_per_pop`

**Întrebare:** Care este tradeoff-ul dintre calitatea soluției și timpul de execuție?

### Sarcina 3 - Studiul ratei de mutație

Mențineți `pop_size=100`, `n_generatii=300`. Variați `rata_mutatie` în: `[5, 20, 40, 60, 80, 95]`.

Generați:
- Grafic cu curbele de convergență suprapuse
- Grafic: distanță finală în funcție de rata de mutație

**Întrebare:** Ce se observă la rate extreme (5% vs. 95%)? Cum se manifestă convergența prematură pe grafic?

### Sarcina 4 - Studiul tipului de selecție

Comparați strategiile: `["tournament", "rws", "rank", "sus"]` cu `pop_size=100`, `n_generatii=300`, `rata_mutatie=40%`.

Generați:
- Grafic cu curbele de convergență suprapuse
- Tabel comparativ: distanță finală, timp de execuție

### Sarcina 5 - Scalabilitate

Adăugați orașe suplimentare (15, 20, 25 de orașe) prin generare aleatoare de coordonate. Rulați AG cu configurația optimă identificată în sarcinile anterioare.

```python
import random

def genereaza_orase_aleatoare(n, seed=42):
    random.seed(seed)
    return {i: (f"Oras_{i}", (random.uniform(-500, 500), random.uniform(-300, 300)))
            for i in range(n)}
```

Generați:
- Grafic: distanță finală / număr de orașe
- Grafic: timp de execuție / număr de orașe

### Sarcina 6 (opțional) - Heatmap de parametri

Rulați o grilă de configurații (`pop_size` × `rata_mutatie`) și vizualizați rezultatele ca heatmap:

```python
import seaborn as sns  # pip install seaborn

valori_pop = [50, 100, 150, 200]
valori_mut = [20, 40, 60, 80]

rezultate = np.zeros((len(valori_pop), len(valori_mut)))
for i, pop in enumerate(valori_pop):
    for j, mut in enumerate(valori_mut):
        _, dist, _ = ruleaza_ga(pop_size=pop, n_generatii=200,
                                 rata_mutatie=mut, verbose=False)
        rezultate[i][j] = dist

plt.figure(figsize=(8, 6))
sns.heatmap(rezultate, xticklabels=valori_mut, yticklabels=valori_pop,
            annot=True, fmt=".1f", cmap="YlOrRd_r")
plt.xlabel("Rata de mutație (%)")
plt.ylabel("Mărimea populației")
plt.title("Heatmap: Distanța finală în funcție de parametri\n(mai mică = mai bun)")
plt.tight_layout()
plt.show()
```

---

## 8. Notă: biblioteca DEAP

**DEAP** (*Distributed Evolutionary Algorithms in Python*) este alternativa academică standard pentru algoritmi evolutivi în Python.

| Caracteristică | PyGAD | DEAP |
|---|---|---|
| Ușurință de utilizare | ★★★★★ | ★★★ |
| Documentație | Excelentă | Bună |
| Suport TSP (OX crossover built-in) | ✗ (implementare manuală) | ✓ (`tools.cxOrdered`) |
| Mutație swap built-in | ✗ (implementare manuală) | ✓ (`tools.mutShuffleIndexes`) |
| Flexibilitate algoritmică | Medie | Foarte mare |
| Algoritmi disponibili | GA clasic | GA, ES, GP, CMA-ES, NSGA-II etc. |
| Vizualizare convergență built-in | ✓ `plot_fitness()` | ✗ (manuală) |
| Instalare | `pip install pygad` | `pip install deap` |

**Exemplu minimal DEAP pentru TSP** (pentru referință):

```python
from deap import base, creator, tools, algorithms

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("indices", random.sample, range(N_ORASE), N_ORASE)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate",   tools.cxOrdered)                         # OX built-in
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)    # swap built-in
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", lambda ind: (distanta_ruta(ind),))

pop = toolbox.population(n=100)
algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.4, ngen=300, verbose=False)
best = tools.selBest(pop, k=1)[0]
```

**Concluzie:** DEAP oferă operatorii pentru TSP **built-in** (`cxOrdered`, `mutShuffleIndexes`), eliminând necesitatea implementării manuale. Totuși, API-ul său este semnificativ mai complex și necesită familiarizarea cu conceptele de `creator`, `toolbox` și `Fitness`. Absența vizualizării built-in a convergenței impune implementarea manuală a trackingului fitness-ului.

**Recomandare:** Utilizați PyGAD pentru acest laborator; explorați DEAP pentru proiecte de cercetare sau algoritmi evolutivi mai avansați (Genetic Programming, optimizare multi-obiectiv).

---

## 9. Bibliografie

1. **Adewole Philip, Akinwale A.T., Otunbanowo K.** - *A Genetic Algorithm for Solving Travelling Salesman Problem*, International Journal of Advanced Computer Science and Applications, Vol. 2, No. 1, pp. 26–29, 2011.

2. **GeeksForGeeks** - *Traveling Salesman Problem using Genetic Algorithm*, disponibil la: https://www.geeksforgeeks.org/dsa/traveling-salesman-problem-using-genetic-algorithm/ [accesat 2026]

3. **DataCamp** - *Genetic Algorithm in Python Tutorial*, disponibil la: https://www.datacamp.com/tutorial/genetic-algorithm-python [accesat 2026]

4. **PyGAD Documentation** - *PyGAD: An Intuitive Genetic Algorithm Python Library*, disponibil la: https://pygad.readthedocs.io/en/latest/ [accesat 2026]

5. **Holland, J.H.** - *Adaptation in Natural and Artificial Systems: An Introductory Analysis with Applications to Biology, Control, and Artificial Intelligence*, MIT Press, Cambridge, MA, 1992.

6. **Goldberg, D.E.** - *Genetic Algorithms in Search, Optimization, and Machine Learning*, Addison-Wesley Publishing Company, 1989.
