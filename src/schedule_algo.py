import pandas as pd
import networkx as nx
from itertools import combinations
from src.load_data import prep_data
from config import CLASSROOMS, time_for_lesson


def build_conflict_graph(events: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(events.index)

    for i, j in combinations(events.index, 2):
        u = events.loc[i]
        v = events.loc[j]

        if set(u['Студенти']) & set(v['Студенти']):
            G.add_edge(i, j)
            continue

        if u.get('Викладач') == v.get('Викладач'):
            G.add_edge(i, j)
            continue

        if (u['Start'] < v['End']) and (v['Start'] < u['End']):
            G.add_edge(i, j)
            continue

    return G


def assign_rooms_by_coloring(events: pd.DataFrame) -> pd.DataFrame:
    G = build_conflict_graph(events)
    color = nx.coloring.greedy_color(G, strategy='largest_first')

    needed = max(color.values()) + 1
    available = len(CLASSROOMS)
    if needed > available:
        raise ValueError(
            f"Потрібно мінімум {needed} аудиторій, "
            f"а в наявності лише {available}."
        )

    out = events.copy()
    out['RoomAssigned'] = [CLASSROOMS[color[idx]] for idx in out.index]
    return out


def main():
    events = prep_data()

    if 'Період' in events.columns:
        events = events.rename(columns={'Період': 'Period'})
    elif 'Номер пари' in events.columns:
        events = events.rename(columns={'Номер пари': 'Period'})

    if 'Period' not in events.columns:
        raise KeyError(f"У DataFrame немає стовпця 'Period'. Є тільки: {events.columns.tolist()}")

    slot_times = time_for_lesson()
    events['Start'] = events['Period'].map(lambda p: slot_times[p][0])
    events['End'] = events['Period'].map(lambda p: slot_times[p][1])

    scheduled = assign_rooms_by_coloring(events)

    cols = ['Дисципліна', 'Група', 'Викладач', 'Period', 'Start', 'End', 'RoomAssigned']
    print(scheduled[cols].to_string(index=False))


if __name__ == '__main__':
    main()
