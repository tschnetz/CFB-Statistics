from datetime import datetime
import json
import pandas as pd
import requests
import streamlit as st
from config_api import headers

# YEAR = 2024
st.sidebar.title("CFB Data")

def select_team_year():
    year = st.sidebar.number_input('Enter Year',
                                   min_value=1902,
                                   max_value=datetime.now().year,
                                   step=1,
                                   value=2024)
    # Load the JSON data from the uploaded file
    with open('team_info.json') as f:
        team_data = json.load(f)
    # Filter teams with classification "fbs" or "fcs"
    filtered_teams = sorted([team['school'] for team in team_data if team['classification'] in ['fbs']])
    if st.session_state.team != '':
        team_index = filtered_teams.index(st.session_state.team)
    else:
        team_index = filtered_teams.index('Georgia Tech')
    team_1 = st.sidebar.selectbox('Select Team One', options=filtered_teams, index=team_index)
    team_2 = st.sidebar.selectbox('Select Team Two', options=filtered_teams, index=team_index)
    return team_1, team_2, year

def team_information(team):
    with open('team_info.json', 'r') as file:
        data_dict = json.load(file)
    team_df = pd.DataFrame(data_dict)
    for school in team_df['school']:
        if school == team:
            # set team_color = color for school = team
            team_color = team_df[team_df['school'] == team]['color'].values[0]
            team_logo = team_df[team_df['school'] == team]['logos'].values[0][0]
            return team_color, team_logo

def get_ratings(url, team):
    querystring = {"team":team,"year":year}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    return response.json()

def get_fpi(team):
    link = "https://api.collegefootballdata.com/ratings/fpi"
    team_stat = pd.DataFrame(get_ratings(link, team))
    return team_stat['fpi'].values[0]

def get_elo(team):
    link = "https://api.collegefootballdata.com/ratings/elo"
    team_stat = pd.DataFrame(get_ratings(link, team))
    return team_stat['elo'].values[0]

def get_srs(team):
    link = "https://api.collegefootballdata.com/ratings/srs"
    team_stat = pd.DataFrame(get_ratings(link, team))
    return team_stat['rating']

def get_sp(team):
    link = "https://api.collegefootballdata.com/ratings/sp"
    team_stat = pd.DataFrame(get_ratings(link, team))
    team_stat = team_stat[team_stat['team'] == team]
    return team_stat['rating']

def get_stats(team):
    fpi = get_fpi(team)
    elo = get_elo(team)
    srs = get_srs(team)
    sp = get_sp(team)
    stats_df = pd.DataFrame({'FPI':fpi, 'ELO':elo, 'SRS':srs, 'SP':sp})
    return stats_df

def get_games_played(team):
    link = "https://api.collegefootballdata.com/records"
    team_games = pd.DataFrame(get_ratings(link, team))
    team_games['games_played'] = team_games['total'].apply(lambda x: x['games'] if isinstance(x, dict) else None)
    played = team_games[team_games['games_played'].notnull()]
    return played['games_played'].iloc[0]

def get_team_stats(team):
    link = "https://api.collegefootballdata.com/stats/season"
    team_stats = pd.DataFrame(get_ratings(link, team))
    games_played = get_games_played(team)
    team_stats = team_stats[['statName', 'statValue']]
    team_stats = team_stats.sort_values(by='statName')
    team_stats['statPerGame'] = team_stats['statValue'] / games_played
    return team_stats

def display_ratings():
    st.markdown(f"""**Ratings**
    1.	**FPI**: Higher values suggest a stronger team with better chances of winning games.
    2.	**Elo**: A higher Elo rating means a team is performing well compared to others, indicating greater strength.
    3.	**SP+**: Higher SP+ ratings indicate more efficient and successful performances on both offense and defense.
    4.	**SRS**: A higher SRS value reflects a team’s ability to win games by larger margins against stronger opponents.
           	""")
    with col1:
        team_color, team_logo = team_information(team_1)
        st.markdown(f"""
            <div style='display: flex; align-items: center;'>
                <img src='{team_logo}' alt='team logo' style='width:75px; height:auto; margin-right:15px;'>
                <h2 style='color: {team_color}; margin: 0;'>{team_1}</h2>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f'##### Ratings')
        st.dataframe(team_1_metrics_df, hide_index=True, use_container_width=True)
    with col2:
        team_color, team_logo = team_information(team_2)
        st.markdown(f"""
            <div style='display: flex; align-items: center;'>
                <img src='{team_logo}' alt='team logo' style='width:75px; height:auto; margin-right:15px;'>
                <h2 style='color: {team_color}; margin: 0;'>{team_2}</h2>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f'##### Ratings')
        st.dataframe(team_2_metrics_df, hide_index=True, use_container_width=True)


def display_stats():
    with (col1):
        games = get_games_played(team_1)
        st.markdown(f'##### Team Statistics ({games} games)')
        st.dataframe(team_1_stats_df,
                     hide_index=True,
                     use_container_width=True,
                     height=500)
    with col2:
        games = get_games_played(team_2)
        st.markdown(f'##### Team Statistics ({games} games)')
        st.dataframe(team_2_stats_df,
                     hide_index=True,
                     use_container_width=True,
                     height=500)


team_1, team_2, year = select_team_year()
team_1_metrics_df = get_stats(team_1)
team_2_metrics_df = get_stats(team_2)
team_1_stats_df = get_team_stats(team_1)
team_2_stats_df = get_team_stats(team_2)
col1, col2 = st.columns(2)
display_ratings()
display_stats()

