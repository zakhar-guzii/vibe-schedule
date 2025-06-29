import ast
import csv
import networkx as nx
import pandas as pd
from config import CLASSROOMS, DAYS

events = []
with open('../data/schedule.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # пар на тиждень
        try:
            weekly = ast.literal_eval(row.get('ПТ', '[]'))
        except (ValueError, SyntaxError):
            weekly = []
        for week_idx, cnt in enumerate(weekly, start=1):
            for _ in range(int(cnt)):
                # читаємо студентів для підрахунку num_students
                try:
                    students = ast.literal_eval(row.get('Список учнів', '[]'))
                except (ValueError, SyntaxError):
                    students = []
                events.append({
                    'id': len(events),
                    'week': week_idx,
                    'group': row['Група'],
                    'subject': row['Дисципліна'],
                    'teacher': row['Викладач'],
                    'students': set(students),
                    'num_students': len(students)             # <<< додано!
                })


def build_conflicts(ev_list):
    G = nx.Graph()
    for ev in ev_list:
        G.add_node(ev['id'], **ev)
    for i, a in enumerate(ev_list):
        for b in ev_list[i + 1:]:
            if a['teacher'] == b['teacher'] or not a['students'].isdisjoint(b['students']):
                G.add_edge(a['id'], b['id'])
    return G


def assign_timeslots(ev_list):
    G = build_conflicts(ev_list)
    color = nx.coloring.greedy_color(G, strategy='largest_first')
    slots_per_day = 8
    assignment = {}
    for ev in ev_list:
        c = color[ev['id']]
        day = c // slots_per_day
        slot = (c % slots_per_day) + 1
        if day >= len(DAYS):
            day = len(DAYS) - 1
        assignment[ev['id']] = (day, slot)
    return assignment


def assign_rooms(ev_list, times):
    room_schedule = {r: set() for r in CLASSROOMS}
    room_assign = {}
    for ev in ev_list:
        tid = ev['id']
        # тепер num_students існує і може бути використаний, якщо треба перевіряти місткість
        needed = ev['num_students']
        d, s = times[tid]
        for room, cap in CLASSROOMS.items():
            # наприклад, можна враховувати місткість:
            # if cap >= needed and (d, s) not in room_schedule[room]:
            if (d, s) not in room_schedule[room]:
                room_assign[tid] = room
                room_schedule[room].add((d, s))
                break
    return room_assign


all_rows = []
for week_idx in range(1, 13):
    week_events = [e for e in events if e['week'] == week_idx]
    if not week_events:
        continue

    times = assign_timeslots(week_events)
    rooms = assign_rooms(week_events, times)

    for ev in week_events:
        d, s = times[ev['id']]
        all_rows.append({
            'Week': week_idx,
            'Day': DAYS[d],
            'Slot': s,
            'Subject': ev['subject'],
            'Group': ev['group'],
            'Teacher': ev['teacher'],
            'Room': rooms.get(ev['id'], 'TBD')
        })

df = pd.DataFrame(all_rows)
df = df.sort_values(['Week', 'Day', 'Slot'])
df.to_csv('../data/timetable_simple.csv', index=False)
with pd.ExcelWriter('../data/timetable_simple.xlsx', engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Schedule', index=False)
    ws = writer.sheets['Schedule']
    rows, cols = df.shape
    ws.autofilter(0, 0, rows, cols - 1)
    ws.freeze_panes(1, 0)