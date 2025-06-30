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

## 4 Baseline Greedy Pipeline

1. **Build Conflict Graph**
   - Each course ⇒ vertex
   - Edge if courses share students / teacher / room

2. **Greedy Colouring**
   ```text
   sort vertices by descending degree
   for v in vertices:
       assign the smallest colour not used by neighbours
   

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