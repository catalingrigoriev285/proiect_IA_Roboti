# INTELIGENȚĂ ARTIFICIALĂ 2025-2026

# Laborator #06

---

## Cuprins

- [INTELIGENȚĂ ARTIFICIALĂ 2025-2026](#inteligență-artificială-2025-2026)
- [Laborator #06](#laborator-06)
  - [Cuprins](#cuprins)
  - [1. Obiective](#1-obiective)
  - [2. Elemente teoretice](#2-elemente-teoretice)
    - [2.1 Arhitectura CoppeliaSim și Remote API](#21-arhitectura-coppeliasim-și-remote-api)
    - [2.2 Robotul Pioneer P3-DX](#22-robotul-pioneer-p3-dx)
      - [Cinematica tracțiunii diferențiale](#cinematica-tracțiunii-diferențiale)
      - [Senzorii ultrasonici](#senzorii-ultrasonici)
    - [2.3 Comportamente reactive și vehicule Braitenberg](#23-comportamente-reactive-și-vehicule-braitenberg)
      - [Comportamente reactive (*reactive behaviors*)](#comportamente-reactive-reactive-behaviors)
      - [Vehicule Braitenberg](#vehicule-braitenberg)
      - [Wall-following (urmărirea unui perete)](#wall-following-urmărirea-unui-perete)
  - [3. Cerințe de laborator](#3-cerințe-de-laborator)
    - [3.1 Conectarea la CoppeliaSim și inspecția scenei](#31-conectarea-la-coppeliasim-și-inspecția-scenei)
    - [3.2 Controlul motorului - mișcare în formă geometrică](#32-controlul-motorului--mișcare-în-formă-geometrică)
    - [3.3 Citirea senzorilor de proximitate](#33-citirea-senzorilor-de-proximitate)
    - [3.4 Comportament reactiv simplu - oprire la obstacol](#34-comportament-reactiv-simplu--oprire-la-obstacol)
    - [3.5 Vehicul Braitenberg - evitare de obstacole](#35-vehicul-braitenberg--evitare-de-obstacole)
    - [3.6 Wall-following - urmărirea unui perete](#36-wall-following--urmărirea-unui-perete)
  - [4. Temă](#4-temă)
    - [Tema A - Evitare cu recuperare (nivel: mediu)](#tema-a--evitare-cu-recuperare-nivel-mediu)
    - [Tema B - Braitenberg cu înregistrare de date (nivel: mediu-avansat)](#tema-b--braitenberg-cu-înregistrare-de-date-nivel-mediu-avansat)
    - [Tema C - Robot Explorer (nivel: avansat)](#tema-c--robot-explorer-nivel-avansat)
    - [Tema D - Braitenberg "Iubire" (Bonus)](#tema-d--braitenberg-iubire-bonus)
  - [5. Bibliografie](#5-bibliografie)
  - [Anexă](#anexă)
    - [A1 - Fișier `requirements.txt`](#a1--fișier-requirementstxt)
    - [A2 - Structura recomandată a proiectului](#a2--structura-recomandată-a-proiectului)
    - [A3 - Referință rapidă API CoppeliaSim (Python)](#a3--referință-rapidă-api-coppeliasim-python)
    - [A4 - Harta senzorilor Pioneer P3-DX](#a4--harta-senzorilor-pioneer-p3-dx)
    - [A5 - Resurse suplimentare și tutoriale](#a5--resurse-suplimentare-și-tutoriale)

---

## 1. Obiective

Obiectivele sesiunii curente de laborator:

- Familiarizarea cu mediul de simulare **CoppeliaSim** și cu arhitectura sa *client-server* pentru controlul extern al roboților.
- Conectarea unui script Python la **CoppeliaSim** prin **ZMQ Remote API** și accesarea obiectelor dintr-o scenă de simulare.
- Controlul unui robot cu tracțiune diferențială (**Pioneer P3-DX**) prin setarea vitezelor celor două motoare.
- Citirea și interpretarea datelor de la senzorii de proximitate **ultrasonici** ai robotului (16 senzori).
- Implementarea **comportamentelor reactive** (*reactive behaviors*): oprire la obstacol, evitare autonomă și urmărirea unui perete (*wall-following*).
- Înțelegerea principiului **vehiculelor Braitenberg** ca model fundamental al comportamentului emergent în robotică și inteligență artificială.

---

## 2. Elemente teoretice

**CoppeliaSim** (fostul V-REP) este un simulator de roboți utilizat pe scară largă atât în industrie, cât și în mediul academic. Permite simularea fizică a roboților, a senzorilor, a mediului și a interacțiunilor dintre acestea. Codul de control poate fi scris direct în interiorul simulatorului (în Lua sau Python) sau poate rula extern - dintr-un script Python obișnuit care comunică cu simulatorul prin rețea.

Înainte de a utiliza API-ul Python, instalați clientul ZMQ într-un mediu virtual Python:

```bash
# Activare mediu virtual (Windows)
.venv\Scripts\activate

# Instalare client ZMQ pentru CoppeliaSim
pip install coppeliasim-zmqremoteapi-client
```

> **Notă:** CoppeliaSim trebuie să fie deschis și scena `pioneer_lab06.ttt` trebuie să fie încărcată înainte de a rula orice script Python. Serverul ZMQ pornește automat la deschiderea CoppeliaSim (portul implicit este **23000**).

---

### 2.1 Arhitectura CoppeliaSim și Remote API

**CoppeliaSim** funcționează ca un **server** care gestionează simularea fizică, modelele 3D, senzorii și actuatorii. Scriptul Python este un **client** extern care trimite comenzi și primește date prin rețea (local, via protocolul TCP/ZMQ). Această separare este intenționată: simulatorul se ocupă de fizică, Python se ocupă de logica AI.

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   Script Python (client)     │  ZMQ    │   CoppeliaSim (server)       │
│                              │◄───────►│                              │
│  RemoteAPIClient()           │  TCP    │  Motor physics engine        │
│  sim.setJointTargetVelocity  │  :23000 │  Proximity sensor simulation │
│  sim.readProximitySensor     │         │  Pioneer P3-DX model         │
└──────────────────────────────┘         └──────────────────────────────┘
```

**Handle-urile obiectelor:** orice obiect din scenă este identificat printr-un *handle* - un număr întreg intern. Funcția `sim.getObject('/cale/obiect')` returnează handle-ul corespunzător căii ierarhice specificate. Căile sunt construite ca un arbore de obiecte: `/PioneerP3DX/leftMotor` este motorul stâng, copil al nodului rădăcină `/PioneerP3DX`.

**Convenții de denumire** pentru scena `pioneer_lab06.ttt`:

| Cale obiect                                 | Descriere                     |
| ------------------------------------------- | ----------------------------- |
| `/PioneerP3DX`                              | Corpul principal al robotului |
| `/PioneerP3DX/leftMotor`                    | Articulație motor stâng       |
| `/PioneerP3DX/rightMotor`                   | Articulație motor drept       |
| `/PioneerP3DX/ultrasonicSensor[0]` … `[15]` | Cei 16 senzori ultrasonici    |

**Cod de bază - stabilirea conexiunii:**

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Stabilim conexiunea cu CoppeliaSim (localhost, portul implicit 23000)
client = RemoteAPIClient()
sim = client.require('sim')

print("Conectat la CoppeliaSim.")
```

---

### 2.2 Robotul Pioneer P3-DX

**Pioneer P3-DX** este unul dintre cei mai utilizați roboți în cercetarea robotică și educație. Are **tracțiune diferențială** (*differential drive*): două roți motorizate independent pe axa centrală și o roată de sprijin pasivă în spate. Viteza de rotație diferită a celor două roți determină direcția de deplasare.

#### Cinematica tracțiunii diferențiale

Dacă $v_S$ = viteza roată stângă și $v_D$ = viteza roată dreaptă (exprimate în **rad/s**):

| Condiție        | Comportament                  |
| --------------- | ----------------------------- |
| $v_S = v_D > 0$ | Mers înainte în linie dreaptă |
| $v_S = v_D < 0$ | Mers înapoi în linie dreaptă  |
| $v_S > v_D$     | Viraj la dreapta              |
| $v_S < v_D$     | Viraj la stânga               |
| $v_S = -v_D$    | Rotire pe loc                 |

#### Senzorii ultrasonici

Robotul are **16 senzori ultrasonici** dispuși circular. Numerotarea începe din față-stânga și continuă în sens orar (privit de sus). Raza maximă de detectare în scena implicită este **~1.0 m**.

| Indecși | Poziție aproximativă               |
| ------- | ---------------------------------- |
| 0, 1    | Față-stânga (exterior → interior)  |
| 2, 3    | Față-centru stânga                 |
| 4, 5    | Față-centru dreapta                |
| 6, 7    | Față-dreapta (interior → exterior) |
| 8, 9    | Lateral dreapta                    |
| 10, 11  | Spate dreapta → spate centru       |
| 12, 13  | Spate centru → spate stânga        |
| 14, 15  | Lateral stânga                     |

> **Notă:** Maparea exactă a indicilor pe poziții se validează experimental în cerința 3.3. Numerotarea de mai sus este orientativă; scenele pot diferi ușor.

**Cod - obținerea handle-urilor:**

```python
# Handle-ul corpului robotului
robot = sim.getObject('/PioneerP3DX')

# Handle-urile motoarelor
left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
right_motor = sim.getObject('/PioneerP3DX/rightMotor')

# Lista celor 16 senzori ultrasonici
sensors = [
    sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
    for i in range(16)
]
```

---

### 2.3 Comportamente reactive și vehicule Braitenberg

#### Comportamente reactive (*reactive behaviors*)

Spre deosebire de comportamentele **deliberative** (care implică planificare, modele interne ale lumii și raționament), comportamentele **reactive** produc acțiune direct din percepție, fără reprezentare internă a stării. Arhitectura canonică este:

```
Senzori  ──►  Procesor  ──►  Actuatori
 (input)      (logică)        (output)
```

Avantaje: viteză de răspuns, robustețe la erori de percepție, simplitate de implementare.
Dezavantaje: comportament limitat pentru sarcini complexe, pot apărea cicluri sau situații de blocaj.

**Structura canonică a buclei de control reactiv în Python:**

```python
sim.startSimulation()

try:
    while True:
        # 1. PERCEPȚIE: citire date de la senzori
        readings = read_sensors(sim, sensors)

        # 2. PROCESARE: calculare comenzi de acțiune
        v_left, v_right = compute_velocities(readings)

        # 3. ACȚIUNE: trimitere comenzi la actuatori
        sim.setJointTargetVelocity(left_motor,  v_left)
        sim.setJointTargetVelocity(right_motor, v_right)

except KeyboardInterrupt:
    pass
finally:
    # Oprire garantată a motoarelor și a simulării
    sim.setJointTargetVelocity(left_motor,  0.0)
    sim.setJointTargetVelocity(right_motor, 0.0)
    sim.stopSimulation()
```

> **Notă:** Blocul `try/finally` garantează că motoarele sunt oprite și simularea este încheiată corect chiar dacă scriptul este întrerupt (Ctrl+C) sau apare o eroare. Acesta este un **șablon obligatoriu** pentru toate scripturile de control din acest laborator.

#### Vehicule Braitenberg

Valentino Braitenberg (1984) a descris vehicule simple cu **conexiuni directe senzor-motor** care produc comportamente ce par să exprime intenții complexe - frică, agresivitate, atracție, curiozitate. Esența: fără stare internă, fără planificare, doar conexiuni ponderate.
*Vezi și https://en.wikipedia.org/wiki/Braitenberg_vehicle. Numele conceptuale ale vehicolelor ("agresivitate", "frică", "atracție") sunt preluate din cartea lui Valentino Braitenberg*:

> "Simple rules can appear to be smart"

Există două tipuri de conexiuni:

```
Vehicul tip "Frică" (evitare):         Vehicul tip "Agresivitate" (atracție):

Senzor_S ─────────► Motor_S            Senzor_S ─────────► Motor_D
Senzor_D ─────────► Motor_D            Senzor_D ─────────► Motor_S
         (direct / ipsilateral)                  (încrucișat / contralateral)
```

- **Conexiune ipsilaterală (directă):** senzorul stâng influențează motorul stâng. Un obstacol la stânga accelerează roata stângă → roata stângă mai rapidă → robotul virează *la dreapta*, departe de obstacol → comportament de **evitare** ("frică").
- **Conexiune contralaterală (încrucișată):** senzorul stâng influențează motorul drept. Un obstacol la stânga accelerează roata dreaptă → roata dreaptă mai rapidă → robotul virează *la stânga*, spre obstacol → comportament de **atracție** ("agresivitate").

> **Notă pedagogică:** CoppeliaSim include în scena implicită a robotului Pioneer P3-DX un script Lua care implementează exact un vehicul Braitenberg, folosind array-urile `braitenbergL[]` și `braitenbergR[]`. Puteți inspecta acel script (click dreapta pe robot în scenă → *Edit child script*) pentru a vedea coeficienții originali. În cerința 3.5, vom re-implementa aceeași logică în Python.

**Formula de calcul a vitezelor Braitenberg:**

Fie $s_i \in [0, 1]$ valoarea normalizată a senzorului $i$ (0 = nimic detectat, 1 = obstacol foarte aproape), iar $w^L_i$, $w^D_i$ ponderile senzorului $i$ pentru motorul stâng, respectiv drept:

$$v_S = v_{baza} + k \cdot \sum_{i} w^S_i \cdot s_i$$
$$v_D = v_{baza} + k \cdot \sum_{i} w^D_i \cdot s_i$$

unde $k$ este un factor de amplificare și $v_{baza}$ este viteza de mers în absența obstacolelor.

#### Wall-following (urmărirea unui perete)

Comportamentul de urmărire a peretelui menține robotul la o distanță constantă față de un perete lateral. Implementarea se bazează pe un **controller proporțional (P)**:

$$\text{eroare} = d_{actuala} - d_{tinta}$$
$$v_S = v_{baza} + k_P \cdot \text{eroare}$$
$$v_D = v_{baza} - k_P \cdot \text{eroare}$$

Dacă eroarea este pozitivă (prea departe de perete) → robotul virează spre perete. Dacă eroarea este negativă (prea aproape) → robotul virează departe. Coeficientul $k_P$ controlează reactivitatea: prea mic → robot lent; prea mare → robot oscilant.

---

## 3. Cerințe de laborator

> **Notă:** Înainte de a rula orice cerință, verificați că:
> 
> 1. CoppeliaSim este deschis și scena `pioneer_lab06.ttt` este încărcată (File → Open Scene).
> 2. Simularea este **pornită** (butonul ▶ Play din bara de sus).
> 3. Mediul virtual Python este activat și pachetul `coppeliasim-zmqremoteapi-client` este instalat.

---

### 3.1 Conectarea la CoppeliaSim și inspecția scenei

**Cerință:** Conectați-vă la CoppeliaSim printr-un script Python, obțineți handle-urile tuturor obiectelor relevante din scenă și afișați informații despre starea inițială a simulării: versiunea simulatorului, poziția robotului și lecturile tuturor celor 16 senzori ultrasonici.

Creați fișierul `lab06/cerinta_3_1_conectare.py` cu conținutul de mai jos și rulați-l:

```python
"""
Cerința 3.1 - Conectarea la CoppeliaSim și inspecția scenei.
IA Lab #06 - Inteligență Artificială 2025-2026
"""
from coppeliasim_zmqremoteapi_client import RemoteAPIClient


def main():
    # Conectare la serverul CoppeliaSim (localhost:23000)
    client = RemoteAPIClient()
    sim = client.require('sim')

    print("=== Conexiune stabilita ===")
    version = sim.getInt32Param(sim.intparam_program_version)
    print(f"Versiune CoppeliaSim (encoded): {version}")

    # --- Obținerea handle-urilor ---
    robot       = sim.getObject('/PioneerP3DX')
    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')

    sensors = [
        sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
        for i in range(16)
    ]

    print(f"\n=== Handle-uri obiecte ===")
    print(f"Robot:        {robot}")
    print(f"Motor stang:  {left_motor}")
    print(f"Motor drept:  {right_motor}")
    print(f"Senzori:      {sensors}")

    # --- Poziția inițială a robotului ---
    pos = sim.getObjectPosition(robot, sim.handle_world)
    print(f"\n=== Pozitia initiala a robotului ===")
    print(f"X={pos[0]:.3f} m,  Y={pos[1]:.3f} m,  Z={pos[2]:.3f} m")

    # --- Lectura inițială a tuturor senzorilor ---
    print(f"\n=== Lectura initiala senzori (detectat, distanta) ===")
    for i, sensor in enumerate(sensors):
        result, distance, *_ = sim.readProximitySensor(sensor)
        detected = bool(result)
        dist_str = f"{distance:.3f} m" if detected else "---"
        print(f"  Sensor[{i:2d}]: detectat={str(detected):<5},  distanta={dist_str}")


if __name__ == '__main__':
    main()
```

**Ieșire așteptată (parțial):**

```
=== Conexiune stabilita ===
Versiune CoppeliaSim (encoded): 40600

=== Handle-uri obiecte ===
Robot:        42
Motor stang:  17
Motor drept:  18
Senzori:      [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20]

=== Pozitia initiala a robotului ===
X=0.000 m,  Y=0.000 m,  Z=0.139 m

=== Lectura initiala senzori (detectat, distanta) ===
  Sensor[ 0]: detectat=False,  distanta=---
  Sensor[ 1]: detectat=False,  distanta=---
  ...
  Sensor[ 3]: detectat=True,   distanta=0.847 m
```

> **Notă:** Handle-urile numerice variază în funcție de scenă - valorile de mai sus sunt orientative. Ceea ce contează este că `getObject()` returnează un număr valid (pozitiv, nenul). Dacă apare excepția `ConnectionRefusedError`, verificați că simularea este pornită (butonul ▶ este activ în CoppeliaSim).

---

### 3.2 Controlul motorului - mișcare în formă geometrică

**Cerință:** Implementați o secvență de mișcări care face robotul să parcurgă un **pătrat** (4 laturi drepte + 4 viraje de 90°), folosind controlul în buclă deschisă bazat pe timp.

**Controlul *open-loop* (buclă deschisă)** nu citește senzori - trimite comenzi pentru un interval de timp calculat și presupune că mișcarea se realizează conform predicției. Este simplu de implementat, dar acumulează erori pe parcursul execuției.

Valorile de timp recomandate pentru Pioneer P3-DX la viteza `V_FORWARD = 2.0 rad/s` sunt date mai jos ca puncte de plecare; ajustați-le experimental dacă este nevoie.

Creați fișierul `lab06/cerinta_3_2_patrat.py`:

```python
"""
Cerința 3.2 - Controlul motorului: mișcare în pătrat (buclă deschisă).
IA Lab #06 - Inteligență Artificială 2025-2026
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- Parametri de mișcare (ajustați experimental dacă e nevoie) ---
V_FORWARD = 2.0    # rad/s - viteza înainte (ambele roți egale)
V_TURN    = 2.0    # rad/s - viteza pentru viraj (pe o singură roată)
T_LINIE   = 3.0    # secunde - timp mers drept (o latură de pătrat)
T_VIRAJ   = 1.57   # secunde - timp viraj ~90° (π/2 rad, empiric)


def set_velocity(sim, left_motor, right_motor, v_left, v_right):
    """
    Setează viteza țintă a ambelor motoare.

    Args:
        sim: obiectul API CoppeliaSim.
        left_motor: handle-ul motorului stâng.
        right_motor: handle-ul motorului drept.
        v_left: viteza roată stângă (rad/s).
        v_right: viteza roată dreaptă (rad/s).
    """
    sim.setJointTargetVelocity(left_motor,  v_left)
    sim.setJointTargetVelocity(right_motor, v_right)


def move_forward(sim, left_motor, right_motor, duration):
    """Mișcare rectilinie pentru 'duration' secunde."""
    set_velocity(sim, left_motor, right_motor, V_FORWARD, V_FORWARD)
    time.sleep(duration)


def turn_left_90(sim, left_motor, right_motor):
    """Viraj stânga ~90°: roata dreaptă înainte, roata stângă înapoi."""
    set_velocity(sim, left_motor, right_motor, -V_TURN, V_TURN)
    time.sleep(T_VIRAJ)


def stop(sim, left_motor, right_motor):
    """Oprire completă a ambelor motoare."""
    set_velocity(sim, left_motor, right_motor, 0.0, 0.0)


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    robot       = sim.getObject('/PioneerP3DX')
    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')

    sim.startSimulation()
    print("Simulare pornita. Robotul va parcurge un patrat.")
    time.sleep(0.5)  # pauza scurta de stabilizare

    try:
        for latura in range(4):
            print(f"Latura {latura + 1}/4 - mers inainte {T_LINIE}s")
            move_forward(sim, left_motor, right_motor, T_LINIE)

            print(f"Viraj stanga ~90°")
            turn_left_90(sim, left_motor, right_motor)

        stop(sim, left_motor, right_motor)

        pos = sim.getObjectPosition(robot, sim.handle_world)
        print(f"\nPozitie finala: X={pos[0]:.3f} m,  Y={pos[1]:.3f} m")
        print("(Ideal: robotul sa fie aproape de pozitia initiala 0, 0)")
        time.sleep(1.0)

    finally:
        stop(sim, left_motor, right_motor)
        sim.stopSimulation()
        print("Simulare oprita.")


if __name__ == '__main__':
    main()
```

**Ieșire așteptată:**

```
Simulare pornita. Robotul va parcurge un patrat.
Latura 1/4 - mers inainte 3.0s
Viraj stanga ~90°
Latura 2/4 - mers inainte 3.0s
Viraj stanga ~90°
Latura 3/4 - mers inainte 3.0s
Viraj stanga ~90°
Latura 4/4 - mers inainte 3.0s
Viraj stanga ~90°

Pozitie finala: X=0.021 m,  Y=-0.018 m
(Ideal: robotul sa fie aproape de pozitia initiala 0, 0)
Simulare oprita.
```

*De ce poziția finală nu coincide exact cu cea inițială? Ce factori ar cauza această eroare pe un robot real față de un simulator ideal?*

---

### 3.3 Citirea senzorilor de proximitate

**Cerință:** Implementați o buclă de monitorizare care afișează în timp real lecturile tuturor celor 16 senzori ultrasonici, actualizată la fiecare 0.5 secunde. Identificați care senzori se activează când există un obstacol în față față de un obstacol lateral.

Funcția `sim.readProximitySensor(handle)` returnează un tuplu de 5 valori:
`(result, distance, detected_point, detected_object_handle, detected_surface_normal)`.
Valoarea `result = 1` înseamnă că un obiect a fost detectat; `distance` este distanța în metri. Când `result = 0`, valoarea `distance` nu este semnificativă.

Creați fișierul `lab06/cerinta_3_3_senzori.py`:

```python
"""
Cerința 3.3 - Citirea și vizualizarea în timp real a senzorilor de proximitate.
IA Lab #06 - Inteligență Artificială 2025-2026
"""
import time
import os
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

SENSOR_MAX_RANGE = 1.0   # metri - raza maxima de detectare a senzorilor

# Etichete descriptive pentru cei 16 senzori (orientative, validati prin experiment)
SENSOR_LABELS = [
    "S00  fata-stanga-ext ",
    "S01  fata-stanga     ",
    "S02  fata-centru-st  ",
    "S03  fata-centru-st  ",
    "S04  fata-centru-dr  ",
    "S05  fata-centru-dr  ",
    "S06  fata-dreapta    ",
    "S07  fata-dreapta-ext",
    "S08  lateral-dreapta ",
    "S09  lateral-dreapta ",
    "S10  spate-dreapta   ",
    "S11  spate-centru    ",
    "S12  spate-centru    ",
    "S13  spate-stanga    ",
    "S14  lateral-stanga  ",
    "S15  lateral-stanga  ",
]


def read_all_sensors(sim, sensors):
    """
    Citeste toti senzorii si returneaza lista de lecturi.

    Args:
        sim: obiectul API CoppeliaSim.
        sensors: lista de handle-uri ale senzorilor.

    Returns:
        Lista de tupluri (bool detectat, float distanta_m).
    """
    readings = []
    for sensor in sensors:
        result, distance, *_ = sim.readProximitySensor(sensor)
        detected = bool(result)
        dist = distance if detected else SENSOR_MAX_RANGE
        readings.append((detected, dist))
    return readings


def print_dashboard(readings):
    """Afisaza un dashboard text cu lecturile tuturor senzorilor."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== DASHBOARD SENZORI ULTRASONICI - Pioneer P3-DX ===\n")
    print(f"  {'Idx':<5} {'Eticheta':<25} {'Detectat':<10} {'Distanta':>10}  {'Bar':}")
    print("  " + "-" * 65)
    for i, (detected, dist) in enumerate(readings):
        bar_len = int((1.0 - dist / SENSOR_MAX_RANGE) * 20) if detected else 0
        bar     = "█" * bar_len
        dist_str = f"{dist:.3f} m" if detected else "(nimic)"
        det_str  = "DA" if detected else "nu"
        print(f"  [{i:2d}]  {SENSOR_LABELS[i]}  {det_str:<10} {dist_str:>10}  {bar}")
    print("\n  Ctrl+C pentru oprire.")


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    sensors = [
        sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
        for i in range(16)
    ]

    print("Monitorizare senzori pornita (simularea trebuie sa fie activa).")
    print("Plasati sau mutati un obiect in CoppeliaSim si observati schimbarile.\n")

    try:
        while True:
            readings = read_all_sensors(sim, sensors)
            print_dashboard(readings)
            time.sleep(0.5)   # actualizare la fiecare 0.5 secunde
    except KeyboardInterrupt:
        print("\nMonitorizare oprita.")


if __name__ == '__main__':
    main()
```

**Ieșire așteptată (parțial - cu un obstacol plasat in fata robotului):**

```
=== DASHBOARD SENZORI ULTRASONICI - Pioneer P3-DX ===

  Idx   Eticheta                  Detectat     Distanta  Bar
  -----------------------------------------------------------------
  [ 0]  S00  fata-stanga-ext      nu            (nimic)
  [ 1]  S01  fata-stanga          nu            (nimic)
  [ 2]  S02  fata-centru-st       DA            0.612 m  ████████
  [ 3]  S03  fata-centru-st       DA            0.587 m  ████████
  [ 4]  S04  fata-centru-dr       DA            0.601 m  ████████
  [ 5]  S05  fata-centru-dr       DA            0.634 m  ███████
  [ 6]  S06  fata-dreapta         nu            (nimic)
  ...
```

**Sarcina echipei:** plasați (drag) un obiect de tip cutie (*cuboid*) în scenă, mai întâi în fața robotului, apoi în lateral. Notați ce indecși de senzori se activează în fiecare caz - aceste informații vor fi folosite în cerința 3.4.

---

### 3.4 Comportament reactiv simplu - oprire la obstacol

**Cerință:** Implementați o buclă de control care pornește robotul drept înainte și îl oprește automat când cel puțin un senzor frontal detectează un obstacol la mai puțin de `STOP_DISTANCE` metri.

Acesta este cel mai simplu comportament reactiv posibil: un singur stimul (*detecție obstacol*) produce o singură acțiune (*stop*). Este un **prag de declanșare** (*threshold trigger*).

Creați fișierul `lab06/cerinta_3_4_stop_obstacol.py`:

```python
"""
Cerința 3.4 - Comportament reactiv simplu: oprire la obstacol.
IA Lab #06 - Inteligență Artificială 2025-2026
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

V_FORWARD     = 2.0    # rad/s - viteza de deplasare inainte
STOP_DISTANCE = 0.5    # metri - distanta la care robotul opreste
FRONT_SENSORS = [2, 3, 4, 5]  # indicii senzorilor frontali (ajustati dupa cerinta 3.3)
SENSOR_MAX    = 1.0    # metri - valoare returnata cand senzorul nu detecteaza nimic


def get_min_front_distance(sim, sensors, front_indices):
    """
    Returneaza distanta minima detectata de senzorii frontali.

    Args:
        sim: obiectul API CoppeliaSim.
        sensors: lista completa de handle-uri senzori.
        front_indices: lista indicilor senzorilor de monitorizat.

    Returns:
        float: distanta minima in metri (SENSOR_MAX daca nimic detectat).
    """
    min_dist = SENSOR_MAX
    for idx in front_indices:
        result, distance, *_ = sim.readProximitySensor(sensors[idx])
        if result and distance < min_dist:
            min_dist = distance
    return min_dist


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [
        sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
        for i in range(16)
    ]

    sim.startSimulation()
    print(f"Robot pornit. Se opreste la obstacol < {STOP_DISTANCE} m. (Ctrl+C pentru iesire)")

    try:
        while True:
            dist_front = get_min_front_distance(sim, sensors, FRONT_SENSORS)

            if dist_front < STOP_DISTANCE:
                # OPRIT: obstacol detectat prea aproape
                sim.setJointTargetVelocity(left_motor,  0.0)
                sim.setJointTargetVelocity(right_motor, 0.0)
                print(f"[STOP]   Obstacol la {dist_front:.3f} m  (prag: {STOP_DISTANCE} m)")
            else:
                # MERS INAINTE: drum liber
                sim.setJointTargetVelocity(left_motor,  V_FORWARD)
                sim.setJointTargetVelocity(right_motor, V_FORWARD)
                print(f"[MERS]   Distanta frontala minima: {dist_front:.3f} m")

            time.sleep(0.05)   # 20 Hz - frecventa buclei de control

    except KeyboardInterrupt:
        print("\nOprire manuala.")
    finally:
        sim.setJointTargetVelocity(left_motor,  0.0)
        sim.setJointTargetVelocity(right_motor, 0.0)
        sim.stopSimulation()


if __name__ == '__main__':
    main()
```

**Ieșire așteptată:**

```
Robot pornit. Se opreste la obstacol < 0.5 m. (Ctrl+C pentru iesire)
[MERS]   Distanta frontala minima: 1.000 m
[MERS]   Distanta frontala minima: 0.823 m
[MERS]   Distanta frontala minima: 0.614 m
[STOP]   Obstacol la 0.487 m  (prag: 0.500 m)
[STOP]   Obstacol la 0.487 m  (prag: 0.500 m)
```

*Ce se întâmplă dacă `STOP_DISTANCE = 0.1 m`? Dar dacă `STOP_DISTANCE = 2.0 m`? Care este compromisul (*trade-off*) dintre siguranță și eficiența deplasării?*

---

### 3.5 Vehicul Braitenberg - evitare de obstacole

**Cerință:** Implementați un vehicul Braitenberg de tip **"Frică"** (evitare de obstacole) care navighează autonom într-o arenă cu obstacole fără să se lovească de ele. Robotul trebuie să demonstreze evitare fluidă, nu oprire bruscă.

Vom folosi **8 senzori frontali** (indicii 0–7) cu conexiuni **contralaterale** ponderate. Fiecare senzor activat modifică vitezele celor două motoare proporțional cu apropierea de obstacol.

**Tabelul ponderilor senzor-motor** (conexiuni ipsilaterale = evitare / "Frică"):

| Idx | Poziție               | Pondere motor stâng ($w^S$) | Pondere motor drept ($w^D$) | Efect           |
| --- | --------------------- | --------------------------- | --------------------------- | --------------- |
| 0   | față-stânga exterior  | +0.5                        | −0.5                        | virează dreapta |
| 1   | față-stânga           | +1.0                        | −1.0                        | virează dreapta |
| 2   | față-centru stânga    | +1.5                        | −1.5                        | virează dreapta |
| 3   | față-centru stânga    | +2.0                        | −2.0                        | virează dreapta |
| 4   | față-centru dreapta   | −2.0                        | +2.0                        | virează stânga  |
| 5   | față-centru dreapta   | −1.5                        | +1.5                        | virează stânga  |
| 6   | față-dreapta          | −1.0                        | +1.0                        | virează stânga  |
| 7   | față-dreapta exterior | −0.5                        | +0.5                        | virează stânga  |

Creați fișierul `lab06/cerinta_3_5_braitenberg.py`:

```python
"""
Cerința 3.5 - Vehicul Braitenberg: evitare de obstacole (tip 'Frica').
IA Lab #06 - Inteligență Artificială 2025-2026
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

V_BASE   = 3.0   # rad/s - viteza de baza (robot fara obstacole in fata)
V_MAX    = 6.0   # rad/s - viteza maxima permisa
K_SENSOR = 6.0   # factor de amplificare a influentei senzorilor
SENSOR_MAX = 1.0 # metri - raza maxima senzor

# Ponderile senzorilor: (w_motor_stang, w_motor_drept)
# Indecsi 0..7 = jumatatea frontala a robotului
# Conexiuni ipsilaterale (directe) => tip "Frica" (evitare):
#   senzor stanga excita motorul stang → roata stanga mai rapida → vireaza DREAPTA (departe)
#   senzor dreapta excita motorul drept → roata dreapta mai rapida → vireaza STANGA (departe)
WEIGHTS = [
    (+0.5, -0.5),   # S0  fata-stanga-ext   → excita stanga, inhiba dreapta → vireaza dreapta
    (+1.0, -1.0),   # S1  fata-stanga
    (+1.5, -1.5),   # S2  fata-centru-st
    (+2.0, -2.0),   # S3  fata-centru-st
    (-2.0, +2.0),   # S4  fata-centru-dr    → excita dreapta, inhiba stanga → vireaza stanga
    (-1.5, +1.5),   # S5  fata-centru-dr
    (-1.0, +1.0),   # S6  fata-dreapta
    (-0.5, +0.5),   # S7  fata-dreapta-ext
]


def braitenberg_velocities(sim, sensors):
    """
    Calculeaza vitezele Braitenberg pentru evitarea obstacolelor.

    Fiecare senzor activat contribuie proportional cu apropierea
    de obstacol, prin ponderile definite in WEIGHTS.

    Args:
        sim: obiectul API CoppeliaSim.
        sensors: lista handle-urilor tuturor senzorilor.

    Returns:
        tuple (v_stang, v_drept) in rad/s.
    """
    v_left  = V_BASE
    v_right = V_BASE

    for i, (w_l, w_r) in enumerate(WEIGHTS):
        result, distance, *_ = sim.readProximitySensor(sensors[i])
        if result:
            # Normalizare: obstacol aproape => proximity=1, departe => proximity=0
            proximity = 1.0 - (distance / SENSOR_MAX)
            proximity = max(0.0, min(1.0, proximity))

            v_left  += K_SENSOR * w_l * proximity
            v_right += K_SENSOR * w_r * proximity

    # Limitare la intervalul [-V_MAX, +V_MAX]
    v_left  = max(-V_MAX, min(V_MAX, v_left))
    v_right = max(-V_MAX, min(V_MAX, v_right))

    return v_left, v_right


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [
        sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
        for i in range(16)
    ]

    sim.startSimulation()
    print("Vehicul Braitenberg (evitare) pornit. Ctrl+C pentru oprire.\n")

    try:
        iteration = 0
        while True:
            v_left, v_right = braitenberg_velocities(sim, sensors)

            sim.setJointTargetVelocity(left_motor,  v_left)
            sim.setJointTargetVelocity(right_motor, v_right)

            # Afisare la fiecare ~1 secunda (20 iteratii x 0.05s)
            if iteration % 20 == 0:
                print(f"v_stang={v_left:+.2f} rad/s  |  v_drept={v_right:+.2f} rad/s")

            iteration += 1
            time.sleep(0.05)   # 20 Hz

    except KeyboardInterrupt:
        print("\nOprire vehicul Braitenberg.")
    finally:
        sim.setJointTargetVelocity(left_motor,  0.0)
        sim.setJointTargetVelocity(right_motor, 0.0)
        sim.stopSimulation()


if __name__ == '__main__':
    main()
```

**Ieșire așteptată:**

```
Vehicul Braitenberg (evitare) pornit. Ctrl+C pentru oprire.

v_stang=+3.00 rad/s  |  v_drept=+3.00 rad/s
v_stang=+4.21 rad/s  |  v_drept=+1.17 rad/s
v_stang=+5.84 rad/s  |  v_drept=-0.51 rad/s
v_stang=+3.00 rad/s  |  v_drept=+3.00 rad/s
```

**Experimentul echipei:** modificați `WEIGHTS` pentru a obține comportamentul de tip **"Agresivitate"** - înlocuiți conexiunile ipsilaterale cu conexiuni contralaterale (inversați semnele fiecărei ponderi: `(+0.5, -0.5)` devine `(-0.5, +0.5)` etc.). Observați că robotul virează acum *spre* obstacole în loc să le evite. Documentați diferența de comportament față de varianta "Frică".

*Cum se compară comportamentul generat de codul vostru cu scriptul Lua preinstalat al robotului Pioneer P3-DX? Inspectați acel script în CoppeliaSim (click dreapta pe robot → Edit child script) și identificați array-urile `braitenbergL` și `braitenbergR`.*

---

### 3.6 Wall-following - urmărirea unui perete

**Cerință:** Implementați un comportament de urmărire a **peretelui din dreapta**. Robotul trebuie să mențină o distanță de ~0.4 m față de peretele drept, corectând traiectoria printr-un controller proporțional.

Vom folosi senzorii laterali dreapta (indicii 8 și 9) pentru estimarea distanței față de perete, și senzorii frontali (3 și 4) pentru detectarea obstacolelor din față.

**Controller proporțional (P):** eroarea = distanța actuală − distanța țintă. Dacă eroarea > 0 (prea departe de perete) → viraj ușor la dreapta. Dacă eroarea < 0 (prea aproape) → viraj ușor la stânga.

Creați fișierul `lab06/cerinta_3_6_wall_following.py`:

```python
"""
Cerința 3.6 - Wall-following: urmărirea peretelui din dreapta.
IA Lab #06 - Inteligență Artificială 2025-2026
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

V_BASE       = 2.0    # rad/s - viteza de baza
TARGET_DIST  = 0.4    # metri - distanta dorita fata de peretele drept
K_P          = 3.0    # coeficient proportional (P-controller)
FRONT_STOP   = 0.4    # metri - distanta de declansare viraj la obstacol frontal
SENSOR_MAX   = 1.0    # metri - valoare implicita cand senzorul nu detecteaza

RIGHT_SENSORS = [8, 9]   # senzori laterali dreapta
FRONT_SENSORS = [3, 4]   # senzori frontali pentru detectare obstacol


def read_min_dist(sim, sensors, indices):
    """
    Returneaza distanta minima detectata de un grup de senzori.

    Args:
        sim: obiectul API CoppeliaSim.
        sensors: lista completa de handle-uri senzori.
        indices: lista indicilor senzorilor de verificat.

    Returns:
        float: distanta minima in metri.
    """
    min_dist = SENSOR_MAX
    for idx in indices:
        result, dist, *_ = sim.readProximitySensor(sensors[idx])
        if result and dist < min_dist:
            min_dist = dist
    return min_dist


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [
        sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
        for i in range(16)
    ]

    sim.startSimulation()
    print(f"Wall-following pornit. Distanta tinta perete drept: {TARGET_DIST} m")
    print("(Ctrl+C pentru oprire)\n")

    try:
        while True:
            dist_right = read_min_dist(sim, sensors, RIGHT_SENSORS)
            dist_front = read_min_dist(sim, sensors, FRONT_SENSORS)

            if dist_front < FRONT_STOP:
                # Obstacol frontal: viraj la stanga
                v_left, v_right = -V_BASE, +V_BASE
                state = f"VIREAZA STANGA (frontal={dist_front:.3f} m)"

            elif dist_right >= SENSOR_MAX * 0.95:
                # Nu exista perete la dreapta: cautam perete (viraj usor dreapta)
                v_left, v_right = V_BASE, V_BASE * 0.5
                state = "CAUTA PERETE (viraj dreapta)"

            else:
                # Controller P: eroare = distanta actuala - tinta
                error   = dist_right - TARGET_DIST
                v_left  = V_BASE + K_P * error
                v_right = V_BASE - K_P * error

                # Limitare la [-V_BASE*1.5, +V_BASE*1.5]
                cap = V_BASE * 1.5
                v_left  = max(-cap, min(cap, v_left))
                v_right = max(-cap, min(cap, v_right))

                state = f"URMARIRE  dr={dist_right:.3f} m  err={error:+.3f} m"

            sim.setJointTargetVelocity(left_motor,  v_left)
            sim.setJointTargetVelocity(right_motor, v_right)
            print(f"{state:<45}  vS={v_left:+.2f}  vD={v_right:+.2f}")

            time.sleep(0.05)   # 20 Hz

    except KeyboardInterrupt:
        print("\nOprire wall-follower.")
    finally:
        sim.setJointTargetVelocity(left_motor,  0.0)
        sim.setJointTargetVelocity(right_motor, 0.0)
        sim.stopSimulation()


if __name__ == '__main__':
    main()
```

**Ieșire așteptată:**

```
Wall-following pornit. Distanta tinta perete drept: 0.4 m
(Ctrl+C pentru oprire)

CAUTA PERETE (viraj dreapta)             vS=+2.00  vD=+1.00
URMARIRE  dr=0.831 m  err=+0.431 m       vS=+3.29  vD=+0.71
URMARIRE  dr=0.421 m  err=+0.021 m       vS=+2.06  vD=+1.94
URMARIRE  dr=0.401 m  err=+0.001 m       vS=+2.00  vD=+2.00
```

*Ce se întâmplă dacă `K_P = 0.5`? Dar dacă `K_P = 15.0`? Există un interval de valori pentru care comportamentul este stabil și fluid - găsiți-l experimental și justificați rezultatele.*

---

## 4. Temă

Alegeți **cel puțin una** dintre temele de mai jos și implementați-o în directorul `lab06/tema/`. Predați fișierele sursă pe GitHub împreună cu un scurt fișier `tema/README.md` care descrie comportamentul implementat și observațiile echipei.

#### Tema A - Evitare cu recuperare (nivel: mediu)

Extindeți cerința 3.4 cu o stare de **recuperare**: când robotul este oprit în fața unui obstacol, în loc să rămână blocat, execută automat o manevră de ieșire (dă înapoi 1 secundă, virează aleatoriu stânga sau dreapta 90°, reia mersul înainte).

Implementați o **mașină de stări** cu 3 stări: `FORWARD`, `BACKWARD`, `TURNING`. Afișați starea curentă la fiecare pas al buclei de control.

1. Definiți o clasă `RobotState` cu cele 3 stări ca atribute de clasă (sau folosiți un `Enum`).
2. Implementați funcția `next_state(current_state, dist_front) → new_state`.
3. Demonstrați că robotul nu se blochează permanent în fața unui obstacol.

#### Tema B - Braitenberg cu înregistrare de date (nivel: mediu-avansat)

Extindeți cerința 3.5 cu înregistrarea datelor de simulare. La fiecare iterație, salvați într-un fișier CSV (`tema/log_braitenberg.csv`) coloanele: `timestamp`, `v_left`, `v_right`, `s0`, `s1`, …, `s7`, `pos_x`, `pos_y`.

La finalul rulării (după Ctrl+C), generați cu **Matplotlib** (Laborator #02) 3 grafice salvate ca imagini PNG:

1. Traiectoria robotului în planul XY (`pos_x` vs `pos_y`).
2. Vitezele `v_left` și `v_right` în funcție de timp.
3. Un *heatmap* al activării senzorilor în timp (`s0`–`s7` pe axa Y, timpii pe axa X).

#### Tema C - Robot Explorer (nivel: avansat)

Implementați un comportament de **explorare autonomă** care combină *wall-following* (cerința 3.6) cu o strategie de recuperare la blocaj (similar Temei A). Robotul trebuie să exploreze o arenă dreptunghiulară cu obstacole fără coliziuni timp de **cel puțin 60 de secunde**.

1. Salvați traiectoria completă (X, Y) și generați graficul la final.
2. Realizați o înregistrare video a ecranului (*screen capture*) a simulării de minimum 60 de secunde.
3. Documentați în `README.md` parametrii aleși și motivația fiecărei decizii de design.

#### Tema D - Braitenberg "Iubire" (Bonus)

Braitenberg a descris 14 vehicule cu comportamente emergente diferite. Implementați vehiculul de tip **"Iubire"**: conexiuni ipsilaterale *inhibitorii* - senzorii din față-stânga *reduc* viteza motorului stâng, iar senzorii din față-dreapta *reduc* viteza motorului drept. Efectul: robotul *urmărește* sursele de stimul, dar se oprește când ajunge aproape - comportament similar atracției magnetice.

Demonstrați diferența de comportament față de vehiculul "Frică" din cerința 3.5. Documentați teoretic alegerea conexiunilor și explicați de ce comportamentul emergent seamănă cu "iubirea" conform descrierii lui Braitenberg.

---

## 5. Bibliografie

[1] Coppelia Robotics, *CoppeliaSim User Manual*, 2024.
    https://manual.coppeliarobotics.com/

[2] Coppelia Robotics, *ZMQ Remote API - Python client*, GitHub, 2024.
    https://github.com/CoppeliaRobotics/zmqRemoteApi
    PyPI: https://pypi.org/project/coppeliasim-zmqremoteapi-client/
    Documentație API: https://manual.coppeliarobotics.com/en/zmqRemoteApiOverview.htm

[3] V. Braitenberg, *Vehicles: Experiments in Synthetic Psychology*. MIT Press, 1984.

[4] R. Siegwart, I. R. Nourbakhsh, D. Scaramuzza, *Introduction to Autonomous Mobile Robots*, 2nd ed. MIT Press, 2011.

[5] CoppeliaSim Forums, *Meaning of the values of braitenbergL in PioneerP3DX robot*, 2022.
    https://forum.coppeliarobotics.com/viewtopic.php?t=9965

[6] Python Software Foundation, *time - Time access and conversions*, Python 3 Documentation, 2024.
    https://docs.python.org/3/library/time.html

[7] Northwestern Mechatronics Wiki, *Getting Started with the CoppeliaSim Simulator*, 2023.
    https://hades.mech.northwestern.edu/index.php/Getting_Started_with_the_CoppeliaSim_Simulator

---

## Anexă

### A1 - Fișier `requirements.txt`

```
coppeliasim-zmqremoteapi-client>=1.0.0
```

Instalare:

```bash
# Activare mediu virtual
.venv\Scripts\activate

# Instalare din requirements.txt
pip install -r requirements.txt
```

---

### A2 - Structura recomandată a proiectului

```
lab06/
├── .venv/                              # mediu virtual Python (nu se include in repo)
├── requirements.txt                    # dependente Python
│
├── cerinta_3_1_conectare.py
├── cerinta_3_2_patrat.py
├── cerinta_3_3_senzori.py
├── cerinta_3_4_stop_obstacol.py
├── cerinta_3_5_braitenberg.py
├── cerinta_3_6_wall_following.py
│
└── tema/
    ├── README.md                       # descriere comportament + observatii
    ├── tema_a_recuperare.py
    ├── tema_b_logging.py
    ├── tema_b_grafice.py               # genereaza graficele din CSV
    ├── tema_b_log_braitenberg.csv      # generat la rulare (nu e obligatoriu in repo)
    ├── tema_c_explorer.py
    └── tema_d_bonus_iubire.py
```

> **Notă:** Fișierele `.venv/`, `*.csv` și `*.png` generate la rulare nu trebuie incluse în repository. Adăugați un fișier `.gitignore` cu aceste excluderi (cf. Laboratorul #01).

---

### A3 - Referință rapidă API CoppeliaSim (Python)

| Operație                  | Apel API                                             | Returnează                        |
| ------------------------- | ---------------------------------------------------- | --------------------------------- |
| Obținere handle obiect    | `sim.getObject('/cale/obiect')`                      | `int`                             |
| Start simulare            | `sim.startSimulation()`                              | -                                 |
| Stop simulare             | `sim.stopSimulation()`                               | -                                 |
| Setare viteză motor       | `sim.setJointTargetVelocity(handle, rad_s)`          | -                                 |
| Citire senzor proximitate | `sim.readProximitySensor(handle)`                    | `(result, dist, pt, obj, normal)` |
| Poziție obiect în lume    | `sim.getObjectPosition(handle, sim.handle_world)`    | `[x, y, z]`                       |
| Orientare obiect (Euler)  | `sim.getObjectOrientation(handle, sim.handle_world)` | `[α, β, γ]` rad                   |
| Timp simulare curent      | `sim.getSimulationTime()`                            | `float` s                         |
| Versiune simulator        | `sim.getInt32Param(sim.intparam_program_version)`    | `int`                             |

---

### A4 - Harta senzorilor Pioneer P3-DX

Diagramă orientativă - vedere de sus (numerotare în sens orar, începând din față-stânga):

```
                      FAȚĂ
            [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]
           ____________________________________________
          /    \                                /    \
         / S[0] \  S[1]  S[2]  S[3]  S[4]  S[5] / S[6]\
        |        |================================|        |
   [15] | S[15]  |                               | S[7]  | [7]
        |        |       CORP ROBOT              |        |
   [14] | S[14]  |                               | S[8]  | [8]
        |        |================================|        |
         \      /  S[13] S[12] S[11] S[10]  S[9] \      /
          \    /                                    \    /
           [15] [14] [13] [12] [11] [10]  [9]  [8]
                      SPATE
```

> **Atenție:** Aceasta este o schemă conceptuală. Validați maparea exactă experimental prin cerința 3.3 - plasați obiecte în diferite direcții față de robot și observați care indecși se activează.

---

### A5 - Resurse suplimentare și tutoriale

| #   | Resursă                                                                                | Tip                   | Link                                                                     |
| --- | -------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------ |
| R1  | Hrithik Verma - *CoppeliaSim Tutorial Playlist* (de la instalare la simulări avansate) | YouTube               | https://www.youtube.com/playlist?list=PLOQhCaBjYnsf-PpKAUX0hfNXqZT637i1w |
| R2  | Northwestern Mechatronics Wiki - *CoppeliaSim Introduction & Getting Started*          | Ghid web              | https://hades.mech.northwestern.edu/index.php/CoppeliaSim_Introduction   |
| R3  | Coppelia Robotics - *ZMQ Remote API: overview și exemple Python*                       | Documentație oficială | https://manual.coppeliarobotics.com/en/zmqRemoteApiOverview.htm          |
| R4  | Chair of Cyber-Physical Systems, Unileoben - *CoppeliaSim Tutorial*                    | Tutorial academic     | https://cps.unileoben.ac.at/coppeliasim-tutorial/                        |
