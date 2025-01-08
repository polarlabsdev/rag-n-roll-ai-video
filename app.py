import streamlit as st

from components.main_col import main_col
from components.side_col import side_col
from utils.styles import init_styles

# Load secrets
page_title = st.secrets['app']['page_title']
page_icon = st.secrets['app']['page_icon']
layout = 'wide'


def main():
	# Set page configuration
	st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

	# Create two columns with 65/35 ratio
	main_col_container, side_col_container = st.columns([0.6, 0.3])

	# Initialize custom styles
	init_styles()

	# Main section
	with main_col_container:
		main_col()

	# Side section - Chat interface
	with side_col_container:
		side_col()


if __name__ == '__main__':
	main()
