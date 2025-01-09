import json
from io import StringIO

import requests
import webvtt


def get_video_transcript(playback_id, track_id):
	url = f'https://stream.mux.com/{playback_id}/text/{track_id}.vtt'
	response = requests.get(url)
	response.raise_for_status()

	vtt_content = response.text
	vtt = webvtt.from_buffer(StringIO(vtt_content))

	transcript = json.dumps(
		[
			{
				'start': caption.start_in_seconds,
				'end': caption.end_in_seconds,
				'text': caption.text,
			}
			for caption in vtt.captions
		]
	)
	return transcript
