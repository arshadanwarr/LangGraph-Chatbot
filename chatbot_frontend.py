import streamlit as st
from chatbot_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# -----------------
# UTILITY FUNCTIONS
# -----------------

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_labels'][thread_id] = f"Chat {len(st.session_state['chat_threads'])}"

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Safely return messages if available, otherwise []
    return state.values.get('messages', [])


def export_chat_as_txt(chat_history):
    txt_content = ""
    for msg in chat_history:
        role = msg["role"].capitalize()
        content = msg["content"]
        txt_content += f"{role}: {content}\n\n"
    return txt_content



# -----------------
# SESSION SETUP
# -----------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
     st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_labels' not in st.session_state:
    st.session_state['thread_labels'] = {}

# Ensure current thread is added
add_thread(st.session_state['thread_id'])

# Ensure all threads have labels
for idx, tid in enumerate(st.session_state['chat_threads'], start=1):
    if tid not in st.session_state['thread_labels']:
        st.session_state['thread_labels'][tid] = f"Chat {idx}"


# -----------------
# SIDE BAR UI
# -----------------

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    label = st.session_state['thread_labels'].get(thread_id, str(thread_id))
    if st.sidebar.button(label):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# -----------------
# MAIN UI
# -----------------

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

if st.session_state['message_history']:
    txt_file = export_chat_as_txt(st.session_state['message_history'])
    st.download_button(
        label="📄 Download Chat (.txt)",
        data=txt_file,
        file_name="chat_history.txt",
        mime="text/plain"
    )

user_input = st.chat_input('Type here')

if user_input:
    # Add user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Assistant response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})