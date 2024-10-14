import json
from datetime import datetime
import requests
import streamlit as st
import pandas as pd
from config_api import headers


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


def get_recruits():
    url = "https://api.collegefootballdata.com/recruiting/players"
    querystring = {"year": year, "team": team}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    recruits_df = pd.DataFrame(response.json())
    return recruits_df


def get_transfers():
    url = "https://api.collegefootballdata.com/player/portal"
    querystring = {"year": year}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    transfers_df = pd.DataFrame(response.json())
    transfers_in_df = transfers_df[transfers_df['destination'] == team]
    transfers_out_df = transfers_df[transfers_df['origin'] == team]
    return transfers_in_df, transfers_out_df


def display_team_rating():
    url = "https://api.collegefootballdata.com/recruiting/teams"
    querystring = {"year": year, "team": team}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    if len(response.json()) > 0:
        team_rank = response.json()[0]['rank']
        team_points = response.json()[0]['points']
        st.markdown(f'##### National Rank: {team_rank} | Points: {team_points}')


def display_recruits():
    recruits_columns = {
        'ranking': 'Natl Rank',
        'stars': 'Stars',
        'rating': 'Rating',
        'name': 'Name',
        'position': 'Position',
        'height': 'Height',
        'weight': 'Weight',
        'school': 'School',
        'city': 'City',
        'stateProvince': 'State',
    }
    st.markdown(f'#### Recruits')
    display_team_rating()
    st.dataframe(recruits_df,
                 column_order=recruits_columns.keys(),
                 column_config=recruits_columns,
                 hide_index=True,
                 )


def display_transfers():
    transfers_in_columns = {
        'stars': 'Stars',
        'rating': 'Rating',
        'firstName': 'First Name',
        'lastName': 'Last Name',
        'position': 'Position',
        'origin': 'From School',
        'eligibility': 'Eligibility',
    }
    st.markdown(f'#### Transfers In')
    st.dataframe(transfers_in_df,
                 column_order=transfers_in_columns.keys(),
                 column_config=transfers_in_columns,
                 hide_index=True,
                 )
    transfers_out_columns = {
        'stars': 'Stars',
        'rating': 'Rating',
        'firstName': 'First Name',
        'lastName': 'Last Name',
        'position': 'Position',
        'destination': 'To School',
        'eligibility': 'Eligibility',
    }
    st.markdown(f'#### Transfers Out')
    st.dataframe(transfers_out_df,
                 column_order=transfers_out_columns.keys(),
                 column_config=transfers_out_columns,
                 hide_index=True,
                 )

team, year = select_team_year()
team_color, team_logo = team_information()
st.markdown(f"""
    <div style='display: flex; align-items: center;'>
        <img src='{team_logo}' alt='team logo' style='width:100px; height:auto; margin-right:15px;'>
        <h2 style='color: {team_color}; margin: 0;'>{st.session_state.team} {st.session_state.year} Recruits and Transfers</h1>
    </div>
    """, unsafe_allow_html=True)

recruits_df = get_recruits()
display_recruits()
if year in range(2021, datetime.now().year):
    transfers_in_df, transfers_out_df = get_transfers()
    display_transfers()