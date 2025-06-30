# Vibe-Schedule: Automatic Class-Timetabling at KSE

The _vibe-schedule_ project explores algorithms that generate clash-free, capacity-aware class schedules for three academic terms at **Kyiv School of Economics (KSE)**.

---

## 1 Problem Statement

> **Goal:** Assign every course to a _time slot_ and _classroom_ so that
>
> - no student, teacher, or room is double-booked,
> - room capacity constraints are met,
> - the total number of time slots is minimised (or otherwise kept reasonable).

This is a classic **constraint-satisfaction** problem that can be modelled as **graph colouring**.

---

## 2 From Graph Colouring to Timetabling

| Concept    | Timetabling Analogue                         |
| ---------- | -------------------------------------------- |
| **Vertex** | Course (or a specific class meeting)         |
| **Edge**   | Conflict (shared students, teacher, or room) |
| **Colour** | Time slot                                    |

> **Rule:** Adjacent vertices must receive different colours ⇒ conflicting classes never share a slot.

---

## 3 Historical Milestones

| Year               | Milestone                              | Key Idea                                                                                                                                   |
| ------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **1960**           | _Appleby–Blake–Newman_                 | Early **hill climbing** for exam timetables.                                                                                               |
| **1967**           | _Welsh & Powell_                       | Formalised timetabling as **graph colouring**; introduced degree-ordered **greedy** algorithm.                                             |
| **1979**           | _Brélaz DSATUR_                        | Pick vertex with highest colour **sat**uration; improves greedy quality.                                                                   |
| **1990s**          | **Constraint Logic Programming (CLP)** | Model schedules as logical constraints and search systematically.                                                                          |
| **Late 1990s**     | **Genetic Algorithms**                 | Evolve populations of schedules; crossover + mutation reduce clashes.                                                                      |
| **2000 – present** | **Hybrid Meta-heuristics**             | Chains of _Iterative Forward Search → Hill Climbing → Great Deluge → Simulated Annealing_ win international competitions (ITC 2002, 2007). |

---
## Welsh–Powell Greedy Algorithm (Largest Degree First)

The **Welsh–Powell algorithm** is a greedy algorithm for graph coloring, which sequentially assigns colors to graph vertices aiming to minimize the total number of colors used. Formally, given a graph \( G = (V, E) \), the steps are as follows:

### 1. Vertex Sorting
Calculate the degree \( d(v) \) for each vertex \( v \in V \). Sort the vertices in descending order of degrees:

$$
d(v_1) \geq d(v_2) \geq \dots \geq d(v_n)
$$

Vertices with equal degrees may be ordered arbitrarily.

### 2. Assigning the First Color
Select the vertex with the highest degree \( v_1 \) and assign it color \(1\):

$$
c(v_1) = 1
$$

Then sequentially, for each vertex \( v_2, v_3, \dots, v_n \):

- If vertex \( v_i \) is not yet colored and does not share an edge with any vertex already colored with color \(1\), assign:

$$
c(v_i) = 1
$$

### 3. Assigning Subsequent Colors
If uncolored vertices remain, select the uncolored vertex \( v_j \) with the highest degree among the remaining ones and assign it the next available color (e.g., color \(2\)):

$$
c(v_j) = 2
$$

Continue assigning this new color to each remaining uncolored vertex \( v_k \) that has no edges with vertices already assigned this color.

Repeat the procedure, introducing new colors \( 3, 4, \dots \) as needed until all vertices are colored.

---

### Formal Notes
At each iteration, the algorithm selects maximal independent subsets of vertices, coloring each subset identically. This heuristic prioritizes highly connected vertices and guarantees an upper bound for the chromatic number \( \chi(G) \):

$$
\chi(G) \leq \Delta(G) + 1
$$

where \( \Delta(G) \) represents the maximum vertex degree in graph \( G \).



---

## Implementation in Vibe-Schedule

The project leverages Python, NetworkX for graph management, and pandas for data handling. The primary workflow includes:

### Data Preparation
- Processes student groupings, course details, and required weekly class counts from spreadsheets (`load_data.py`).
- Calculates weekly class occurrences, associating students, teachers, and groups accordingly.

### Conflict Graph Construction
- Represents each course as a vertex, identifying conflicts where students or teachers overlap (`schedule_algo.py`).
- Uses a greedy colouring algorithm to assign initial slots, prioritizing vertices by their conflict degree.

### Optimization
- Applies soft optimizations: moving extreme slots to central slots, minimizing gaps between classes.
- Enforces hard constraints, limiting daily classes per student (max. 4/day) and per subject (max. 2/day).

### Room Assignment
- Matches courses with appropriate classrooms, considering class sizes and capacities from predefined configurations (`config.py`).

### Schedule Generation and Export
- Compiles final weekly schedules, exporting as CSV and Excel files for practical usage (`test.py`).

---