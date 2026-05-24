# Laborator 10 – Prelucrarea limbajului natural: Clasificarea textelor

---

## Cuprins

- [Laborator 10 – Prelucrarea limbajului natural: Clasificarea textelor](#laborator-10--prelucrarea-limbajului-natural-clasificarea-textelor)
  - [Cuprins](#cuprins)
  - [1. Obiective](#1-obiective)
  - [2. Fundamente teoretice](#2-fundamente-teoretice)
    - [2.1 Ce este prelucrarea limbajului natural?](#21-ce-este-prelucrarea-limbajului-natural)
    - [2.2 Preprocesarea textului](#22-preprocesarea-textului)
    - [2.3 Reprezentarea textului prin vectori](#23-reprezentarea-textului-prin-vectori)
      - [2.3.1 Modelul Bag of Words](#231-modelul-bag-of-words)
      - [2.3.2 TF-IDF (Term Frequency – Inverse Document Frequency)](#232-tf-idf-term-frequency--inverse-document-frequency)
    - [2.4 Clasificatori de text](#24-clasificatori-de-text)
      - [2.4.1 Naive Bayes](#241-naive-bayes)
      - [2.4.2 Mașini cu Vectori Suport (SVM)](#242-mașini-cu-vectori-suport-svm)
      - [2.4.3 Regresia Logistică](#243-regresia-logistică)
      - [2.4.4 Păduri Aleatorii (Random Forest)](#244-păduri-aleatorii-random-forest)
    - [2.5 Evaluarea modelelor](#25-evaluarea-modelelor)
  - [3. Instrumentele utilizate](#3-instrumentele-utilizate)
  - [4. Setul de date: 20 Newsgroups](#4-setul-de-date-20-newsgroups)
  - [5. Implementarea de referință](#5-implementarea-de-referință)
  - [6. Sarcini](#6-sarcini)
    - [Sarcina 1 – Clasificare de bază](#sarcina-1--clasificare-de-bază)
    - [Sarcina 2 – Compararea clasificatorilor](#sarcina-2--compararea-clasificatorilor)
    - [Sarcina 3 – Studiul parametrului `ngram_range`](#sarcina-3--studiul-parametrului-ngram_range)
    - [Sarcina 4 – Studiul parametrului `max_features`](#sarcina-4--studiul-parametrului-max_features)
    - [Sarcina 5 (opțională) – Grid search: ngram × max\_features](#sarcina-5-opțională--grid-search-ngram--max_features)
  - [7. Bibliografie](#7-bibliografie)

---

## 1. Obiective

La finalul acestui laborator, veți fi capabili să:

- Înțelegeți principiile fundamentale ale prelucrării limbajului natural (NLP).
- Să aplice tehnici standard de preprocesare a textului.
- Să construiască reprezentări vectoriale ale documentelor folosind TF-IDF.
- Să asambleze și să antreneze un pipeline de clasificare cu _scikit-learn_.
- Să compare performanța mai multor clasificatori de text (Bayes naiv, SVM, regresie logistică, _random forest_).
- Să evalueze modelele folosind metrici standard: acuratețe, precizie, recall, scor F1.
- Să analizeze influența hiperparametrilor (`ngram_range`, `max_features`) asupra calității clasificării.

---

## 2. Fundamente teoretice

### 2.1 Ce este prelucrarea limbajului natural?

**Prelucrarea limbajului natural** (NLP - *Natural Language Processing*) este un domeniu al inteligenței artificiale care se ocupă cu interacțiunea dintre calculatoare și limbajul uman scris sau vorbit. Obiectivul central este acela de a permite mașinilor să înțeleagă, interpreteze și genereze text într-un mod util din punct de vedere aplicativ \[1\].

Aplicațiile NLP sunt omniprezente: motoare de căutare, asistenți virtuali (Siri, Alexa), traducere automată, filtre de spam, analiza sentimentelor pe rețele sociale, sisteme de întrebări și răspunsuri etc. \[2\].

**Clasificarea textelor** este una dintre cele mai fundamentale sarcini NLP. Ea constă în atribuirea automată a unui document de text unei categorii predefinite. Câteva exemple reprezentative:

| Domeniu               | Exemple de categorii                     |
| --------------------- | ---------------------------------------- |
| Filtrare e-mail       | spam / non-spam                          |
| Analiza sentimentelor | pozitiv / negativ / neutru               |
| Clasificare știri     | sport / politică / economie / tehnologie |
| Detecție limbă        | română / engleză / franceză / …          |
| Moderare conținut     | acceptabil / ofensator / discurs al urii |

Procesul general urmează un **pipeline** (flux de prelucrare) standard, de la textul brut până la eticheta de clasă \[1, 2\]:

```
┌─────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│  Text brut  │──▶│    Preprocesare      │──▶│  Vectorizare     │
│             │   │  (tokenizare,        │   │  (Bag of Words   │
│ "Racheta a  │   │   lowercase,         │   │   sau TF-IDF)    │
│  decolat    │   │   eliminare          │   │                  │
│  cu succes" │   │   stop words)        │   │ [0, 0.3, 0.7, …] │
└─────────────┘   └──────────────────────┘   └────────┬─────────┘
                                                       │
                  ┌───────────────────┐                │
                  │    Predicție      │◀───────────────┤
                  │  (ex: sci.space)  │  ┌─────────────────────┐
                  │                   │  │    Clasificator     │
                  └───────────────────┘  │  (NB / SVM / LR)   │
                                         └─────────────────────┘
```

*Figura 1. Pipeline-ul standard pentru clasificarea textelor.*

---

### 2.2 Preprocesarea textului

Textul brut conține mult *zgomot* (*noise*) care nu contribuie la clasificare. Etapele tipice de preprocesare sunt \[2, 3\]:

1. **Conversia la minuscule** (*lowercasing*): `"Python"` → `"python"`. Reduce dimensionalitatea vocabularului prin unificarea formelor cu majusculă și fără.
2. **Eliminarea punctuației și a caracterelor speciale**: `"Hello, world!"` → `"Hello world"`.
3. **Tokenizarea**: împărțirea textului în unități individuale (*tokeni*) - de regulă cuvinte.
4. **Eliminarea cuvintelor de oprire** (*stop words*): cuvintele frecvente dar lipsite de conținut semantic (articole, prepoziții, conjuncții: *the*, *a*, *is*, *în*, *și*). Acestea apar în aproape orice text și nu ajută la discriminarea categoriilor.
5. **Stemming / Lematizare**: reducerea cuvintelor la rădăcina sau forma de bază. Exemplu: *„alergând"*, *„aleargă"*, *„alergat"* → *„alerg"*. Reduce dispersia vocabularului.

> **Notă practică:** `TfidfVectorizer` din scikit-learn efectuează automat tokenizarea și conversia la minuscule. Eliminarea cuvintelor de oprire se activează prin `stop_words='english'` (sau o listă personalizată pentru alte limbi).

---

### 2.3 Reprezentarea textului prin vectori

Algoritmii de învățare automată operează pe vectori numerici de dimensiune fixă, nu pe șiruri de caractere. Este necesară o transformare care să mapeze fiecare document pe un astfel de vector \[1\].

#### 2.3.1 Modelul Bag of Words

**Bag of Words (BoW)** este cea mai simplă reprezentare vectorială. Fiecare document este descris printr-un vector de frecvențe ale termenilor din vocabularul global, **fără a ține cont de ordinea acestora** - documentul este tratat ca o „pungă de cuvinte" \[1\]:

```
Documente:
  D1: "câinele aleargă repede"
  D2: "pisica doarme liniștit"
  D3: "câinele și pisica se joacă"

Vocabular (sortat): [aleargă, câinele, doarme, joacă, liniștit, pisica, repede, se, și]

Matrice BoW:
         aleargă  câinele  doarme  joacă  liniștit  pisica  repede  se  și
    D1  [  1        1        0       0       0         0       1      0   0 ]
    D2  [  0        0        1       0       1         1       0      0   0 ]
    D3  [  0        1        0       1       0         1       0      1   1 ]
```

**Limitele BoW:**

- Nu ține cont de ordinea cuvintelor și pierde contextul sintactic.
- Cuvintele frecvente în toate documentele (ex: *„și"*, *„este"*, *„the"*) primesc pondere mare, deși sunt puțin informative semantic.
- A doua limitare este corectată de schema TF-IDF.

#### 2.3.2 TF-IDF (Term Frequency – Inverse Document Frequency)

**TF-IDF** este o schemă de ponderare care reflectă importanța unui termen atât față de documentul curent, cât și față de colecția întreagă \[4\]. Ideea centrală: un termen este valoros dacă apare **des în documentul de interes**, dar **rar în restul colecției**.

**Term Frequency (TF)** măsoară cât de frecvent apare un termen $t$ într-un document $d$. Există mai multe variante:

*Varianta clasică (normalizată):*

$$
\text{TF}(t, d) = \frac{\text{numărul de apariții ale lui } t \text{ în } d}{\text{numărul total de termeni din } d}
$$

*Varianta logaritmică* (`sublinear_tf=True` în scikit-learn) - atenuează influența termenilor extrem de frecvenți:

$$\text{TF}_{\log}(t, d) = \log\!\bigl(1 + \text{count}(t, d)\bigr)$$

Această variantă este preferată în practică deoarece un termen care apare de 100 de ori nu ar trebui să aibă o pondere de 100 de ori mai mare față de unul care apare o singură dată. **Implementarea din acest laborator folosește varianta logaritmică** (`sublinear_tf=True`).

**Inverse Document Frequency (IDF)** penalizează termenii care apar în multe documente (deci sunt slab discriminatori). Formula *smoothed* din scikit-learn \[8\] este:

$$
\text{IDF}(t) = \log\!\left(\frac{1 + N}{1 + \text{df}(t)}\right) + 1
$$

unde $N$ este numărul total de documente, iar $\text{df}(t)$ este numărul de documente care conțin termenul $t$. Cei doi termeni de netezire au roluri distincte: `+1` din **numitor** evită împărțirea la zero pentru termenii absenți din colecție, iar `+1` adăugat **în afara logaritmului** garantează că termenii prezenți în toate documentele primesc IDF $= \log(1)+1 = 1$ (nu zero), astfel că nu sunt complet eliminați din ponderare.

**Scorul TF-IDF** este produsul celor două componente:

$$
\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)
$$

**Normalizare L2:** după calcul, `TfidfVectorizer` împarte implicit fiecare vector-document la norma sa euclidiană (`norm='l2'`), astfel că $\|\mathbf{v}_d\|_2 = 1$. Normalizarea elimină efectul lungimii documentului: un text de 1.000 de cuvinte nu domină unul de 100 de cuvinte doar prin volum brut.

```
Intuiție vizuală - colecție de articole de sport, politică, știință:

Termenul „fotbal":
  ├── TF ridicat în articolele de sport     ✓
  └── IDF ridicat (apare rar în restul)     ✓
      ──────────────────────────────────────
      TF-IDF = MARE  →  termen discriminator ✓

Termenul „și":
  ├── TF ridicat în toate documentele       ✓
  └── IDF SCĂZUT (apare peste tot)          ✗
      ──────────────────────────────────────
      TF-IDF = MIC   →  termen nediscriminator ✗
```

*Figura 2. Intuiția din spatele scorului TF-IDF: un termen este informativ dacă este specific unui document, nu universal.*

Matricea TF-IDF finală are dimensiunea $|\mathcal{D}| \times |\mathcal{V}|$ (documente × vocabular) și este de obicei **extrem de rară** (*sparse matrix*), deoarece fiecare document conține doar un subset mic din vocabularul total. scikit-learn stochează eficient această matrice în format CSR (*Compressed Sparse Row*).

---

### 2.4 Clasificatori de text

#### 2.4.1 Naive Bayes

**Naive Bayes** este un clasificator probabilistic bazat pe teorema lui Bayes \[5\]. Este numit *„naiv"* deoarece presupune **independența condițională** a atributelor (cuvintelor) față de clasă - o ipoteză simplificatoare care, deși rar adevărată în practică, conduce la un clasificator remarcabil de eficient \[1\].

**Teorema lui Bayes:**

$$
P(c \mid \mathbf{d}) = \frac{P(\mathbf{d} \mid c) \cdot P(c)}{P(\mathbf{d})}
$$

unde $c$ este clasa (categoria), iar $\mathbf{d}$ este documentul. Deoarece $P(\mathbf{d})$ este constantă pentru toți clasificatorii candidați, alegem clasa care maximizează numărătorul:

`MultinomialNB` modelează distribuția frecvențelor cuvintelor: termenul $t$ care apare de $f_{t,d}$ ori în document contribuie de $f_{t,d}$ ori la probabilitate. Formula corectă este:

$$
\hat{c} = \underset{c}{\arg\max} \; P(c) \cdot \prod_{t \in V} P(t \mid c)^{f_{t,d}}
$$

unde $V$ este vocabularul, iar $f_{t,d}$ este frecvența termenului $t$ în documentul $d$ (zero pentru termenii absenți). În practică, se lucrează cu **logaritmi** pentru a evita underflow-ul numeric la înmulțirea multor probabilități mici:

$$
\hat{c} = \underset{c}{\arg\max} \left[ \log P(c) + \sum_{t \in V} f_{t,d} \cdot \log P(t \mid c) \right]
$$

**`MultinomialNB`** (implementarea din scikit-learn) utilizează frecvențele termenilor și este adecvat pentru date text. Probabilitățile $P(t \mid c)$ se estimează prin numărul de apariții al termenului $t$ în documentele din clasa $c$, cu netezire Laplace pentru a evita probabilitățile zero.

> **Notă de implementare:** `MultinomialNB` este conceput teoretic pentru frecvențe brute de cuvinte. În această implementare, caracteristicile de intrare sunt scoruri TF-IDF cu transformare logaritmică și normalizate L2 - valorile rămân ≥ 0, deci modelul funcționează numeric, dar deviază de la ipotezele statistice stricte ale modelului multinomial. Această combinație este acceptabilă și larg răspândită în practică \[1\].

**Avantaje:** antrenament extrem de rapid, scalabil la colecții mari, funcționează bine chiar și cu seturi de date mici.
**Dezavantaje:** ipoteza de independență este rareori respectată în realitate; performanța poate fi inferioară modelelor discriminative.

#### 2.4.2 Mașini cu Vectori Suport (SVM)

**Support Vector Machine (SVM)** este un clasificator care caută **hiperplanul cu marjă maximă** ce separă clasele în spațiul de caracteristici \[6\]. Ideea geometrică este intuitivă:

```
         Clasa A (●)     |     Clasa B (○)
                         |
              ●    ●     |
           ●          ←marjă→        ○
        ●          ════════════         ○
           ●          ←marjă→        ○
              ●    ●     |     ○    ○
                         |
                    hiperplan optim
                  (maximizează marja)
```

*Figura 3. SVM caută hiperplanul care maximizează distanța față de cele mai apropiate puncte din fiecare clasă - numite vectori suport.*

Datele reale nu sunt niciodată perfect separabile, astfel că `LinearSVC` implementează **soft-margin SVM**, care permite erori de clasificare controlate prin variabilele de relaxare $\xi_i \geq 0$:

$$
\min_{\mathbf{w}, b, \boldsymbol{\xi}} \frac{1}{2} \|\mathbf{w}\|^2 + C\sum_i \xi_i \quad \text{s.t.} \quad y_i(\mathbf{w} \cdot \mathbf{x}_i + b) \geq 1 - \xi_i, \; \xi_i \geq 0, \; \forall i
$$

Hiperparametrul $C > 0$ controlează **compromisul marjă–eroare**: un $C$ mic tolerează mai multe erori (marjă mai largă, risc de subadaptare); un $C$ mare penalizează sever erorile (marjă mai îngustă, risc de supraadaptare). Valoarea implicită în scikit-learn este $C = 1{,}0$.

**`LinearSVC`** este deosebit de eficientă pentru clasificarea textelor: în spații de dimensionalitate înaltă (mii de caracteristici TF-IDF) un kernel liniar este adesea suficient și considerabil mai rapid decât kernel-urile neliniare \[1\].

**Avantaje:** performanță ridicată pe date text, robust la dimensionalitate înaltă, eficient în timp de clasificare.
**Dezavantaje:** mai lent la antrenament decât Naive Bayes; necesită tuning pentru $C$; nu produce probabilități calibrate direct.

#### 2.4.3 Regresia logistică

**Regresia logistică** este un model liniar de clasificare probabilistică. Pentru clasificare binară, estimează probabilitatea de apartenența la clasa pozitivă prin funcția **sigmoid** \[2\]:

$$
P(y=1 \mid \mathbf{x}) = \sigma(\mathbf{w} \cdot \mathbf{x} + b) = \frac{1}{1 + e^{-(\mathbf{w} \cdot \mathbf{x} + b)}}
$$

```
    1 ┤                                    ╭─────────────
      │                              ╭─────╯
  0.5 ┤ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╭───╯
      │                   ╭─────╯
    0 ┤ ──────────────────╯
      └────────────────────────────────────────────────▶
      -∞                  0                           +∞
                       w·x + b
```

*Figura 4. Funcția sigmoid mapează orice valoare reală în intervalul (0, 1), interpretată ca probabilitate de clasificare.*

Parametrii $\mathbf{w}$ se estimează prin maximizarea log-verosimilității (echivalent cu minimizarea entropiei încrucișate) cu un termen de regularizare $L_2$ pentru a preveni supraadaptarea (*overfitting*). Pentru clasificare multi-clasă, scikit-learn extinde automat modelul prin strategia *one-vs-rest* sau *multinomial* (funcție softmax).

**Avantaje:** interpretabil (coeficienții $\mathbf{w}$ indică importanța fiecărui cuvânt pentru fiecare clasă), oferă probabilități calibrate, antrenament rapid.
**Dezavantaje:** necesită regularizare atentă pe date de dimensionalitate înaltă; poate fi depășit de SVM în acuratețe.

#### 2.4.4 Păduri Aleatorii (Random Forest)

**Random forest** este un **ansamblu de arbori de decizie** antrenați pe subseturi aleatorii ale datelor (*bootstrap aggregation* - bagging) \[1\]. Fiecare arbore votează independent o clasă, iar clasa majoritară devine predicția finală:

```
      Date antrenament
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
 Arbore   Arbore   Arbore   … (n_estimators)
    1        2        3
    │        │        │
    ▼        ▼        ▼
  cls_A    cls_A    cls_B
    └────────┼────────┘
             ▼
      Vot majoritar → cls_A
```

*Figura 5. Random forest agreghează predicțiile mai multor arbori de decizie prin vot majoritar.*

În contextul clasificării textelor, *random forest* are o limitare structurală importantă: la fiecare nod al unui arbore se selectează aleatoriu doar $\sqrt{|\mathcal{V}|}$ caracteristici din vocabularul total $|\mathcal{V}|$ (de ordinul zecilor de mii). La fiecare split, marea majoritate a caracteristicilor relevante este ignorată - motiv pentru care RF performează de obicei **mai slab** decât SVM sau *regresia logistică* pe date text sparse \[1\]. Este inclus în laborator tocmai pentru a ilustra această limitare.

**Avantaje:** robust la zgomot, nu necesită scalarea caracteristicilor, ușor de paralelizat.
**Dezavantaje:** performanță slabă pe date text de dimensionalitate înaltă; lent la antrenament față de modelele liniare.

---

### 2.5 Evaluarea modelelor

Evaluarea unui clasificator depășește simpla acuratețe globală, mai ales când clasele sunt dezechilibrate \[1, 3\]. Metricile standard sunt:

| Metrică       | Formulă                              | Interpretare                                             |
| ------------- | ------------------------------------ | -------------------------------------------------------- |
| **Acuratețe** | $\dfrac{TP + TN}{TP + TN + FP + FN}$ | Proporția totală a predicțiilor corecte                  |
| **Precizie**  | $\dfrac{TP}{TP + FP}$                | Din toate predicțiile pozitive, câte sunt corecte?       |
| **Recall**    | $\dfrac{TP}{TP + FN}$                | Din toate exemplele pozitive reale, câte au fost găsite? |
| **Scor F1**   | $\dfrac{2 \cdot P \cdot R}{P + R}$   | Media armonică a preciziei și recall-ului                |

unde: TP = *True Positives*, TN = *True Negatives*, FP = *False Positives*, FN = *False Negatives*.

**Matricea de confuzie** este o tabelă $K \times K$ (pentru $K$ clase) în care elementul $(i, j)$ reprezintă numărul de documente din clasa reală $i$ clasificate în clasa prezisă $j$. Diagonala principală conține clasificările corecte; elementele extradiagonale sunt erorile de clasificare \[1\].

```
                   PREZIS
              sp.  hoc. pol. gfx
         ┌───────────────────────┐
    sp.  │  95   1    2    2   │  ← 95 documente sci.space clasificate corect
R  hoc. │   0   98   1    1   │
E  pol. │   3    2   87   8   │  ← 8 erori: talk.politics confundat cu comp.graphics
A  gfx  │   2    1    5   92  │
L        └───────────────────────┘
```

*Figura 6. Exemplu de matrice de confuzie pentru 4 categorii. Valorile mari pe diagonală indică un clasificator bun.*

---

## 3. Instrumentele utilizate

| Bibliotecă     | Versiune minimă | Utilizare în laborator                                   |
| -------------- | --------------- | -------------------------------------------------------- |
| `scikit-learn` | 1.0             | Pipeline NLP, TF-IDF, clasificatori, metrici de evaluare |
| `numpy`        | 1.21            | Operații numerice, matrice de rezultate                  |
| `matplotlib`   | 3.4             | Grafice de comparație, vizualizarea matricei de confuzie |
| `seaborn`      | 0.11            | Heatmap pentru studiul de grid (Sarcina 5, opțional)     |

Instalare:

```bash
pip install scikit-learn numpy matplotlib seaborn
```

---

## 4. Setul de date: 20 Newsgroups

**20 Newsgroups** este un set de date clasic în NLP, creat de Ken Lang (1995) \[9\] și utilizat extensiv atât în cercetare cât și în educație. Conține aproximativ 18.000 de postări din grupuri de discuție online (*newsgroups*), distribuite în **20 de categorii** tematice:

```
20 Newsgroups
├── Calculatoare: comp.graphics, comp.os.ms-windows.misc,
│                comp.sys.ibm.pc.hardware, comp.sys.mac.hardware,
│                comp.windows.x
├── Știință:      sci.crypt, sci.electronics, sci.med, sci.space
├── Recreere:     rec.autos, rec.motorcycles,
│                rec.sport.baseball, rec.sport.hockey
├── Politică:     talk.politics.guns, talk.politics.mideast,
│                talk.politics.misc
├── Religie:      talk.religion.misc, alt.atheism,
│                soc.religion.christian
└── Diverse:      misc.forsale
```

**Avantajele** acestui set de date pentru laborator:

- Disponibil direct în scikit-learn prin `fetch_20newsgroups()` - fără descărcare sau procesare manuală.
- Volum suficient (~11.000 exemple de antrenament, ~7.500 de test) pentru a observa diferențe semnificative între modele.
- Categoriile sunt distincte tematic, dar unele sunt similare (ex: `sci.space` vs. `sci.med`), oferind atât cazuri ușoare cât și dificile de clasificare.
- Opțiunea `remove=('headers', 'footers', 'quotes')` elimină metadatele tehnice, forțând modelul să se bazeze pe conținutul textual real.

În acest laborator vom folosi **4 categorii** pentru eficiență computațională:

```python
CATEGORII = ['sci.space', 'rec.sport.hockey', 'talk.politics.guns', 'comp.graphics']
```

Aceste 4 categorii oferă o diversitate tematică bună: știință spațială, sport, politică și informatică grafică.

> **De ce split train/test?** Modelul este antrenat exclusiv pe datele de antrenament; evaluarea se face pe date **nevăzute** (test), simulând comportamentul în producție. Evaluarea pe datele de antrenament ar produce metrici artificial optimiste, fără valoare predictivă.

---

## 5. Implementarea de referință

Fișierul `nlp_classification.py` conține implementarea completă. Structura modulului urmează același tipar modular ca laboratoarele anterioare:

```
nlp_classification.py
├── incarca_date()                   - încarcă setul 20 Newsgroups (train/test split)
├── construieste_pipeline()          - asamblează TfidfVectorizer + clasificator
├── evalueaza_model()                - antrenează, evaluează, returnează metrici
├── plot_matrice_confuzie()          - vizualizează matricea de confuzie
├── plot_comparatie()                - grafic bare cu acuratețile
├── studiu_clasificatori()           - Sarcina 2: NB vs SVM vs LR vs RF
├── studiu_ngram()                   - Sarcina 3: variația ngram_range
├── studiu_max_features()            - Sarcina 4: variația max_features
└── studiu_grid()                    - Sarcina 5 (opțional): heatmap ngram × features
```

> **De ce `Pipeline` și nu pași separați?** Dacă am apela `tfidf.fit_transform()` pe întregul dataset (train + test) înainte de antrenament, vocabularul și statisticile IDF ar fi influențate de datele de test - o formă de **scurgere de date** (*data leakage*) care produce metrici artificial optimiste. `Pipeline` asigură că `TfidfVectorizer.fit()` se apelează **exclusiv** pe datele de antrenament, iar `transform()` se aplică separat pe setul de test.

```python
# nlp_classification.py  -  referință pentru Laborator 10
import time
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)

CATEGORII = ['sci.space', 'rec.sport.hockey', 'talk.politics.guns', 'comp.graphics']


def incarca_date():
    train = fetch_20newsgroups(
        subset='train', categories=CATEGORII,
        remove=('headers', 'footers', 'quotes')
    )
    test = fetch_20newsgroups(
        subset='test', categories=CATEGORII,
        remove=('headers', 'footers', 'quotes')
    )
    return train, test


def construieste_pipeline(clasificator, ngram_range=(1, 1), max_features=None):
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            stop_words='english',
            sublinear_tf=True       # aplică log(1 + TF) pentru a comprima frecvențele mari
        )),
        ('clf', clasificator)
    ])


def evalueaza_model(pipeline, train, test, verbose=True):
    start = time.time()
    pipeline.fit(train.data, train.target)
    durata = time.time() - start
    pred = pipeline.predict(test.data)
    acc = accuracy_score(test.target, pred)
    if verbose:
        print(f"Acuratețe: {acc:.4f}  |  Timp antrenament: {durata:.2f}s")
        print(classification_report(test.target, pred, target_names=train.target_names))
    return acc, pred, durata


def plot_matrice_confuzie(pred, test, titlu="Matricea de confuzie"):
    cm = confusion_matrix(test.target, pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=test.target_names)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp.plot(ax=ax, colorbar=True, cmap='Blues')
    ax.set_title(titlu)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig(f"matrice_{titlu[:20].replace(' ', '_')}.png", dpi=150)
    plt.show()


def plot_comparatie(etichete, acurateti, titlu, xlabel):
    fig, ax = plt.subplots(figsize=(8, 5))
    culori = plt.cm.tab10(np.linspace(0, 1, len(etichete)))
    bare = ax.bar(etichete, acurateti, color=culori, edgecolor='black')
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Acuratețe')
    ax.set_xlabel(xlabel)
    ax.set_title(titlu)
    for bar, val in zip(bare, acurateti):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(f"{titlu[:25].replace(' ', '_')}.png", dpi=150)
    plt.show()


def studiu_clasificatori(train, test):
    print("\n" + "=" * 60)
    print("SARCINA 2 – Compararea clasificatorilor")
    print("=" * 60)
    clasificatori = {
        'Naive Bayes':        MultinomialNB(),
        'LinearSVC':          LinearSVC(max_iter=2000),
        'Reg. Logistică':     LogisticRegression(max_iter=1000, solver='saga'),
        'Random Forest':      RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
    }
    acurateti, durate, etichete, rezultate = [], [], [], []
    for nume, clf in clasificatori.items():
        print(f"\n--- {nume} ---")
        pipeline = construieste_pipeline(clf)
        acc, pred, durata = evalueaza_model(pipeline, train, test)
        rezultate.append((acc, pred, nume))
        acurateti.append(acc)
        durate.append(durata)
        etichete.append(nume)
    print("\n" + "-" * 50)
    print(f"{'Clasificator':<22} {'Acuratețe':>10} {'Timp (s)':>10}")
    print("-" * 50)
    for nume, acc, dur in zip(etichete, acurateti, durate):
        print(f"{nume:<22} {acc:>10.4f} {dur:>10.2f}")
    print("-" * 50)
    cel_mai_bun = max(rezultate, key=lambda x: x[0])
    print(f"\nCel mai bun: {cel_mai_bun[2]} (acc={cel_mai_bun[0]:.4f})")
    plot_matrice_confuzie(cel_mai_bun[1], test,
                          f"{cel_mai_bun[2]} – Matrice de confuzie")
    plot_comparatie(etichete, acurateti, "Compararea clasificatorilor", "Clasificator")


def studiu_ngram(train, test):
    print("\n" + "=" * 60)
    print("SARCINA 3 – Variația ngram_range")
    print("=" * 60)
    ngram_configs = [(1, 1), (1, 2), (2, 2), (1, 3)]
    acurateti, etichete = [], []
    for ng in ngram_configs:
        pipeline = construieste_pipeline(LinearSVC(max_iter=2000), ngram_range=ng)
        print(f"\nngram_range = {ng}")
        acc, _, _ = evalueaza_model(pipeline, train, test)
        acurateti.append(acc)
        etichete.append(str(ng))
    plot_comparatie(etichete, acurateti, "Influența ngram_range (SVM)", "ngram_range")


def studiu_max_features(train, test):
    print("\n" + "=" * 60)
    print("SARCINA 4 – Variația max_features")
    print("=" * 60)
    valori = [100, 500, 1000, 5000, 10000, None]
    acurateti, etichete = [], []
    for mf in valori:
        pipeline = construieste_pipeline(LinearSVC(max_iter=2000), max_features=mf)
        label = str(mf) if mf is not None else 'toate'
        print(f"\nmax_features = {label}")
        acc, _, _ = evalueaza_model(pipeline, train, test)
        acurateti.append(acc)
        etichete.append(label)
    plot_comparatie(etichete, acurateti, "Influența max_features (SVM)", "max_features")


def studiu_grid(train, test):
    print("\n" + "=" * 60)
    print("SARCINA 5 (opțional) – Grid ngram × max_features")
    print("=" * 60)
    try:
        import seaborn as sns
    except ImportError:
        print("Instalați seaborn: pip install seaborn")
        return
    ngrams = [(1, 1), (1, 2), (1, 3)]
    features = [500, 2000, 5000, 10000]
    rezultate = np.zeros((len(ngrams), len(features)))
    for i, ng in enumerate(ngrams):
        for j, mf in enumerate(features):
            pipeline = construieste_pipeline(LinearSVC(max_iter=2000),
                                             ngram_range=ng, max_features=mf)
            acc, _, _ = evalueaza_model(pipeline, train, test, verbose=False)
            rezultate[i, j] = acc
            print(f"  ngram={ng}, max_features={mf}: acc={acc:.4f}")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(rezultate, annot=True, fmt='.3f', cmap='YlOrRd',
                xticklabels=features,
                yticklabels=[str(ng) for ng in ngrams], ax=ax)
    ax.set_xlabel('max_features')
    ax.set_ylabel('ngram_range')
    ax.set_title('Acuratețe (SVM) – Grid ngram × max_features')
    plt.tight_layout()
    plt.savefig('grid_ngram_features.png', dpi=150)
    plt.show()


if __name__ == '__main__':
    print("Se încarcă datele 20 Newsgroups...")
    train, test = incarca_date()
    print(f"Train: {len(train.data)} documente | Test: {len(test.data)} documente")

    print("\n" + "=" * 60)
    print("SARCINA 1 – Clasificare de bază (Naive Bayes)")
    print("=" * 60)
    pipeline_baza = construieste_pipeline(MultinomialNB())
    acc, pred, _ = evalueaza_model(pipeline_baza, train, test)
    plot_matrice_confuzie(pred, test, "Naive Bayes – Matrice de confuzie")

    studiu_clasificatori(train, test)
    studiu_ngram(train, test)
    studiu_max_features(train, test)
    studiu_grid(train, test)
```

---

## 6. Sarcini

### Sarcina 1 – Clasificare de bază

Rulați pipeline-ul de bază folosind **Naive Bayes** cu parametrii impliciți ai vectorizorului TF-IDF (`ngram_range=(1,1)`, `max_features=None`, `stop_words='english'`).

**Raportați și interpretați:**

1. Acuratețea globală (*accuracy*) pe setul de test.
2. Raportul de clasificare complet (`classification_report`) - precizie, recall și scorul F1 pentru fiecare categorie.
3. Matricea de confuzie - care perechi de categorii sunt cel mai frecvent confundate? Oferiți o explicație semantică.

> **Indiciu:** Analizați matricea de confuzie fără prejudecăți - nu presupuneți dinainte care categorii vor fi confundate. Categoriile cu vocabular parțial suprapus tind să fie mai frecvent confundate. Identificați perechile problematice pe baza rezultatelor obținute și oferiți o explicație semantică.

---

### Sarcina 2 – Compararea clasificatorilor

Rulați `studiu_clasificatori()` pentru a compara patru clasificatori cu aceeași configurație TF-IDF (`ngram_range=(1,1)`, `stop_words='english'`):

| Clasificator       | Clasa scikit-learn                                 | Note                                                                    |
| ------------------ | -------------------------------------------------- | ----------------------------------------------------------------------- |
| Naive Bayes        | `MultinomialNB()`                                  | Clasificator probabilistic                                              |
| SVM liniar         | `LinearSVC(max_iter=2000)`                         | Performanță ridicată pe date text sparse                                |
| Regresie logistică | `LogisticRegression(max_iter=1000, solver='saga')` | Model liniar cu probabilități; `saga` converge mai rapid pe date sparse |
| Păduri Aleatorii   | `RandomForestClassifier(n_estimators=100)`         | Ansamblu de arbori de decizie                                           |

**Raportați:**

1. Tabelul acuratețelor și timpilor de antrenament pentru fiecare clasificator.
2. Graficul de comparație generat automat.
3. Matricea de confuzie pentru **cel mai bun** clasificator.

**Discutați:** Care clasificator oferă cel mai bun raport acuratețe / viteză de antrenament? La ce aplicații ați prefera Naive Bayes în locul SVM, în ciuda acurateții mai scăzute?

---

### Sarcina 3 – Studiul parametrului `ngram_range`

**N-gramele** sunt secvențe continue de $n$ tokeni. Bigramele captează fraze cu sens propriu, cum ar fi *„artificial intelligence"* (care are un înțeles specific față de *„artificial"* și *„intelligence"* separate) \[1\].

| Configurație                     | Tipuri de caracteristici generate | Exemplu                            |
| -------------------------------- | --------------------------------- | ---------------------------------- |
| `(1, 1)` - unigrame              | cuvinte individuale               | `"spațiu"`, `"rachetă"`            |
| `(1, 2)` - uni- și bigrame       | cuvinte + fraze de 2              | `"stație spațială"`                |
| `(2, 2)` - numai bigrame         | fraze de 2 cuvinte                | `"misiune orbitală"`               |
| `(1, 3)` - uni-, bi- și trigrame | include și fraze de 3             | `"stație spațială internațională"` |

> **Notă:** Când `stop_words='english'` este activ împreună cu `ngram_range=(1,2)`, bigramele care conțin cuvinte de oprire la margini sunt eliminate automat (ex: *„of the"* dispare, dar *„machine learning"* este păstrat). Bigramele utile - formate exclusiv din termeni cu conținut semantic - sunt astfel conservate.

Rulați `studiu_ngram()` cu clasificatorul **LinearSVC** (cel mai robust pentru comparații).

**Raportați:**

1. Acuratețele pentru fiecare configurație n-gram.
2. Graficul de comparație.
3. Explicați de ce bigramele pot îmbunătăți sau nu performanța față de unigrame, și de ce vocabularul crește dramatic la `(1, 3)`.

---

### Sarcina 4 – Studiul parametrului `max_features`

`max_features` limitează dimensiunea vocabularului la cei mai frecvenți $k$ termeni. Un vocabular mai mic reduce memoria și timpul de calcul, dar poate elimina termeni importanți.

Rulați `studiu_max_features()` cu valorile: `[100, 500, 1000, 5000, 10000, None]` (unde `None` înseamnă vocabular complet).

**Raportați:**

1. Acuratețele pentru fiecare valoare a lui `max_features`.
2. Graficul de comparație.
3. Identificați **pragul de saturație**: valoarea minimă a lui `max_features` dincolo de care acuratețea se stabilizează. Explicați comportamentul la valori foarte mici (ex: 100 termeni).

> **Întrebare de reflecție:** Un vocabular complet (nentrunchiat) conduce întotdeauna la o acuratețe mai bună? Explicați din perspectiva raportului semnal/zgomot.

---

### Sarcina 5 (opțională) – Grid search: ngram × max\_features

Explorați **interacțiunea** dintre `ngram_range` și `max_features` pe o grilă $3 \times 4$:

- `ngram_range` ∈ {`(1,1)`, `(1,2)`, `(1,3)`}
- `max_features` ∈ {500, 2000, 5000, 10000}

Rulați `studiu_grid()` și interpretați heatmap-ul generat.

**Raportați:**

1. Combinația optimă de hiperparametri (cu acuratețea corespunzătoare).
2. Există interacțiuni neașteptate între cei doi parametri? De exemplu, bigramele cu `max_features` mic pot performa mai prost decât unigramele cu `max_features` mare?
3. Ce concluzie practică puteți trage pentru alegerea hiperparametrilor TF-IDF?

---

## 7. Bibliografie

\[1\] Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press. DOI: [10.1017/CBO9780511809071](https://doi.org/10.1017/CBO9780511809071)

\[2\] Jurafsky, D., & Martin, J. H. (2024). *Speech and Language Processing* (3rd ed., draft). Stanford University. Disponibil la: <https://web.stanford.edu/~jurafsky/slp3/>

\[3\] Bird, S., Klein, E., & Loper, E. (2009). *Natural Language Processing with Python: Analyzing Text with the Natural Language Toolkit*. O'Reilly Media. ISBN: 978-0-596-51649-9

\[4\] Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management*, 24(5), 513–523. DOI: [10.1016/0306-4573(88)90021-0](https://doi.org/10.1016/0306-4573(88)90021-0)

\[5\] Rish, I. (2001). An empirical study of the naive Bayes classifier. *IJCAI 2001 Workshop on Empirical Methods in Artificial Intelligence*, 3(22), 41–46.

\[6\] Cortes, C., & Vapnik, V. (1995). Support-vector networks. *Machine Learning*, 20(3), 273–297. DOI: [10.1007/BF00994018](https://doi.org/10.1007/BF00994018)

\[7\] Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

\[8\] Scikit-learn Documentation. (2024). *sklearn.feature\_extraction.text.TfidfVectorizer*. scikit-learn.org. Disponibil la: <https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html>

\[9\] Lang, K. (1995). NewsWeeder: Learning to filter netnews. In *Proceedings of the 12th International Conference on Machine Learning (ICML 1995)*, pp. 331–339.

---

*Laborator elaborat pentru cursul de Inteligență Artificială. Toate implementările utilizează biblioteci open-source. Setul de date 20 Newsgroups este distribuit sub licență publică \[9\].*
