import streamlit as st

from components.main_col import main_col
from components.side_col import side_col
from utils.snowflake import SnowflakeConnector
from utils.styles import init_styles
from utils.video_details import get_video_transcript

# Load secrets
page_title = st.secrets['app']['page_title']
page_icon = st.secrets['app']['page_icon']
layout = 'wide'


@st.cache_resource
def load_snowflake():
	return SnowflakeConnector(st.secrets)


# I would love to cache this result with st.cache_resource, but
# for some reason that causes the entire app to duplicate itself, then remove
# the original UI and then not load the video again. No idea why.
def load_video_details():
	return {
		'video_tags': st.secrets['mux']['video_tags'],
		'video_transcript': get_video_transcript(
			st.secrets['mux']['playback_id'],
			st.secrets['mux']['track_id'],
		),
	}


def main():
	# Set page configuration
	st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

	# Create Snowflake singleton to be used throughout the app
	snowflake = load_snowflake()

	# Load video details
	video_details = load_video_details()

	# Create two columns with 65/35 ratio
	main_col_container, side_col_container = st.columns([0.6, 0.3])

	# Initialize custom styles
	init_styles()

	# Main section
	with main_col_container:
		main_col()

	# Side section - Chat interface
	with side_col_container:
		side_col(snowflake, video_details)


if __name__ == '__main__':
	main()
