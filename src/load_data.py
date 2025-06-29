import pandas as pd
from collections import Counter
from collections import defaultdict


def prep_data():
    file = '../data/Розклад для студентів (літній терм 2025).xlsx'
    df_groups = pd.read_excel(file, sheet_name='Розподіл на групи')
    df_courses = pd.read_excel(file, sheet_name='Дисципліни')
    df_number_of_lessons = pd.read_excel(file, sheet_name='Розклад')

    df_final = df_courses.copy()

    CSV_PATH = '../data/Розклад для студентів (літній терм 2025).csv'
    df = pd.read_csv(CSV_PATH, sep=';', header=None, dtype=str)
    week_subject_counts = defaultdict(lambda: defaultdict(int))
    current_week = None
    max_week = 0

    for _, row in df.iterrows():
        cell0 = row.iloc[0]
        if isinstance(cell0, str) and 'тижд.' in cell0:
            current_week = int(cell0.split()[0])
            max_week = max(max_week, current_week)
        else:
            if current_week is None:
                continue
            for subj in row.iloc[1:]:
                if isinstance(subj, str) and subj.strip():
                    subj_code = subj.strip()
                    week_subject_counts[current_week][subj_code] += 1

    result = {}
    for week in range(1, max_week + 1):
        for subj_code, cnt in week_subject_counts[week].items():
            result.setdefault(subj_code, [0] * max_week)
            result[subj_code][week - 1] = cnt

    cols_to_drop = (
            [f'{i} тижд.' for i in range(1, 12)]
            + pd.date_range('08:30', '19:30', freq='90min').strftime('%H:%M').tolist()
            + ['ПОНЕДІЛОК', 'ВІВТОРОК', 'СЕРЕДА', 'ЧЕТВЕР', "П'ЯТНИЦЯ"]
    )
    df_subj = df_number_of_lessons.drop(
        columns=[c for c in cols_to_drop if c in df_number_of_lessons.columns]
    )

    all_entries = df_subj.values.flatten()
    subjects = [s.strip() for s in all_entries if isinstance(s, str) and s.strip()]
    counts = dict(Counter(subjects))
    df_final['Кількість пар'] = (
        df_final['Група'].str.strip()
        .map(counts)
        .replace(0, pd.NA)
        .astype('Int64')
    )

    df_groups_for_melt = df_groups.drop(columns=['Група'], errors='ignore')

    id_cols = ['Прізвище', "Ім'я", 'Пошта']
    value_cols = [c for c in df_groups_for_melt.columns if c not in id_cols]
    long = df_groups_for_melt.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name='Предмет',
        value_name='Група'
    )

    long = long[
        long['Група'].notna()
        & (long['Група'].astype(str).str.strip() != '')
        ]
    long['Учень'] = long['Прізвище'] + ' ' + long["Ім'я"]

    students_per_group = (
        long
        .groupby('Група')['Учень']
        .agg(lambda x: list(x.unique()))
        .reset_index()
        .rename(columns={'Учень': 'Список учнів'})
    )

    df_final = df_final.merge(
        students_per_group,
        on='Група',
        how='left'
    )

    df_final['ПТ'] = df_final['Група'].map(result)
    return df_final


if __name__ == '__main__':
    df_final = prep_data()
    df_final.to_csv('../data/schedule.csv', index=False)
