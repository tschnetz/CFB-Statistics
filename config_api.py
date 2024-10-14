import cfbd
import streamlit as st

# Initialize global variables
API_KEY = st.secrets["cfbd_api_key"]
headers = {
    'accept': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}
st.session_state.headers = headers
configuration = cfbd.Configuration(access_token=API_KEY)