from datetime import datetime, time, timedelta

def time_for_lesson():
    start0   = datetime.combine(datetime.today(), time(8, 30))
    pair_len = timedelta(minutes=80)
    breaks   = {1:10,2:10,3:10,4:40,5:10,6:10,7:10}
    slot_times = {}
    cur = start0
    for p in range(1,9):
        slot_times[p] = (cur.time(), (cur + pair_len).time())
        cur = cur + pair_len + timedelta(minutes=breaks.get(p,10))
    return slot_times

CLASSROOMS = [
    '1.08.1','1.08.2','1.15.1','1.15.2',
    '2.08.1','2.08.2','2.15.1','2.15.2',
    '3.05','4.05','4.08','4.16',
    'Феофанія 1','Феофанія 2','Феофанія 3','Феофанія 4',
]

DAYS = ['Mon','Tue','Wed','Thu','Fri']

