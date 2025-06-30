import ast
import csv
import networkx as nx
from networkx.algorithms.coloring import greedy_color
import pandas as pd
from collections import defaultdict
from config import CLASSROOMS, DAYS

# Аналогічно з базовим алгоритмом
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


# Аналогічно з базовим алгоритмом
def build_conflict_graph(events_week):
    G = nx.Graph()
    for ev in events_week:
        G.add_node(ev['id'], **ev)
    for i, ev1 in enumerate(events_week):
        for ev2 in events_week[i + 1:]:
            if ev1['teacher'] == ev2['teacher'] or not ev1['students'].isdisjoint(ev2['students']):
                G.add_edge(ev1['id'], ev2['id'])
    return G


def schedule_week(events_week):
    """
    Пояснення для любого перевіряючого, аби Вам було легше зрозуміти:

    Приймає список подій за один тиждень,
    будує граф конфліктів між ними (спільні студенти або викладачі),
    а потім за допомогою жадібного алгоритму граф-фарбування
    призначає кожній події початковий слот (день, пара).

    Далі вона рахує навантаження на кожного студента
    (не більше 5 пар на день) і на кожну дисциплінно-групову пару
    (не більше 2 занять на день), і для тих подій, що перевищують ці ліміти,
    шукає вільні слоти без конфліктів із сусідніми у графі
    та без перевантаження студентів чи дисципліни,
    переносить їх у нові слоти.

    Наприкінці вона проходить по всіх ребрах графа і,
    якщо дві події опинилися в одному слоті,
    переміщує ту з меншим ступенем у графі
    на перший допустимий слот, знову оновлюючи лічильники навантажень.

    Результатом є словник `assignment`,
    який для кожного `id` події повертає оптимізовану пару
    `(день, номер_пари)`.
        """
    G = build_conflict_graph(events_week)
    events_map = {ev['id']: ev for ev in events_week}

    color_map = greedy_color(G, strategy='largest_first')
    assignment = {}
    for ev in events_week:
        c = color_map[ev['id']]
        d = min(c // 8, len(DAYS) - 1)
        s = (c % 8) + 1
        assignment[ev['id']] = (d, s)

    student_load = defaultdict(lambda: defaultdict(int))
    subj_load = defaultdict(lambda: defaultdict(int))
    for ev in events_week:
        d, _ = assignment[ev['id']]
        for st in ev['students']:
            student_load[st][d] += 1
        subj_load[(ev['subject'], ev['group'])][d] += 1

    for ev in sorted(events_week, key=lambda e: G.degree[e['id']]):
        ev_id = ev['id']
        d, s = assignment[ev_id]
        if not (any(student_load[st][d] > 5 for st in ev['students']) or
                subj_load[(ev['subject'], ev['group'])][d] > 2):
            continue
        for dd in range(len(DAYS)):
            for ss in range(1, 9):
                if any(assignment.get(nb) == (dd, ss) for nb in G.neighbors(ev_id)):
                    continue
                if any(student_load[st][dd] >= 5 for st in ev['students']):
                    continue
                if subj_load[(ev['subject'], ev['group'])][dd] >= 2:
                    continue
                for st in ev['students']:
                    student_load[st][d] -= 1
                    student_load[st][dd] += 1
                subj_load[(ev['subject'], ev['group'])][d] -= 1
                subj_load[(ev['subject'], ev['group'])][dd] += 1
                assignment[ev_id] = (dd, ss)
                dd = len(DAYS)
                break
            else:
                continue
            break

    for u, v in G.edges():
        if assignment[u] == assignment[v]:
            ev_move = u if G.degree[u] < G.degree[v] else v
            old_d, old_s = assignment[ev_move]
            ev = events_map[ev_move]
            for dd in range(len(DAYS)):
                for ss in range(1, 9):
                    if (dd, ss) == (old_d, old_s):
                        continue
                    if any(assignment.get(nb) == (dd, ss) for nb in G.neighbors(ev_move)):
                        continue
                    if any(student_load[st][dd] >= 5 for st in ev['students']):
                        continue
                    key = (ev['subject'], ev['group'])
                    if subj_load[key][dd] >= 2:
                        continue
                    for st in ev['students']:
                        student_load[st][old_d] -= 1
                        student_load[st][dd] += 1
                    subj_load[key][old_d] -= 1
                    subj_load[key][dd] += 1
                    assignment[ev_move] = (dd, ss)
                    dd = len(DAYS)
                    break
                else:
                    continue
                break

    return assignment


def assign_rooms(events_week, times, room_caps=CLASSROOMS):
    """
    Призначає аудиторії для подій заданого тижня з урахуванням місткості
    та зайнятості в кожному тайм-слоті.
    """
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
            for rooms in base_map.values():
                for i in range(len(rooms)):
                    for j in range(i + 1, len(rooms)):
                        r1, r2 = rooms[i], rooms[j]
                        if (room_caps[r1] + room_caps[r2] >= needed and
                                (d, s) not in room_schedule[r1] and
                                (d, s) not in room_schedule[r2]):
                            result[tid] = f"{r1}+{r2}"
                            room_schedule[r1].add((d, s))
                            room_schedule[r2].add((d, s))
                            break
                    if tid in result:
                        break
                if tid in result:
                    break
    return result

# у нас після роботи слоти, яким алгоритм зручно для всіх не зміг впихнути, того для того, щоб цн виправити, ми впихуємо їх тут
def auto_assign_tbd(events_week, times, rooms, room_caps=CLASSROOMS):
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

# Все аналогічно стандартному алгоритмку
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
