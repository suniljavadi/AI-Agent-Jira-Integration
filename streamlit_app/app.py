import json

import requests
import streamlit as st


st.set_page_config(page_title="AI Engineering Assistant", page_icon="AI", layout="wide")
API_URL = st.sidebar.text_input("API URL", "http://localhost:8000")
st.title("AI Engineering Assistant")
st.caption("Mock Jira mode - approval-gated engineering workflows")

if "conversation_id" not in st.session_state: st.session_state.conversation_id = None
if "messages" not in st.session_state: st.session_state.messages = []

with st.sidebar:
    st.subheader("Issue Search")
    search = st.text_input("Search text")
    priority = st.selectbox("Priority", ["Any", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
    if st.button("Search"):
        params = {"query": search}
        if priority != "Any": params["priority"] = priority
        response = requests.get(f"{API_URL}/api/v1/search", params=params, timeout=10)
        st.json(response.json())
    st.divider()
    st.subheader("Activity")
    st.write(f"{len(st.session_state.messages)} chat event(s)")

for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.write(message["content"])

prompt = st.chat_input("Ask about Jira work...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    payload = {"message": prompt, "conversation_id": st.session_state.conversation_id}
    data = requests.post(f"{API_URL}/api/v1/chat", json=payload, timeout=30).json()
    st.session_state.conversation_id = data.get("conversation_id", st.session_state.conversation_id)
    content = data.get("message") or data.get("error") or json.dumps(data)
    st.session_state.messages.append({"role": "assistant", "content": content})
    if data.get("requires_approval"):
        st.warning(content)
        if st.button("Approve action"):
            approved = requests.post(f"{API_URL}/api/v1/chat", json={"message": "Approve", "conversation_id": st.session_state.conversation_id, "approve": True}, timeout=30).json()
            st.session_state.messages.append({"role": "assistant", "content": approved.get("message", json.dumps(approved))})
    else:
        st.json(data.get("data", data))
    st.rerun()
