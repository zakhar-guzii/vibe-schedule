import ast
import csv
import networkx as nx
import pandas as pd
from config import CLASSROOMS, DAYS

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


def build_conflict_graph(events_week):
    G = nx.Graph()
    for ev in events_week:
        G.add_node(ev['id'], **ev)
    for i, ev1 in enumerate(events_week):
        for ev2 in events_week[i + 1:]:
            if (ev1['teacher'] == ev2['teacher']
                    or not ev1['students'].isdisjoint(ev2['students'])):
                G.add_edge(ev1['id'], ev2['id'])
    return G


def schedule_week(events_week, prev_week_assignments=None):
    G = build_conflict_graph(events_week)
    sorted_events = sorted(events_week, key=lambda e: G.degree[e['id']], reverse=True)
    assignment = {}
    student_counts = {}
    subj_counts = {}

    preferred = {}
    if prev_week_assignments:
        by_key = {}
        for ev in events_week:
            key = (ev['subject'], ev['group'])
            by_key.setdefault(key, []).append(ev)
        for key, lst in by_key.items():
            if key in prev_week_assignments:
                prev_slots = prev_week_assignments[key]
                prev_slots = prev_slots if isinstance(prev_slots, list) else [prev_slots]
                prev_sorted = sorted(prev_slots, key=lambda x: x[0] * 10 + x[1])
                lst_sorted = sorted(lst, key=lambda x: x['id'])
                for i, ev in enumerate(lst_sorted):
                    if i < len(prev_sorted):
                        preferred[ev['id']] = prev_sorted[i]

    def can_place(ev, d, s):
        for nb in G.neighbors(ev['id']):
            if assignment.get(nb) == (d, s):
                return False
        for st in ev['students']:
            if student_counts.get((st, d), 0) >= 5:
                return False
        key = (ev['subject'], ev['group'])
        if subj_counts.get((key, d), 0) >= 2:
            return False
        return True

    for ev in sorted_events:
        placed = False
        if ev['id'] in preferred:
            d0, s0 = preferred[ev['id']]
            if can_place(ev, d0, s0):
                assignment[ev['id']] = (d0, s0)
                placed = True
        if not placed:
            for d in range(len(DAYS)):
                for s in range(1, 9):
                    if can_place(ev, d, s):
                        assignment[ev['id']] = (d, s)
                        placed = True
                        break
                if placed:
                    break
        if not placed:
            for d in range(len(DAYS)):
                for s in range(1, 9):
                    assignment[ev['id']] = (d, s)
                    placed = True
                    break
                if placed:
                    break
            print(f"Warning: подію {ev['id']} поставлено в слот {assignment[ev['id']]} без перевірки обмежень")

        d_assigned, _ = assignment[ev['id']]
        for st in ev['students']:
            student_counts[(st, d_assigned)] = student_counts.get((st, d_assigned), 0) + 1
        key = (ev['subject'], ev['group'])
        subj_counts[(key, d_assigned)] = subj_counts.get((key, d_assigned), 0) + 1

    return assignment


def assign_rooms(events_week, times, room_caps=CLASSROOMS):
    room_schedule = {r: set() for r in room_caps}
    result = {}
    base_map = {}
    for r in room_caps:
        b = r.split('.', 1)[0]
        base_map.setdefault(b, []).append(r)

    for ev in events_week:
        tid = ev['id']
        d, s = times.get(tid, (None, None))
        needed = ev['num_students']

        for room, cap in room_caps.items():
            if cap >= needed and (d, s) not in room_schedule[room]:
                result[tid] = room
                room_schedule[room].add((d, s))
                break
        else:
            # дві кімнати одного корпусу
            for rooms in base_map.values():
                for i in range(len(rooms)):
                    for j in range(i + 1, len(rooms)):
                        r1, r2 = rooms[i], rooms[j]
                        if (room_caps[r1] + room_caps[r2] >= needed
                                and (d, s) not in room_schedule[r1]
                                and (d, s) not in room_schedule[r2]):
                            result[tid] = f"{r1}+{r2}"
                            room_schedule[r1].add((d, s))
                            room_schedule[r2].add((d, s))
                            break
                    if tid in result:
                        break
                if tid in result:
                    break

    return result


def auto_assign_tbd(events_week, times, rooms, room_caps=CLASSROOMS):
    # будуємо розклад використання кімнат
    room_sched = {r: set() for r in room_caps}
    for ev in events_week:
        tid = ev['id']
        r = rooms.get(tid)
        if r and r != 'TBD':
            for sub in r.split('+'):
                room_sched[sub].add(times[tid])

    teacher_slots = {}
    for ev in events_week:
        teacher_slots.setdefault(ev['teacher'], set()).add(times[ev['id']])

    for ev in events_week:
        tid = ev['id']
        if rooms.get(tid) == 'TBD':
            d, s = times[tid]
            if (d, s) in teacher_slots.get(ev['teacher'], set()):
                continue
            for room in room_caps:
                if (d, s) not in room_sched[room]:
                    rooms[tid] = room
                    room_sched[room].add((d, s))
                    break
    return rooms


final = []
prev = {}

for week_idx in range(1, 13):
    evs = [e for e in events if e['week'] == week_idx]
    if not evs:
        continue

    times = schedule_week(evs, prev.get(week_idx - 1))
    rooms = assign_rooms(evs, times)
    rooms = auto_assign_tbd(evs, times, rooms)

    curr = {}
    for ev in evs:
        tid = ev['id']
        d, s = times[tid]
        final.append({
            'Week': week_idx,
            'DayNum': d,
            'Day': DAYS[d],
            'Slot': s,
            'Subject': ev['subject'],
            'Group': ev['group'],
            'Room': rooms.get(tid, 'TBD'),
            'Teacher': ev['teacher']
        })
        curr.setdefault((ev['subject'], ev['group']), []).append((d, s))

    prev[week_idx] = curr

df = pd.DataFrame(final)
df = df.sort_values(['Week', 'DayNum', 'Slot']).drop(columns=['DayNum'])
df.to_csv('../data/timetable.csv', index=False, encoding='utf-8')
with pd.ExcelWriter('../data/timetable.xlsx', engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Schedule', index=False)
    ws = writer.sheets['Schedule']
    rows, cols = df.shape
    ws.autofilter(0, 0, rows, cols - 1)
    ws.freeze_panes(1, 0)

print("Готово: розклад збережено в timetable.csv та timetable.xlsx")
