# Data Directory

This directory contains datasets and caches for the project.

## Structure

- cache/: Auto-populated cache for downloaded datasets (SMS Spam, AG News, IMDb)

## TSP Matrix Format

Provide an N x N distance matrix in plain text format:

```
N
d_1_1 d_1_2 ... d_1_N
d_2_1 d_2_2 ... d_2_N
...
d_N_1 d_N_2 ... d_N_N
```

Example (4 cities):

```
4
0 10 15 20
10 0 35 25
15 35 0 30
20 25 30 0
```

## Coordinate CSV Format

Provide a CSV with x,y columns:

```
x,y
1.5,2.3
3.1,4.2
```
