import time

import streamlit as st

COACH_RUNNING_LABEL = 'Coach is thinking...'
COACH_COMPLETE_LABEL = 'Coach is waiting for your next question...'
MESSAGES_PLACEHOLDER = (
	'**Ask Coach anything you want about the video or what you learned watching it.**'
)
PROMPT_PLACEHOLDER = 'Ask Coach...'


def get_llm_response(prompt):
	# Sleep for 2 seconds to simulate API call
	time.sleep(2)
	response = f'This is where the LLM response would go for: {prompt}'

	# Add assistant response to chat history
	st.session_state.messages.append({'role': 'assistant', 'content': response})


def side_col():
	# Initialize chat history in session state if it doesn't exist
	if 'messages' not in st.session_state:
		st.session_state.messages = []

	status = st.status(COACH_COMPLETE_LABEL, state='complete', expanded=False)

	# Display chat history
	# Create a container with 100% height and scrollable contents
	# height is managed with custom styles in lib/styles.py
	with st.container(key='chat-container', height=100):
		if len(st.session_state.messages) == 0:
			st.write(MESSAGES_PLACEHOLDER)

		for message in st.session_state.messages:
			with st.chat_message(message['role']):
				st.markdown(message['content'])

	# Chat input
	prompt = st.chat_input(PROMPT_PLACEHOLDER)

	st.write('')  # Add a small amount of padding

	if prompt:
		status.update(label=COACH_RUNNING_LABEL, state='running', expanded=False)

		# Add user message to chat history
		st.session_state.messages.append({'role': 'user', 'content': prompt})

		get_llm_response(prompt)
		status.update(label=COACH_COMPLETE_LABEL, state='complete', expanded=False)

		st.rerun()
