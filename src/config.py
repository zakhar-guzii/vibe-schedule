from datetime import datetime, time, timedelta

# Створення time-слотів для розкладу
def time_for_lesson():
    start0 = datetime.combine(datetime.today(), time(8, 30))
    pair_len = timedelta(minutes=80)
    breaks = {1: 10, 2: 10, 3: 10, 4: 40, 5: 10, 6: 10, 7: 10}
    slot_times = {}
    cur = start0
    for p in range(1, 9):
        slot_times[p] = (cur.time(), (cur + pair_len).time())
        cur = cur + pair_len + timedelta(minutes=breaks.get(p, 10))
    return slot_times

# Доступні аудиторії з їх розміром
CLASSROOMS = {
    '1.08.1': 25, '1.08.2': 25, '1.15.1': 40, '1.15.2': 30,
    '2.08.1': 25, '2.08.2': 25, '2.15.1': 40, '2.15.2': 40,
    '3.05': 20, '4.05': 20, '4.08': 40, '4.16': 40,
    'Феофанія 1': 50, 'Феофанія 2': 35, 'Феофанія 3': 35, 'Феофанія 4': 35,
    'ICU': 130
}

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
