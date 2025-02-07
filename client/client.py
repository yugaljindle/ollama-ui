import streamlit as st
import requests

# ======================
# UI SETUP
# ======================
st.set_page_config(
    page_title="Astro AI",
    page_icon="🔆",
    initial_sidebar_state="collapsed",
    layout="centered"
)

# Centered Title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🔆 Astro AI")

# ======================
# CORE LOGIC
# ======================

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input and processing
if prompt := st.chat_input("Ask me about your stars..."):
    # User message handling
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # API call handling
    with st.chat_message("assistant"):
        with st.spinner("Consulting the stars..."):
            try:
                response = requests.post(
                    "http://localhost:8000/generate",
                    json={"prompt": prompt},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    timeout=300  # 5 minutes
                )
                response.raise_for_status()
                result = response.json().get("response", "Error: Invalid response format")
            except Exception as e:
                result = f"Celestial connection failed: {str(e)}"
        
        st.markdown(result)
        st.session_state.messages.append({"role": "assistant", "content": result})
