import streamlit as st


# Custom Style Summary:
# - Set the max-width of the main block container to 1600px and center it to give
#   the app a consistent width and keep it centered on larger screens
# - Don't show the link icon on headers since this is a web app and not a document,
#   no need for intrapage links
# - Set the max-height of the chat container to 68vh to give it a fixed height
#   getting the chat to move up from the bottom in a clean way in streamlit is tricky
#   so we rely on regular scrolling. This css overrides the height set on the container
#   and swaps for auto height with a max height. This allows the box to grow with the
#   content to a certain point and then scroll up from there.
# - For the container that holds the video title and description, we fix a couple things:
# 	- Make the container a regular block element. This is a classic CSS mistake to make things
# 	  flexbox columns when you don't need to and flex starts adding extra space and things
#   - Remove the strange negative margin on the bottom of the h2 container
#   - adjust the padding on the h2 so it doesn't have extra space on top
#     (and fit things a little tighter on the bottom)
def init_styles():
	st.markdown(
		"""
    <style>
      .stMainBlockContainer {
        box-sizing: border-box;
				max-width: 100rem;
				margin: 0 auto;
			}
		
      .stHeading [data-testid="stHeadingWithActionElements"] {
          cursor: default !important;
          pointer-events: none;
      }
			
			[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-chat-container) {
        height: auto !important;
        max-height: 68vh !important;
			}
			
			.st-key-video-info {
				display: block;
			}
			
			.st-key-video-info .stHeading [data-testid="stMarkdownContainer"] {
        margin-bottom: 0;
			}
			
			.st-key-video-info .stHeading [data-testid="stMarkdownContainer"] h2 {
        padding: 0 0 0.65rem 0;
			}
    </style>
    """,
		unsafe_allow_html=True,
	)
