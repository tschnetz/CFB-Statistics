import json
import streamlit as st
import streamlit.components.v1
import pandas as pd
import requests
import time
from config_api import headers



# Helper function to make HTTP requests and handle errors
def fetch_data_from_api(url, query_params=None):
    try:
        response = requests.get(url, headers=headers, params=query_params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None


def get_scoreboard(conference):
    url = "https://api.collegefootballdata.com/scoreboard"
    querystring = {"classification": "fbs", "conference": conference}
    return fetch_data_from_api(url, query_params=querystring)


def get_conferences():
    url = "https://api.collegefootballdata.com/conferences"
    return fetch_data_from_api(url)


def team_information():
    with open('team_info.json', 'r') as file:
        data_dict = json.load(file)
    colors_logos_df = pd.DataFrame(data_dict)[['id', 'logos', 'color']]
    # Drop rows where logos or color is None
    colors_logos_df = colors_logos_df[colors_logos_df['logos'].notna() & colors_logos_df['color'].notna()]
    # Handle lists of logos
    colors_logos_df['logos'] = colors_logos_df['logos'].apply(lambda x: x[0] if isinstance(x, list) else x)
    return colors_logos_df


def add_logos(games_df):
    logos_df = team_information()
    # Merge logos and colors for the home team
    games_with_logos = games_df.merge(logos_df, left_on='home_id', right_on='id', how='left')
    games_with_logos = games_with_logos.rename(columns={'logos': 'home_team_logo', 'color': 'home_team_color'}).drop(
        'id', axis=1)

    # Merge logos and colors for the away team
    games_with_logos = games_with_logos.merge(logos_df, left_on='away_id', right_on='id', how='left')
    games_with_logos = games_with_logos.rename(columns={'logos': 'away_team_logo', 'color': 'away_team_color'}).drop(
        'id', axis=1)

    return games_with_logos

def create_scoreboard():
    scoreboard = get_scoreboard(conf_abbrev)
    games_list = [
        {
            'home_id': game['homeTeam']['id'],
            'away_id': game['awayTeam']['id'],
            'home_team': game['homeTeam']['name'],
            'away_team': game['awayTeam']['name'],
            'status': game['status'],
            'period': game['period'],
            'clock': game['clock'],
            'situation': game['situation'],
            'possession': game['possession'],
            'home_team_score': game['homeTeam']['points'],
            'away_team_score': game['awayTeam']['points'],
        }
        for game in scoreboard
    ]
    return pd.DataFrame(games_list)


# Helper function to format clock display
def format_clock(clock):
    if clock is None:
        return "00:00"

    parts = clock.split(":")
    if len(parts) == 3:  # If clock has hours, minutes, and seconds
        return f"{parts[1]}:{parts[2]}"  # Return only minutes and seconds
    elif len(parts) == 2:  # Already in minutes and seconds
        return clock
    else:
        return "00:00"  # Default value


# Helper function to display team info (DRY principle)
def display_team_info(team_logo, team_name, team_score, possession_icon):
    st.markdown(f"""
        <div style='text-align: center;'>
            <div style="display: inline-flex; align-items: center; justify-content: center;">
                {possession_icon} <img src='{team_logo}' width='50' style='margin-left: 5px;'>
            </div>
            <br>
            <b>{team_name}</b><br>
            <h2 style='font-weight: bold;'>{int(team_score)}</h2>
        </div>
    """, unsafe_allow_html=True)


# Main scoreboard display function
@st.fragment(run_every="60s")
def display_scoreboard():
    # Loop through each game and generate the scoreboard
    games_df = create_scoreboard()
    games_with_logos = add_logos(games_df)

    for index, game in games_with_logos.iterrows():
        if game['status'] == 'in_progress':  # Only display in-progress or finished games
            away_color = game['away_team_color'] or "#ffffff"  # Default to white if no color
            home_color = game['home_team_color'] or "#ffffff"  # Default to white if no color

            # Apply a gradient background for the whole game block using a <div>
            st.components.v1.html(f"""
                <div style="background: linear-gradient(to right, {away_color}80, transparent, {home_color}80);
                            border-radius: 20px; padding: 20px; margin-bottom: 20px; font-family: 'Arial', sans-serif;
                            display: flex; justify-content: space-between; align-items: center; text-align: center;">
                    <!-- Away team column -->
                    <div style="flex: 1; text-align: center;">
                        <div style="display: inline-flex; align-items: center;">
                            {"🏈" if game['possession'] == 'away' else ""} 
                            <img src='{game['away_team_logo']}' width='50' style='margin-left: 10px;'>
                        </div>
                        <div style="font-size: 18px; font-weight: bold;">{game['away_team']}</div>
                        <div style="font-size: 24px; font-weight: bold;">{int(game['away_team_score'])}</div>
                    </div>

                    <!-- Game information (center column) -->
                    <div style="flex: 1; text-align: center;">
                        <h4 style="font-family: 'Arial', sans-serif; margin: 0;">{int(game['period'])}Q</h4>
                        <p style="margin: 0;">{format_clock(game['clock'])}</p>
                        <p style="margin: 0;">{game['situation'] or "No situation available"}</p>
                    </div>

                    <!-- Home team column -->
                    <div style="flex: 1; text-align: center;">
                        <div style="display: inline-flex; align-items: center;">
                            {"🏈" if game['possession'] == 'home' else ""} 
                            <img src='{game['home_team_logo']}' width='50' style='margin-left: 10px;'>
                        </div>
                        <div style="font-size: 18px; font-weight: bold;">{game['home_team']}</div>
                        <div style="font-size: 24px; font-weight: bold;">{int(game['home_team_score'])}</div>
                    </div>
                </div>
            """)

    # Display the last updated time with Arial font applied
    last_updated = time.strftime("%I:%M %p")  # e.g., "03:45 PM"
    st.markdown(
        f"<div style='text-align: center; font-size: 12px; color: #888;'><i>Last updated: {last_updated}</i></div>",
        unsafe_allow_html=True)


# Main logic for displaying conferences and scoreboard
conferences = get_conferences()

# Filter conferences (id <= 50 and classification == 'fbs')
filtered_conferences = [conf for conf in conferences if conf['id'] <= 50 and conf['classification'] == 'fbs']
filtered_conferences = sorted(filtered_conferences, key=lambda x: x['short_name'])

# Sidebar for conference selection
conf_names = [conf['short_name'] for conf in filtered_conferences]
selected_conf_name = st.sidebar.selectbox("Select Conference", conf_names)
selected_conf = next((conf for conf in filtered_conferences if conf['short_name'] == selected_conf_name), None)

# Display the selected conference's games
if selected_conf:
    conf_abbrev = selected_conf['abbreviation']
    st.markdown(f"### {selected_conf['short_name']} Games")
    display_scoreboard()