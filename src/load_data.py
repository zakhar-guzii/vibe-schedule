import pandas as pd


def prep_data():
    file = '../data/Розклад для студентів (літній терм 2025).xlsx'
    df_groups  = pd.read_excel(file, sheet_name='Розподіл на групи')
    df_courses = pd.read_excel(file, sheet_name='Дисципліни')
