import streamlit as st
from streamlit.components.v1 import html


def main_col():
	# Load env vars
	mux_playback_id = st.secrets['mux']['playback_id']
	mux_video_title = st.secrets['mux']['video_title']
	mux_video_description = st.secrets['mux']['video_description']
	primary_color = st.get_option('theme.primaryColor')

	# Mux Video player hacks below because streamlit makes it incredibly difficult to
	# use external JS libraries and custom HTML

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

	# Add the script to the main page, not the component iframe.
	# Then generate the player in JS and attach to the div element we created above.
	# We check for the mux-player tag first to avoid recreating the player on hot reload.
	mux_script_html = f"""
  <script>
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
      }}
    }}
  </script>
  """
	html(mux_script_html, height=0)
