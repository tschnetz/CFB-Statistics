import json
from datetime import datetime
import streamlit as st
import pandas as pd
import requests

headers = st.session_state.headers
YEAR = 2024

def get_schedule():
    url = "https://api.collegefootballdata.com/calendar"
    querystring = {"year": YEAR}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    weeks = pd.DataFrame(response.text)
    return weeks

def get_games():
    url = "https://api.collegefootballdata.com/games"
    querystring = {"year": YEAR, "week": week, "division": "fbs"}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    games = pd.DataFrame(response.text)
    return games


weeks_df = get_schedule()
games_df = get_games()
week = st.sidebar.selectbox("Select week", weeks_df['week'].unique())
week_games_df = games_df[games_df['week'] == week]
st.dataframe(week_games_df)