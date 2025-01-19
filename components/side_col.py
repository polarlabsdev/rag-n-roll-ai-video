import streamlit as st

COACH_RUNNING_LABEL = 'The professor is thinking...'
COACH_COMPLETE_LABEL = 'Professor Prompt is waiting for your next question.'
COACH_ERROR_LABEL = 'An error occurred. Please try again.'
MESSAGES_PLACEHOLDER = "**Ask Professor Prompt anything about what was said in the video. Specific questions get better answers. Keep in mind the professor can't see what you see, it just has a transcript.**"
PROMPT_PLACEHOLDER = 'Pause the video and ask Professor Prompt something...'


def update_status(status_widget, new_status, new_state):
	st.session_state.status = new_status
	st.session_state.state = new_state
	status_widget.update(label=new_status, state=new_state, expanded=False)


def side_col(snowflake, video_details):
	# Initialize chat history in session state if it doesn't exist
	if 'messages' not in st.session_state:
		st.session_state.messages = []

	# Initialize status and state in session state if they don't exist
	if 'status' not in st.session_state:
		st.session_state.status = COACH_COMPLETE_LABEL
	if 'state' not in st.session_state:
		st.session_state.state = 'complete'

	# Display chat history
	# Create a container with 100% height and scrollable contents
	# height is managed with custom styles in lib/styles.py
	with st.container(key='chat-container', height=100):
		if len(st.session_state.messages) == 0:
			st.write(MESSAGES_PLACEHOLDER)

		for message in st.session_state.messages:
			with st.chat_message(message['role']):
				st.markdown(message['content'])

	# Display status widget
	status_widget = st.status(st.session_state.status, state=st.session_state.state, expanded=False)

	# Chat input
	prompt = st.chat_input(PROMPT_PLACEHOLDER)

	st.write('')  # Add a small amount of padding

	if prompt:
		update_status(status_widget, COACH_RUNNING_LABEL, 'running')

		try:
			formatted_prompt, reference_urls = snowflake.generate_coach_prompt(
				video_details['video_tags'],
				video_details['video_transcript'],
				st.session_state.mux_player_time,  # This comes from the main_col.py file
				prompt,
				st.session_state.messages,
			)

			response = response = snowflake.query_cortex_chat(formatted_prompt)

			response = (
				response + '\n\n**References:**\n\n' + '\n- '.join([''] + list(reference_urls))
			)

			# Add user message to chat history
			st.session_state.messages.append({'role': 'user', 'content': prompt})

			# Add assistant response to chat history
			st.session_state.messages.append({'role': 'assistant', 'content': response})

			update_status(status_widget, COACH_COMPLETE_LABEL, 'complete')

		except Exception as e:
			update_status(status_widget, COACH_ERROR_LABEL, 'error')
			raise e

		st.rerun()
