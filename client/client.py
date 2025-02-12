#!/usr/bin/env python3

import requests
import configparser
import streamlit as st
from uuid import uuid4

config = configparser.ConfigParser()
config.read('../config.ini')

APP_NAME = config["common"]["app_name"]
APP_ICON = config["common"]["app_icon"]
CHAT_PLACEHOLDER = config["client"]["chat_input_placeholder"]
WAITING_TEXT = config["client"]["waiting_text"]
SERVER_PORT = config["server"]["port"]

# ======================
# SETUP
# ======================
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    initial_sidebar_state="collapsed",
    layout="centered"
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())

# Centered Title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title(f"{APP_ICON} {APP_NAME}")

# ======================
# CORE LOGIC
# ======================

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.text(msg["content"])

# Chat input and processing
if prompt := st.chat_input(CHAT_PLACEHOLDER):
    # User message handling
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.text(prompt)

    # API call handling
    with st.spinner(WAITING_TEXT):
        try:
            response = requests.post(
                f"http://localhost:{SERVER_PORT}/generate",
                json={
                    "prompt": prompt,
                    "session_id": st.session_state.session_id
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=300  # 5 minutes
            )
            response.raise_for_status()
            result = response.json().get("response", "Error: Invalid response format")
        except Exception as e:
            result = f"Connection failed: {str(e)}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.text(result)
    st.session_state.messages.append({"role": "assistant", "content": result})
