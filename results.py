import json
from datetime import datetime
import cfbd
import pandas as pd
import requests
import streamlit as st

# Initialize global variables
API_KEY = st.secrets["cfbd_api_key"]
headers = {
    'accept': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}
st.session_state.headers = headers
configuration = cfbd.Configuration(access_token=API_KEY)
st.set_page_config(
    page_title="CFB Data",
    page_icon=":football:",
    layout="wide",
)

cfbd_logo = "images/cfbd.png"
st.logo(cfbd_logo)
st.session_state.team = ''
st.sidebar.title("CFB Data")


def is_number(s):
    """Helper function to check if a value can be converted to a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_cfbd_data(year, team):
    with cfbd.ApiClient(configuration) as api_client:
        games_api = cfbd.GamesApi(api_client)
        coaches_api = cfbd.CoachesApi(api_client)
        teams_api = cfbd.TeamsApi(api_client)
        team_info = teams_api.get_teams()
        with open('team_info.json', 'w') as json_file:
            json.dump([team.to_dict() for team in team_info], json_file)
        games = games_api.get_games(year=year, team=team)
        games_data = games_api.get_game_player_stats(year=year, team=team)
        teams_data = games_api.get_game_team_stats(year=year, team=team)
        games_df = pd.DataFrame([game.to_dict() for game in games])
        coach_data = coaches_api.get_coaches(year=year, team=team)
        return games_df, games_data, team_info, teams_data, coach_data


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


def get_team_records():
    # Make the API request
    url = f'https://api.collegefootballdata.com/records?year={year}&team={team}'
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        team_records = response.json()  # Get the raw JSON response
        return team_records
    else:
        st.write(f"Failed to fetch data. Status code: {response.status_code}")
        return None


def create_team_records(valid_records):
    if not valid_records:
        return pd.DataFrame()  # Return an empty DataFrame if no valid records

    team_records_list = []

    for record in valid_records:
        team_record = {
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


def create_player_stats(games_data):
    # Create a list to store the extracted data
    game_stats = []

    # Loop through each game
    for game in games_data:
        game_id = game.id

        # Loop through each team in the game
        for team in game.teams:
            team_name = team.team

            # Loop through each category and extract statistics
            for category in team.categories:
                category_name = category.name

                # For each type inside the category
                for stat_type in category.types:
                    stat_name = stat_type.name

                    # Extract the statistics of athletes
                    for athlete in stat_type.athletes:
                        athlete_id = athlete.id
                        athlete_name = athlete.name
                        stat_value = athlete.stat

                        # Append the data to the list
                        game_stats.append({
                            'game_id': game_id,
                            'team': team_name,
                            'category': category_name,
                            'stat_name': stat_name,
                            'athlete_id': athlete_id,
                            'athlete_name': athlete_name,
                            'stat_value': stat_value
                        })

    # Convert the list to a pandas DataFrame
    stats_df = pd.DataFrame(game_stats)
    return stats_df


def create_team_stats(teams_data):
    # Create a list to store the extracted data
    team_stats = []

    # Loop through each game
    for game in teams_data:
        game_id = game.id

        # Loop through each team in the game
        for team in game.teams:
            team_name = team.team
            team_id = team.team_id
            conference = team.conference
            points = team.points

            # Loop through each stat category
            for stat in team.stats:
                category = stat.category
                stat_value = stat.stat

                # Append the team stat to the list
                team_stats.append({
                    'game_id': game_id,
                    'team_id': team_id,
                    'team': team_name,
                    'conference': conference,
                    'points': points,
                    'category': category,
                    'stat_value': stat_value
                })

    # Convert the list to a pandas DataFrame
    team_stats_df = pd.DataFrame(team_stats)
    team_stats_df = team_stats_df.sort_values('category', ascending=True)
    return team_stats_df


def create_coach(coaches_data):
    # List to store the extracted data
    coach_data = []
    # Loop through each coach object and extract the information
    for coach in coaches_data:
        coach_data.append({
            'first_name': str(coach.first_name),
            'last_name': str(coach.last_name),
        })
    # Convert the list to a pandas DataFrame
    coach_df = pd.DataFrame(coach_data)
    for index, row in coach_df.iterrows():
        full_name = f"{row['first_name']} {row['last_name']}"
        return full_name


def display_results():# Display results for each game
    games_columns = {
        'seasonType': 'Season',
        'week': 'Week',
        'startDate': st.column_config.DatetimeColumn("Date", format='MM/DD/YY'),
        'homeTeam': 'Home Team',
        'homePoints': 'Score',
        'homeLineScores': 'Line Scores',
        'awayTeam': 'Away Team',
        'awayPoints': 'Score',
        'awayLineScores': 'Line Scores',
        'attendance': 'Attendance',
    }
    st.markdown("Select a game for game statistics")
    games_played = st.dataframe(games_df,
                                column_order=games_columns.keys(),
                                column_config=games_columns,
                                height=500,
                                selection_mode='single-row',
                                on_select='rerun',
                                hide_index=True)
    selected_game = games_df.iloc[games_played.selection.rows]

    if not selected_game.empty and year >= 2004:
        team_game_stats_df = team_stats_df[team_stats_df['game_id'].values == selected_game['id'].values[0]]
        gt_team_stats_df = team_game_stats_df[team_game_stats_df['team'] == team]
        other_team_stats_df = team_game_stats_df[team_game_stats_df['team'] != team]
        players_stats_df = stats_df[stats_df['game_id'].values == selected_game['id'].values[0]]
        gt_stats_df = players_stats_df[players_stats_df['team'] == team]
        other_stats_df = players_stats_df[players_stats_df['team'] != team]

        # Convert 'stat_value' where the values can be converted to numeric, leave others unchanged
        gt_stats_df.loc[:, 'stat_value'] = gt_stats_df['stat_value'].apply(lambda x: float(x) if is_number(x) else x)
        other_stats_df.loc[:, 'stat_value'] = other_stats_df['stat_value'].apply(
            lambda x: float(x) if is_number(x) else x)
        # Get unique categories dynamically from the 'category' field
        gt_categories = sorted(gt_stats_df['category'].unique())
        other_categories = sorted(other_stats_df['category'].unique())

        col1, col2 = st.columns(2)

        with col1:
            st.header(team)
            st.markdown('#### Team Statistics')
            st.dataframe(gt_team_stats_df[['category', 'stat_value']],
                         use_container_width=True,
                         hide_index=True)

            # Display pivot tables for each unique category
            for category in gt_categories:
                st.markdown(f'#### {category.capitalize()} Statistics')
                filtered_gt_stats = gt_stats_df[gt_stats_df['category'] == category]
                if not filtered_gt_stats.empty:
                    gt_pivot = pd.pivot_table(filtered_gt_stats, values='stat_value', index='athlete_name',
                                              columns='stat_name', aggfunc='sum')
                    st.dataframe(gt_pivot, use_container_width=True)
                else:
                    st.write(f"No data available for {category.capitalize()}")

        with col2:
            other_team = other_stats_df['team'].unique()[0] if not other_stats_df.empty else 'Opponent'
            st.header(other_team)
            st.markdown('#### Team Statistics')
            st.dataframe(other_team_stats_df[['category', 'stat_value']],
                         use_container_width=True,
                         hide_index=True)

            # Display pivot tables for each unique category for the other team
            for category in other_categories:
                st.markdown(f'#### {category.capitalize()} Statistics')
                filtered_other_stats = other_stats_df[other_stats_df['category'] == category]
                if not filtered_other_stats.empty:
                    other_pivot = pd.pivot_table(filtered_other_stats, values='stat_value', index='athlete_name',
                                                 columns='stat_name', aggfunc='sum')
                    st.dataframe(other_pivot, use_container_width=True)
                else:
                    st.write(f"No data available for {category.capitalize()}")
    else:
        st.write("No statistics available")


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
    filtered_teams = sorted([team['school'] for team in team_data if team['classification'] in ['fbs', 'fcs']])
    if st.session_state.team != '':
        team_index = filtered_teams.index(st.session_state.team)
    else:
        team_index = filtered_teams.index('Georgia Tech')
    team = st.sidebar.selectbox('Select Team Name', options=filtered_teams, index=team_index)
    st.session_state.team = team
    st.session_state.year = year
    return team, year


team, year = select_team_year()
games_df, games_data, team_info, teams_data, coach_data = get_cfbd_data(year, team)
team_color, team_logo = team_information()
st.markdown(f"""
    <div style='display: flex; align-items: center;'>
        <img src='{team_logo}' alt='team logo' style='width:100px; height:auto; margin-right:15px;'>
        <h1 style='color: {team_color}; margin: 0;'>{team} {year} Results</h1>
    </div>
    """, unsafe_allow_html=True)
st.sidebar.markdown('Statistics per Game available 2004 and later')
team_records = get_team_records()
team_records_df = create_team_records(team_records)
stats_df = create_player_stats(games_data)
team_stats_df = create_team_stats(teams_data)
coach_name = create_coach(coach_data)
if len(team_records_df) == 1:
    st.markdown(f"##### Overall: {int(team_records_df['Total Wins'].iloc[0])} - {int(team_records_df['Total Losses'].iloc[0])}, "
                f"Conference: {int(team_records_df['Conference Wins'].iloc[0])} - {int(team_records_df['Conference Losses'].iloc[0])}, "
                f"Home: {int(team_records_df['Home Wins'].iloc[0])} - {int(team_records_df['Home Losses'].iloc[0])}, "
                f"Away: {int(team_records_df['Away Wins'].iloc[0])} - {int(team_records_df['Away Losses'].iloc[0])}, "
                f"Coach: {coach_name}"
                )
display_results()



