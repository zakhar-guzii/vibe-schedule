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
    '1.08.1':40 , '1.08.2': 40, '1.17.1': 24, '1.17.2': 24,
    '2.08.1': 50, '2.08.2': 40, '2.15.1': 24, '2.15.2': 30,
    '3.05': 26, '4.05': 24, '4.07': 22, '4.16': 42,'4.08': 50,
    'Феофанія 1': 42, 'Феофанія 2': 24, 'Феофанія 3': 13, 'Феофанія 4': 40,
    'ICU': 130
}

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
