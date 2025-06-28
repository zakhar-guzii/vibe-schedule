import pandas as pd
import networkx as nx
from itertools import combinations
from src.load_data import prep_data
from config import CLASSROOMS, time_for_lesson

def build_conflict_graph(events: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(events.index)

    for i, j in combinations(events.index, 2):
        u, v = events.loc[i], events.loc[j]

        if set(u['Студенти']) & set(v['Студенти']):
            G.add_edge(i, j)
            continue
        if u['Викладач'] == v['Викладач']:
            G.add_edge(i, j)
            continue
        if (u['Start'] < v['End']) and (v['Start'] < u['End']):
            G.add_edge(i, j)
            continue

    return G

def assign_rooms_by_coloring(events: pd.DataFrame) -> pd.DataFrame:
    G     = build_conflict_graph(events)
    color = nx.coloring.greedy_color(G, strategy='largest_first')

    needed    = max(color.values()) + 1
    available = len(CLASSROOMS)
    if needed > available:
        raise ValueError(f"Потрібно {needed} аудиторій, а є тільки {available}.")

    out = events.copy()
    out['RoomAssigned'] = [CLASSROOMS[color[idx]] for idx in out.index]
    return out


