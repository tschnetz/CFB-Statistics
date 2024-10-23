from datetime import date
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
from config_api import headers

YEAR = 2024

# Update this function to return both logos and colors
def team_information():
    with open('team_info.json', 'r') as file:
        data_dict = json.load(file)
    colors_logos_df = pd.DataFrame(data_dict)
    colors_logos_df = colors_logos_df[['school', 'logos', 'color', 'mascot']]  # Add color here
    # drop rows with logos = None
    colors_logos_df = colors_logos_df[colors_logos_df['logos'].notna()]
    colors_logos_df['logos'] = colors_logos_df['logos'].apply(lambda x: x[0] if isinstance(x, list) else x)
    return colors_logos_df

# Function to get team logo and color based on school name
def get_team_logo_color(team_name, team_info_df):
    team_data = team_info_df[team_info_df['school'] == team_name]
    if not team_data.empty:
        logo = team_data.iloc[0]['logos']
        color = team_data.iloc[0]['color']
        if team_data.iloc[0]['mascot']:
            mascot = team_data.iloc[0]['mascot']
        else:
            mascot = "  "
        return logo, color, mascot
    return None, "#000000", " "  # Default to black if not found


def get_records(year):
    url = f'https://api.collegefootballdata.com/records?year={year}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")


def create_records(valid_records):
    if not valid_records:
        return pd.DataFrame()
    team_records_list = []
    for record in valid_records:
        team_record = {
            'team': record['team'],
            'Total Wins': record['total'].get('wins', 0),
            'Total Losses': record['total'].get('losses', 0),
            'Conference Wins': record['conferenceGames'].get('wins', 0),
            'Conference Losses': record['conferenceGames'].get('losses', 0),
        }
        team_records_list.append(team_record)
    return pd.DataFrame(team_records_list)


def get_schedule():
    url = "https://api.collegefootballdata.com/calendar"
    querystring = {"year": YEAR}
    response = requests.request("GET", url, headers=headers, params=querystring)
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
    st.header(selected_week)
    week = selected.index(selected_week) + 1
    return week

# Pass the week as a parameter
def get_polls(week):
    url = "https://api.collegefootballdata.com/rankings"
    querystring = {"year": YEAR, "week": week}
    response = requests.request("GET", url, headers=headers, params=querystring)
    polls = response.json()
    return polls

# Function to create a DataFrame for a given poll's ranks
def create_poll_df(poll_data):
    ranks = poll_data['ranks']
    poll_name = poll_data['poll']

    # Extract the required fields for each rank
    poll_ranks = [
        {
            'Rank': rank['rank'],
            'School': rank['school'],
            'Conference': rank['conference'],
            'First Place Votes': rank.get('firstPlaceVotes', 0),  # Handle missing firstPlaceVotes
            'Points': rank['points']
        }
        for rank in ranks
    ]

    # Create a DataFrame from the list of dicts
    df = pd.DataFrame(poll_ranks)
    df.name = poll_name  # Add the poll name to the DataFrame for reference
    return df


# Function to display poll rankings with logos and colors in a table format
def display_poll(poll_data, team_info_df):
    st.markdown(f"### {poll_data['poll']}")

    # Create the table headers with the same font as Streamlit
    html = """
    <table style="width: 100%; border-collapse: collapse; font-family: 'helvetica'; font-size: 16px;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Rank</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Team</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Conference</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">1st Place Votes</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Points</th>
            </tr>
        </thead>
        <tbody>
    """

    # Add a row for each team
    for team in poll_data['ranks']:
        logo, color, mascot = get_team_logo_color(team['school'], team_info_df)

        # Filter the records DataFrame to get the corresponding team record
        team_record = records[records['team'] == team['school']]
        if not team_record.empty:
            wins = team_record.iloc[0]['Total Wins']
            losses = team_record.iloc[0]['Total Losses']
        else:
            wins = "N/A"
            losses = "N/A"

        first_place_votes = team.get('firstPlaceVotes', 0)
        conference = team['conference']
        points = team['points']

        # Add each row with team info, including records
        html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;"><b>{team['rank']}</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd; display: flex; align-items: center;">
                            <img src="{logo}" width="30" height="30" style="margin-right: 10px;">
                            <span style="color: {color}; font-weight: bold; font-size: 20px;">{team['school']} {mascot}</span>
                            <span style="margin-left: 10px;">({wins} - {losses})</span>  <!-- Use <span> instead of <p> -->
                        </td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{conference}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{first_place_votes}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{points:,}</td>
                    </tr>
                    """

    # Close the table
    html += """
        </tbody>
    </table>
    """

    # Use st.components.v1.html to properly render the HTML
    components.html(html, height=600, scrolling=True)


# Main app logic
week = select_week()
team_info_df = team_information()
polls = get_polls(week)  # Pass the selected week to the get_polls function
records = create_records(get_records(YEAR))

# Separate the AP and Coaches polls from the rest
ap_poll = None
coaches_poll = None
other_polls = []

for poll in polls[0]['polls']:
    if poll['poll'] == "AP Top 25":
        ap_poll = poll
    elif poll['poll'] == "Coaches Poll":
        coaches_poll = poll
    else:
        other_polls.append(poll)

# Display the AP poll first, followed by the Coaches poll, then the rest
if ap_poll:
    display_poll(ap_poll, team_info_df)

if coaches_poll:
    display_poll(coaches_poll, team_info_df)

# Optionally display other polls
for poll in other_polls:
    display_poll(poll, team_info_df)