from datetime import date
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
    weeks = pd.DataFrame(response.json())
    return weeks


def select_week():
    weeks_df = get_schedule()
    weeks_df['firstGameStart'] = pd.to_datetime(weeks_df['firstGameStart'])
    weeks_df['lastGameStart'] = pd.to_datetime(weeks_df['lastGameStart'])
    weeks_df['firstGameStart'] = weeks_df['firstGameStart'].dt.strftime('%b-%d')
    weeks_df['lastGameStart'] = weeks_df['lastGameStart'].dt.strftime('%b-%d')
    selected = []
    for index, row in weeks_df.iterrows():
        week_str = f"Week {row['week']} ({row['firstGameStart']} - {row['lastGameStart']})"
        selected.append(week_str)
    current_date = date.today()
    week_number = current_date.isocalendar()[1] - 35
    selected_week = st.sidebar.selectbox("Select week", selected, index=week_number)
    week = selected.index(selected_week) + 1
    return week


def get_polls(poll_name):
    url = "https://api.collegefootballdata.com/rankings"
    querystring = {"year": YEAR, "week": week}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    polls = response.json()[0]['polls']
    for poll in polls:
        if poll['poll'] == poll_name:
            return pd.DataFrame(poll['ranks'])



week = select_week()
coaches_poll_df = get_polls('Coaches Poll')
ap_top_25_df = get_polls('AP Top 25')
col1, col2 = st.columns(2)
with col2:
    st.markdown(f'#### Coaches Poll')
    st.dataframe(coaches_poll_df, hide_index=True, height=920)
with col1:
    st.markdown(f'#### AP Top 25')
    st.dataframe(ap_top_25_df, hide_index=True, height=920)
