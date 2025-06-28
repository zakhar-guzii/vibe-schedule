import pandas as pd


def prep_data():
    file = '../data/Розклад для студентів (літній терм 2025).xlsx'
    df_groups = pd.read_excel(file, sheet_name='Розподіл на групи')
    df_courses = pd.read_excel(file, sheet_name='Дисципліни')

    fixed_cols = ['Прізвище', "Ім'я"]
    discipline_cols = [c for c in df_groups.columns if c not in fixed_cols]

    df_long = df_groups.melt(
        id_vars=fixed_cols,
        value_vars=discipline_cols,
        var_name='Дисципліна',
        value_name='Група_мелт'
    ).dropna(subset=['Група_мелт'])

    df_long = df_long.rename(columns={'Група_мелт': 'Група'})

    df_long['ПІБ'] = df_long['Прізвище'] + ' ' + df_long["Ім'я"]

    df_final = df_courses.copy()

    def get_students(disc, grp):
        mask = (df_long['Дисципліна'] == disc) & (df_long['Група'] == grp)
        return df_long.loc[mask, 'ПІБ'].tolist()

    group_col_name = 'Група'

    df_final['Студенти'] = df_final.apply(
        lambda r: get_students(r['Дисципліна'], r[group_col_name]), axis=1
    )
    return df_final
