""" This module is used to manage the session ID for the Streamlit app. """

import streamlit as st
from datetime import datetime
from database import initialize_session

# Get the session ID for the current user
def get_session_id():
    """ Get the session ID for the current user. """
    if 'session_id' not in st.session_state:
        # Generate a new session ID based on the current timestamp 
        st.session_state['session_id'] = datetime.now().strftime("%Y%m%d%H%M%S")
        # Save the session ID to the database as a new session
        initialize_session(st.session_state['session_id'])
    return st.session_state['session_id']
