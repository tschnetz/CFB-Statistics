import json
from datetime import datetime
import streamlit as st
import pandas as pd
import requests

team = st.session_state.team
year = st.session_state.year
headers = st.session_state.headers

def team_information():
    with open('team_info.json', 'r') as file:
        data_dict = json.load(file)
    team_df = pd.DataFrame(data_dict)
    for school in team_df['school']:
        if school == team:
            # set team_color = color for school = team
            team_color = team_df[team_df['school'] == team]['color'].values[0]
            team_logo = team_df[team_df['school'] == team]['logos'].values[0][0]
            return team_color, team_logo


def select_team_year():
    year = st.sidebar.number_input('Enter Year',
                                   min_value=1902,
                                   max_value=datetime.now().year + 1,
                                   step=1,
                                   value=2024)
    # Load the JSON data from the uploaded file
    with open('team_info.json') as f:
        team_data = json.load(f)
    # Filter teams with classification "fbs" or "fcs"
    filtered_teams = sorted([team['school'] for team in team_data if team['classification'] in ['fbs', 'fcs']])
    team_index = filtered_teams.index(st.session_state.team)
    team = st.sidebar.selectbox('Select Team Name', options=filtered_teams, index=team_index)
    st.session_state.team = team
    st.session_state.year = year
    return team, year


def get_roster():
    url = "http://api.collegefootballdata.com/roster"
    querystring = {"team":team,"year":year}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    roster = pd.DataFrame(response.json())
    return roster


def get_nfl_picks():
    url = "https://api.collegefootballdata.com/draft/picks"
    querystring = {"year": (year + 1), "college": team}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    nfl_picks = pd.DataFrame(response.json())
    return nfl_picks


def display_nfl_picks():
    nfl_picks_columns = {
        'round': 'Round',
        'pick': 'Pick',
        'overall': 'Overall',
        'nflTeam': 'NFL Team',
        'name': 'Name',
        'position': 'Position',
    }
    st.markdown(f'##### NFL Draftees')
    st.dataframe(nfl_picks_df,
                 column_order=nfl_picks_columns.keys(),
                 column_config=nfl_picks_columns,
                 hide_index=True,
                 )


def display_roster():
    roster_columns = {
        'jersey': 'Jersey',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'position': 'Position',
        'height': 'Height',
        'weight': 'Weight',
        'year': 'Year',
        'home_city': 'Home City',
        'home_state': 'Home State',
    }
    positions = sorted(roster_df['position'].fillna('None').unique())
    for position in positions:
        st.markdown(f'##### {position} Position')
        st.dataframe(roster_df[roster_df['position'] == position],
                     column_order=roster_columns.keys(),
                     column_config=roster_columns,
                     hide_index=True,
                     )


team, year = select_team_year()
team_color, team_logo = team_information()
st.markdown(f"""
    <div style='display: flex; align-items: center;'>
        <img src='{team_logo}' alt='team logo' style='width:100px; height:auto; margin-right:15px;'>
        <h2 style='color: {team_color}; margin: 0;'>{st.session_state.team} {st.session_state.year} Roster</h1>
    </div>
    """, unsafe_allow_html=True)

nfl_picks_df = get_nfl_picks()
if len(nfl_picks_df) > 0:
    display_nfl_picks()
roster_df = get_roster()
display_roster()