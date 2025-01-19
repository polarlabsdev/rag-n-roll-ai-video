import streamlit as st

from utils.gen_simple_component import gen_simple_component


def main_col():
	# Load env vars
	mux_playback_id = st.secrets['mux']['playback_id']
	mux_video_title = st.secrets['mux']['video_title']
	mux_video_description = st.secrets['mux']['video_description']
	primary_color = st.get_option('theme.primaryColor')

	# -----------------------------------------
	# Mux Video player hacks below because streamlit makes it incredibly difficult to
	# use external JS libraries and custom HTML
	# -----------------------------------------

	# First create a div element with an id that we can target
	# we can't use the <mux-player> tag directly in the HTML because Streamlit sanitizes it
	mux_player_html = """
  <div id="mux-player"></div>
  """
	st.markdown(mux_player_html, unsafe_allow_html=True)

	# Video title and description
	# Put this in the middle because the generated iframe for the script below
	# takes up space because there is a default line-height on it that cannot be changed (easily)
	with st.container(border=True, key='video-info'):
		st.header(mux_video_title)
		st.write(mux_video_description)

	# We need to add the mux player script and HTML to the main page, not the component iframe.
	# If it's in an iframe then the player will be cut off on different screen sizes since
	# the iframe cannot automatically determine it's own height.
	# We generate the script tag and then the HTML in JS and attach both to the parent.
	# The mux script goes to the head and the mux player goes to the mux-player div we created above.
	# We check for the mux-player tag first to avoid recreating the player on hot reload.
	# Then we get even trickier. To get the current user timestamp there are exactly 0 ways.
	# I found a website deep in the streamlit forums that describe how to easily create a
	# bidirectional component so we can use Streamlit.setComponentValue to send the current time
	# from the player to a streamlit state variable. You can see it in utils/gen_simple_component.py
	script = f"""
		// Check for the presence of the SEEN_DISCLAIMER cookie
		function checkDisclaimerCookie() {{
			if (!document.cookie.split('; ').find(row => row.startsWith('SEEN_DISCLAIMER'))) {{
				// If the cookie does not exist, show the alert
				alertUser();
			}}
		}}

		function alertUser() {{
			alert("Note: You must pause the video to ask Professor Prompt questions. This is due to limitations with Streamlit adding custom HTML/JS like the video player. If you ask a question while the video is playing, nothing will happen. You won't see this warning again.");
			// Set the SEEN_DISCLAIMER cookie
			document.cookie = "SEEN_DISCLAIMER=true; path=/";
		}}

		// Run the check on script load
		checkDisclaimerCookie();

    function onRender(event) {{
      const parentDOM = window.parent.document;

			if (!parentDOM.querySelector('mux-player')) {{
				var head = parentDOM.getElementsByTagName('head')[0];
				var script = parentDOM.createElement('script');
				script.type = 'text/javascript';
				script.src = 'https://cdn.jsdelivr.net/npm/@mux/mux-player';
				head.appendChild(script);

				script.onload = function() {{
					const muxPlayer = parentDOM.createElement('mux-player');
					muxPlayer.setAttribute('playback-id', '{mux_playback_id}');
					muxPlayer.setAttribute('metadata-video-title', '{mux_video_title}');
					muxPlayer.setAttribute('accent-color', '{primary_color}');

					const muxPlayerDiv = parentDOM.getElementById('mux-player');
					muxPlayerDiv.appendChild(muxPlayer);

					muxPlayer.addEventListener("timeupdate", function (event) {{
						Streamlit.setComponentValue(event.target.currentTime);
					}});
				}}
			}}
    }}

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
    Streamlit.setComponentReady()
	"""

	mux_player = gen_simple_component('mux_player', script=script)
	value = mux_player(key='mux')
	st.session_state.mux_player_time = int(value) if value else 0
