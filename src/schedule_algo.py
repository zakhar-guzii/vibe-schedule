import pandas as pd
import networkx as nx
from datetime import datetime, time, timedelta
from src.load_data import prep_data
from config import CLASSROOMS, time_for_lesson


def main():
    df_final = prep_data()
