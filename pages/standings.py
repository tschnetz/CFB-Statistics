import json
import streamlit as st
import streamlit.components.v1
import pandas as pd
import requests
from config_api import headers

YEAR = 2024


def get_conferences():
    url = "http://api.collegefootballdata.com/conferences"
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers)

    if response.status_code == 200:  # Check if the request was successful
        conferences = response.json()  # Get the raw JSON response
        return conferences
    else:
        st.write(f"Failed to fetch data. Status code: {response.status_code}")
        return None


def team_information():
    with open('team_info.json', 'r') as file:
        data_dict = json.load(file)
    colors_logos_df = pd.DataFrame(data_dict)
    colors_logos_df = colors_logos_df[['school', 'logos']]
    # drop rows with logos = None
    colors_logos_df = colors_logos_df[colors_logos_df['logos'].notna()]
    colors_logos_df['logos'] = colors_logos_df['logos'].apply(lambda x: x[0] if isinstance(x, list) else x)
    colors_logos_df['logos'] = colors_logos_df['logos'].str.replace('http://', 'https://')

    return colors_logos_df


def add_logos():
    logos_df = team_information()
    # Merge logos for the home team
    teams_with_logos = teams.merge(logos_df, left_on='Team', right_on='school', how='left')
    teams_with_logos = teams_with_logos.rename(columns={'logos': 'Team Logo'}).drop('school', axis=1)
    return teams_with_logos


def get_team_records(conf):
    # Make the API request
    url = "https://api.collegefootballdata.com/records"
    querystring = {"year": "2024", "conference": conf}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

    # Check if the request was successful
    if response.status_code == 200:
        team_records = response.json()  # Get the raw JSON response
        return team_records
    else:
        st.write(f"Failed to fetch data. Status code: {response.status_code}")
        return None


def clean_team_records(valid_records):
    if not valid_records:
        return pd.DataFrame()  # Return an empty DataFrame if no valid records

    team_records_list = []

    for record in valid_records:
        team_record = {
            'Team': record['team'],
            'Total Games': record['total'].get('games', 0),
            'Total Wins': record['total'].get('wins', 0),
            'Total Losses': record['total'].get('losses', 0),
            'Conference Games': record['conferenceGames'].get('games', 0),
            'Conference Wins': record['conferenceGames'].get('wins', 0),
            'Conference Losses': record['conferenceGames'].get('losses', 0),
            'Home Games': record['homeGames'].get('games', 0),
            'Home Wins': record['homeGames'].get('wins', 0),
            'Home Losses': record['homeGames'].get('losses', 0),
            'Away Games': record['awayGames'].get('games', 0),
            'Away Wins': record['awayGames'].get('wins', 0),
            'Away Losses': record['awayGames'].get('losses', 0),
            'Expected Wins': record.get('expectedWins', "N/A")
        }
        team_records_list.append(team_record)

    team_record_df = pd.DataFrame(team_records_list)
    return team_record_df


def display_standings(teams):
    # Start the HTML for the standings table
    table_html = """
        <style>
        .scrollable-table {
            max-height: 825px; /* Adjust as needed */
            overflow-y: auto;
        }
        table {
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif; 
            font-size: 14px;
        }
        th, td {
            padding: 8px;
        }
        /* Target <th> in the second <tr> within <thead> */
        thead > tr:nth-child(2) > th { 
            width: 5%; /* Adjust this value as needed */
        }
        /* Target the first column (td) in each row */
        td:first-child { 
        width: 20%; /* Adjust this value as needed */
        }
        </style>
        <div class="scrollable-table">
        <table style="border: 1px solid black; border-collapse: collapse; width: 100%; text-align: center;">
            <thead>
                <tr style="background-color: #e0e0e0;">
                    <th rowspan="2" style="border: 1px solid black;">Team</th>
                    <th colspan="3" style="border: 1px solid black;">Totals</th>
                    <th colspan="3" style="border: 1px solid black;">Conference</th>
                    <th colspan="3" style="border: 1px solid black;">Home</th>
                    <th colspan="3" style="border: 1px solid black;">Away</th>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid black;">G</th>
                    <th style="border: 1px solid black;">W</th>
                    <th style="border: 1px solid black;">L</th>
                    <th style="border: 1px solid black;">G</th>
                    <th style="border: 1px solid black;">W</th>
                    <th style="border: 1px solid black;">L</th>
                    <th style="border: 1px solid black;">G</th>
                    <th style="border: 1px solid black;">W</th>
                    <th style="border: 1px solid black;">L</th>
                    <th style="border: 1px solid black;">G</th>
                    <th style="border: 1px solid black;">W</th>
                    <th style="border: 1px solid black;">L</th>
                </tr>
            </thead>
            <tbody>
        """

    # Loop through each team and generate rows dynamically
    for index, row in teams.iterrows():
        team_row = f"""
        <tr>
            <td style="border: 1px solid black; text-align: left; padding: 5px;">
                <img src="{row['Team Logo']}" width="30" style="vertical-align: middle; margin-right: 10px;">
                {row['Team']}
            </td>
            <td style="border: 1px solid black;">{row['Total Games']}</td>
            <td style="border: 1px solid black;">{row['Total Wins']}</td>
            <td style="border: 1px solid black;">{row['Total Losses']}</td>
            <td style="border: 1px solid black;">{row['Conference Games']}</td>
            <td style="border: 1px solid black;">{row['Conference Wins']}</td>
            <td style="border: 1px solid black;">{row['Conference Losses']}</td>
            <td style="border: 1px solid black;">{row['Home Games']}</td>
            <td style="border: 1px solid black;">{row['Home Wins']}</td>
            <td style="border: 1px solid black;">{row['Home Losses']}</td>
            <td style="border: 1px solid black;">{row['Away Games']}</td>
            <td style="border: 1px solid black;">{row['Away Wins']}</td>
            <td style="border: 1px solid black;">{row['Away Losses']}</td>
        </tr>
        """
        table_html += team_row

    # Close the table HTML
    table_html += "</tbody></table></div>"

    return table_html


def create_standings(teams):
    # Instead of generating separate tables for each team, create a single table for the conference
    st.components.v1.html(display_standings(teams), height=825)  # Ensure the full HTML table is rendered


# Main body
conferences = get_conferences()
# Sort the conferences by short_name and eliminate ids > 50 and classification != fbs
conferences = [conf for conf in conferences if conf['id'] <= 50 and conf['classification'] == 'fbs']
conferences = sorted(conferences, key=lambda x: x['short_name'])

# Get a list of conference short names for the selectbox
conf_names = [conf['short_name'] for conf in conferences]
selected_conf_name = st.sidebar.selectbox("Select Conference", conf_names)

# Find the selected conference
selected_conf = next((conf for conf in conferences if conf['short_name'] == selected_conf_name), None)

if selected_conf:
    conf_abbrev = selected_conf['abbreviation']
    conf_teams = get_team_records(conf_abbrev)
    teams = clean_team_records(conf_teams)
    teams = teams.sort_values(by=['Total Wins', 'Conference Wins'], ascending=False)
    teams_with_logos = add_logos()
    st.markdown(f"#### {selected_conf['short_name']} Conference")
    create_standings(teams_with_logos)