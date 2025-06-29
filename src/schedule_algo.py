
import ast
import csv
import networkx as nx
import pandas as pd
from config import CLASSROOMS, DAYS, time_for_lesson


events = []
with open('../data/schedule.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_students = row.get('Список учнів', '')
        try:
            students = ast.literal_eval(raw_students)
        except Exception:
            students = [s.strip() for s in raw_students.strip('[]').split(',') if s.strip()]
        raw_weekly = row.get('ПТ', '')
        try:
            weekly = ast.literal_eval(raw_weekly)
        except Exception:
            weekly = [int(x) for x in raw_weekly.strip('[]').split(',') if x.strip().isdigit()]
        for week, cnt in enumerate(weekly, start=1):
            for _ in range(int(cnt)):
                ev = {
                    'id': len(events),
                    'week': week,
                    'group': row.get('Група', '').strip(),
                    'subject': row.get('Дисципліна', '').strip(),
                    'teacher': row.get('Викладач', '').strip(),
                    'students': set(students),
                    'num_students': int(row.get('Кількість учнів', len(students)))
                }
                events.append(ev)

def build_conflict_graph(events_week):
    G = nx.Graph()
    for ev in events_week:
        G.add_node(ev['id'], **ev)
    for i, ev1 in enumerate(events_week):
        for ev2 in events_week[i+1:]:
            if ev1['teacher'] == ev2['teacher'] or not ev1['students'].isdisjoint(ev2['students']):
                G.add_edge(ev1['id'], ev2['id'])
    return G

def color_week(G):
    return nx.coloring.greedy_color(G, strategy='largest_first')

def map_color_to_timeslot(color_map):
    times = {}
    for node, color in color_map.items():
        day_idx = color // 8
        slot = (color % 8) + 1
        day_idx = min(day_idx, len(DAYS)-1)
        times[node] = (day_idx, slot)
    return times

def assign_rooms(events_week, times, room_caps=CLASSROOMS):
    room_schedule = {r: set() for r in room_caps}
    assignments = {}
    base_map = {}
    for r in room_caps:
        base = r.split('.', 1)[0]
        base_map.setdefault(base, []).append(r)
    for ev in events_week:
        tid = ev['id']
        day, slot = times.get(tid, (0, 0))
        needed = ev['num_students']
        for room, cap in room_caps.items():
            if cap >= needed and (day, slot) not in room_schedule[room]:
                assignments[tid] = room
                room_schedule[room].add((day, slot))
                break
        else:
            for rl in base_map.values():
                for i in range(len(rl)):
                    for j in range(i+1, len(rl)):
                        r1, r2 = rl[i], rl[j]
                        if room_caps[r1] + room_caps[r2] >= needed:
                            if (day, slot) not in room_schedule[r1] and (day, slot) not in room_schedule[r2]:
                                assignments[tid] = f"{r1}+{r2}"
                                room_schedule[r1].add((day, slot))
                                room_schedule[r2].add((day, slot))
                                break
                    if tid in assignments:
                        break
                if tid in assignments:
                    break
    return assignments

final = []
for wk in range(1, 13):
    week_events = [ev for ev in events if ev['week'] == wk]
    if not week_events:
        continue
    G = build_conflict_graph(week_events)
    color_map = color_week(G)
    times = map_color_to_timeslot(color_map)
    rooms = assign_rooms(week_events, times)
    for ev in week_events:
        day_idx, slot = times.get(ev['id'], (0, 0))
        final.append({
            'Week': wk,
            'Day': DAYS[day_idx],
            'DayNum': day_idx,
            'Slot': slot,
            'Subject': ev['subject'],
            'Group': ev['group'],
            'Room': rooms.get(ev['id'], 'TBD'),
            'Teacher': ev['teacher']
        })

df_sched = pd.DataFrame(final, columns=['Week', 'DayNum', 'Day', 'Slot', 'Subject', 'Group', 'Room', 'Teacher'])
df_sched = df_sched.sort_values(['Week', 'DayNum', 'Slot'])
df_sched = df_sched.drop(columns=['DayNum'])

df_sched.to_csv('../data/timetable.csv', index=False, encoding='utf-8')
print("Schedule saved to CSV: ../data/timetable.csv")
with pd.ExcelWriter('../data/timetable.xlsx', engine='xlsxwriter') as writer:
    df_sched.to_excel(writer, sheet_name='Schedule', index=False)
    ws = writer.sheets['Schedule']
    max_row, max_col = df_sched.shape
    ws.autofilter(0, 0, max_row, max_col - 1)
    ws.freeze_panes(1, 0)
print("Schedule saved to Excel: ../data/timetable.xlsx")


