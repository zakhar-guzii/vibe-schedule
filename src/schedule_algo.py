import ast
import csv
import networkx as nx
from networkx.algorithms.coloring import greedy_color
import pandas as pd
from collections import defaultdict
from config import CLASSROOMS, DAYS

# Зчитування подій з CSV
events = []
with open('../data/schedule.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_students = row.get('Список учнів', '')
        try:
            students = ast.literal_eval(raw_students)
        except (ValueError, SyntaxError):
            students = [s.strip() for s in raw_students.strip('[]').split(',') if s.strip()]
        raw_weekly = row.get('ПТ', '')
        try:
            weekly = ast.literal_eval(raw_weekly)
        except (ValueError, SyntaxError):
            weekly = [int(x) for x in raw_weekly.strip('[]').split(',') if x.strip().isdigit()]
        for week_idx, cnt in enumerate(weekly, start=1):
            for _ in range(int(cnt)):
                events.append({
                    'id': len(events),
                    'week': week_idx,
                    'group': row.get('Група', '').strip(),
                    'subject': row.get('Дисципліна', '').strip(),
                    'teacher': row.get('Викладач', '').strip(),
                    'students': set(students),
                    'num_students': int(row.get('Кількість учнів', len(students)))
                })


# Побудова графа конфліктів
def build_conflict_graph(events_week):
    G = nx.Graph()
    for ev in events_week:
        G.add_node(ev['id'], **ev)
    for i, ev1 in enumerate(events_week):
        for ev2 in events_week[i + 1:]:
            if ev1['teacher'] == ev2['teacher'] or not ev1['students'].isdisjoint(ev2['students']):
                G.add_edge(ev1['id'], ev2['id'])
    return G


# М’яка оптимізація: вікна та екстремальні слоти
def optimize_soft(assignment, events_week):
    teacher_slots = defaultdict(lambda: defaultdict(set))
    group_slots = defaultdict(lambda: defaultdict(set))
    for ev in events_week:
        tid = ev['id'];
        d, s = assignment[tid]
        teacher_slots[ev['teacher']][d].add(s)
        group_slots[ev['group']][d].add(s)
    # Переміщення екстремальних слотів (1 та 8) у середину (2–7)
    for ev in events_week:
        tid = ev['id'];
        d, s = assignment[tid]
        if s in (1, 8):
            for new_s in range(2, 8):
                if new_s not in teacher_slots[ev['teacher']][d] and new_s not in group_slots[ev['group']][d]:
                    conflict = False
                    for other in events_week:
                        if other['id'] != tid and assignment.get(other['id']) == (d, new_s):
                            if other['teacher'] == ev['teacher'] or not ev['students'].isdisjoint(other['students']):
                                conflict = True;
                                break
                    if conflict: continue
                    teacher_slots[ev['teacher']][d].discard(s)
                    teacher_slots[ev['teacher']][d].add(new_s)
                    group_slots[ev['group']][d].discard(s)
                    group_slots[ev['group']][d].add(new_s)
                    assignment[tid] = (d, new_s)
                    break
    # Зменшення вікон між парами
    for ev in events_week:
        tid = ev['id'];
        d, s = assignment[tid]
        slots = sorted(teacher_slots[ev['teacher']][d] | group_slots[ev['group']][d])
        if len(slots) > 1 and (max(slots) - min(slots) + 1) > len(slots):
            for candidate in range(min(slots), max(slots) + 1):
                if candidate not in teacher_slots[ev['teacher']][d] and candidate not in group_slots[ev['group']][d]:
                    conflict = False
                    for other in events_week:
                        if other['id'] != tid and assignment.get(other['id']) == (d, candidate):
                            if other['teacher'] == ev['teacher'] or not ev['students'].isdisjoint(other['students']):
                                conflict = True;
                                break
                    if conflict: continue
                    teacher_slots[ev['teacher']][d].discard(s)
                    teacher_slots[ev['teacher']][d].add(candidate)
                    group_slots[ev['group']][d].discard(s)
                    group_slots[ev['group']][d].add(candidate)
                    assignment[tid] = (d, candidate)
                    break
    return assignment


def schedule_week(events_week):
    G = build_conflict_graph(events_week)
    color_map = greedy_color(G, strategy='largest_first')
    assignment = {ev['id']: (min(color_map[ev['id']] // 8, len(DAYS) - 1),
                             (color_map[ev['id']] % 8) + 1)
                  for ev in events_week}
    # Підрахунок щоденного навантаження
    student_load = defaultdict(lambda: defaultdict(int))
    subj_load = defaultdict(lambda: defaultdict(int))
    for ev in events_week:
        d, _ = assignment[ev['id']]
        for st in ev['students']:
            student_load[st][d] += 1
        subj_load[(ev['subject'], ev['group'])][d] += 1
    # Жорсткі щоденні обмеження: <=4 пар/день студент, <=2 пар/день дисципліни
    for st, days in list(student_load.items()):
        for d, cnt in list(days.items()):
            if cnt > 4:
                evs = [ev for ev in events_week if st in ev['students'] and assignment[ev['id']][0] == d]
                for ev in sorted(evs, key=lambda e: G.degree[e['id']])[:cnt - 4]:
                    old_d, old_s = assignment[ev['id']]
                    for dd in range(len(DAYS)):
                        for ss in range(1, 9):
                            if (dd, ss) == (old_d, old_s):
                                continue
                            if any(assignment.get(n) == (dd, ss) for n in G.neighbors(ev['id'])):
                                continue
                            if student_load[st][dd] >= 4:
                                continue
                            key = (ev['subject'], ev['group'])
                            if subj_load[key][dd] >= 2:
                                continue
                            for s2 in ev['students']:
                                student_load[s2][old_d] -= 1
                                student_load[s2][dd] += 1
                            subj_load[key][old_d] -= 1
                            subj_load[key][dd] += 1
                            assignment[ev['id']] = (dd, ss)
                            dd = len(DAYS)
                            break
                        else:
                            continue
                        break
    for key, days in list(subj_load.items()):
        for d, cnt in list(days.items()):
            if cnt > 2:
                evs = [ev for ev in events_week if (ev['subject'], ev['group']) == key and assignment[ev['id']][0] == d]
                for ev in sorted(evs, key=lambda e: G.degree[e['id']])[:cnt - 2]:
                    old_d, old_s = assignment[ev['id']]
                    for dd in range(len(DAYS)):
                        for ss in range(1, 9):
                            if (dd, ss) == (old_d, old_s):
                                continue
                            if any(assignment.get(n) == (dd, ss) for n in G.neighbors(ev['id'])):
                                continue
                            if any(student_load[s2][dd] >= 4 for s2 in ev['students']):
                                continue
                            if subj_load[key][dd] >= 2:
                                continue
                            for s2 in ev['students']:
                                student_load[s2][old_d] -= 1
                                student_load[s2][dd] += 1
                            subj_load[key][old_d] -= 1
                            subj_load[key][dd] += 1
                            assignment[ev['id']] = (dd, ss)
                            dd = len(DAYS)
                            break
                        else:
                            continue
                        break
    assignment = optimize_soft(assignment, events_week)
    return assignment


# Призначення аудиторій
def assign_rooms(events_week, times, room_caps=CLASSROOMS):
    room_schedule = {r: set() for r in room_caps}
    assignment_room = {}
    for ev in events_week:
        tid = ev['id'];
        d, s = times[tid];
        needed = ev['num_students']
        for room, cap in room_caps.items():
            if cap >= needed and (d, s) not in room_schedule[room]:
                assignment_room[tid] = room
                room_schedule[room].add((d, s))
                break
    for ev in events_week:
        tid = ev['id']
        if tid not in assignment_room:
            d, s = times[tid]
            for room in room_caps:
                if (d, s) not in room_schedule[room]:
                    assignment_room[tid] = room
                    room_schedule[room].add((d, s))
                    break
    return assignment_room


# Генерація фінального розкладу
final = []
for week_idx in range(1, 13):
    evs = [e for e in events if e['week'] == week_idx]
    if not evs:
        continue
    times = schedule_week(evs)
    rooms = assign_rooms(evs, times)
    for ev in evs:
        d, s = times[ev['id']]
        final.append({
            'Week': week_idx,
            'DayNum': d,
            'Day': DAYS[d],
            'Slot': s,
            'Subject': ev['subject'],
            'Group': ev['group'],
            'Teacher': ev['teacher'],
            'Room': rooms[ev['id']]
        })

output_df = pd.DataFrame(final)
output_df = output_df.sort_values(['Week', 'DayNum', 'Slot'])
output_df = output_df.drop(columns=['DayNum'])
output_df.to_csv('../data/timetable.csv', index=False, encoding='utf-8')
with pd.ExcelWriter('../data/timetable.xlsx', engine='xlsxwriter') as writer:
    output_df.to_excel(writer, sheet_name='Schedule', index=False)
    ws = writer.sheets['Schedule']
    rows, cols = output_df.shape
    ws.autofilter(0, 0, rows, cols - 1)
    ws.freeze_panes(1, 0)
