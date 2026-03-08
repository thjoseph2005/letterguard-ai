"""Simple chat UI for deterministic LetterGuard QA commands."""

import streamlit as st

from app.services.chat_command_service import execute_chat_command, parse_chat_instruction

st.set_page_config(page_title="LetterGuard AI Chat", page_icon="🛡️", layout="centered")
st.title("LetterGuard AI Chat")
st.caption("Type quality-check commands for local deterministic QA workflow execution.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form("chat_form"):
    message = st.text_input("Instruction", placeholder="Run quality check for E001_letter.pdf")
    submitted = st.form_submit_button("Submit")

if submitted and message.strip():
    command = parse_chat_instruction(message)
    response = execute_chat_command(command)
    st.session_state.chat_history.append(
        {
            "input": message,
            "response_message": response.get("message", ""),
            "intent": response.get("intent", "unknown"),
            "data": response.get("data", {}),
            "status": response.get("status", "error"),
        }
    )

for idx, item in enumerate(reversed(st.session_state.chat_history), start=1):
    st.markdown(f"### Request {idx}")
    st.write(f"**You:** {item['input']}")
    st.write(f"**Assistant:** {item['response_message']}")
    st.write(f"**Intent:** `{item['intent']}` | **Status:** `{item['status']}`")
    with st.expander("Structured Data"):
        st.json(item["data"])
