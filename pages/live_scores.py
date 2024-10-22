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


def get_scoreboard():
    url = "https://api.collegefootballdata.com/scoreboard"
    querystring = {"classification": "fbs"}
    return fetch_data_from_api(url, query_params=querystring)


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
    scoreboard = get_scoreboard()
    games_list = [
        {
            'home_id': game['homeTeam']['id'],
            'away_id': game['awayTeam']['id'],
            'home_team': game['homeTeam']['name'],
            'away_team': game['awayTeam']['name'],
            'status': game['status'],
            'period': game['period'],
            'clock': game['clock'],
            'tv': game['tv'],
            'situation': game['situation'],
            'possession': game['possession'],
            'home_team_score': game['homeTeam']['points'],
            'away_team_score': game['awayTeam']['points'],
            'spread': game['betting']['spread'],
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
    if games_df.empty:
        st.markdown("No games currently underway.")
        return
    games_with_logos = add_logos(games_df)

    for index, game in games_with_logos.iterrows():
        if game['status'] == 'in_progress':  # Only display in-progress or finished games
            away_color = game['away_team_color'] or "#ffffff"  # Default to white if no color
            home_color = game['home_team_color'] or "#ffffff"  # Default to white if no color

            # Apply a consistent gradient background for the whole game block
            st.components.v1.html(f"""
                <div style="background: linear-gradient(to right, {away_color}50, {home_color}50);
                            border-radius: 20px; padding: 20px; margin-bottom: 20px; font-family: 'Verdana', sans-serif;
                            display: flex; justify-content: space-between; align-items: center; 
                            text-align: center;
                            width: 100%; max-width: 800px; margin-left: auto; margin-right: auto; box-sizing: border-box;">

                    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
    
                            <img src='{game['away_team_logo']}' width='50' style='margin-left: 10px;'>
                            {" 🏈" if game['possession'] == 'away' else ""} 
                        </div>
                        <div style="font-size: 16px; font-weight: bold; margin-top: 0; overflow: hidden;
                                    text-overflow: ellipsis; white-space: nowrap; max-width: 250px;">{game['away_team']}</div>
                        <div style="font-size: 24px; font-weight: bold; margin-top: 0;">{int(game['away_team_score'])}</div>
                    </div>

                    <div style="flex: 1; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                        <h4 style="font-family: 'Verdana', sans-serif; margin: 0;">{int(game['period'])}Q</h4>
                        <p style="margin: 0;">{format_clock(game['clock'])}</p>
                        <p style="margin: 0; font-size: 12px"><i>{f"{game['tv']} ▪️ {game['spread']}"}</i></p><br>
                        <p style="margin: 0;">{game['situation'] or "No situation available"}</p>
                        
                    </div>

                    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;"> 
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <img src='{game['home_team_logo']}' width='50' style='margin-left: 10px;'>
                            {" 🏈" if game['possession'] == 'home' else ""} 
                        </div>
                        <div style="font-size: 16px; font-weight: bold; margin-top: 0; overflow: hidden;
                                    text-overflow: ellipsis; white-space: nowrap; max-width: 250px;">{game['home_team']}</div>
                        <div style="font-size: 24px; font-weight: bold; margin-top: 0;">{int(game['home_team_score'])}</div>
                    </div>
                </div>
            """)

    # Display the last updated time with Verdana font applied
    last_updated = time.strftime("%I:%M %p")  # e.g., "03:45 PM"
    st.markdown(
        f"<div style='text-align: center; font-size: 12px; color: #888;'><i>Last updated: {last_updated}</i></div>",
        unsafe_allow_html=True)


st.markdown(f"### Games in Progress")
display_scoreboard()