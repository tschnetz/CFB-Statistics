import json
from datetime import datetime
from unicodedata import category

import streamlit as st
import pandas as pd
import requests

from team_results import stats_df

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
    filtered_teams = sorted([team['school'] for team in team_data if team['classification'] in ['fbs']])
    team_index = filtered_teams.index(st.session_state.team)
    team = st.sidebar.selectbox('Select Team Name', options=filtered_teams, index=team_index)
    st.session_state.team = team
    st.session_state.year = year
    return team, year


def get_stats():
    url = "https://api.collegefootballdata.com/stats/player/season"
    querystring = {"team":team,"year":year}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    stats_df = pd.DataFrame(response.json())
    # Convert stats_df['stat'] into a float from a string
    stats_df['stat'] = stats_df['stat'].astype(float)
    # Sort stats_df on 'category' and 'statType'
    stats_df = stats_df.sort_values(by=['category', 'statType', 'stat'], ascending=False)
    return stats_df


def display_stats():
    stats_categories = [
        'receiving',
        'rushing',
        'passing',
        'defensive',
        'punting',
        'kickReturns',
        'puntReturns',
    ]
    stats_columns = {
        'player': 'Player',
        'statType': 'Stat Type',
        'stat': 'Value'
    }
    for stat in stats_df['category'].unique():
        st.markdown(f'### {stat.capitalize()}')
        category_df = stats_df[stats_df['category'] == stat]
        for stat_type in category_df['statType'].unique():
            st.markdown(f'##### {stat_type}')
            # Remove items with a 'stat' value of 0
            category_df = category_df[category_df['stat'] != 0]
            st.dataframe(category_df[category_df['statType'] == stat_type],
                        column_order=stats_columns.keys(),
                        column_config=stats_columns,
                        use_container_width= True,
                        hide_index=True,)


team, year = select_team_year()
team_color, team_logo = team_information()
st.markdown(f"""
    <div style='display: flex; align-items: center;'>
        <img src='{team_logo}' alt='team logo' style='width:100px; height:auto; margin-right:15px;'>
        <h1 style='color: {team_color}; margin: 0;'>{st.session_state.team} {st.session_state.year} Team Statistics</h1>
    </div>
    """, unsafe_allow_html=True)

stats_df = get_stats()
display_stats()