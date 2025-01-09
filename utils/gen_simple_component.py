import os
import tempfile

import streamlit.components.v1 as components


# https://appcreatecomponent-ngm4rrw7ryvtzb6nigbbmw.streamlit.app/
def gen_simple_component(name, template='', script=''):
	def html():
		return f"""
						<!DOCTYPE html>
						<html lang="en">
								<head>
										<meta charset="UTF-8" />
										<title>{name}</title>
										<script>
												function sendMessageToStreamlitClient(type, data) {{
														const outData = Object.assign({{
																isStreamlitMessage: true,
																type: type,
														}}, data);
														window.parent.postMessage(outData, "*");
												}}

												const Streamlit = {{
														setComponentReady: function() {{
																sendMessageToStreamlitClient("streamlit:componentReady", {{apiVersion: 1}});
														}},
														setFrameHeight: function(height) {{
																sendMessageToStreamlitClient("streamlit:setFrameHeight", {{height: height}});
														}},
														setComponentValue: function(value) {{
																sendMessageToStreamlitClient("streamlit:setComponentValue", {{value: value}});
														}},
														RENDER_EVENT: "streamlit:render",
														events: {{
																addEventListener: function(type, callback) {{
																		window.addEventListener("message", function(event) {{
																				if (event.data.type === type) {{
																						event.detail = event.data
																						callback(event);
																				}}
																		}});
																}}
														}}
												}}
										</script>

								</head>
						<body>
						{template}
						</body>
						<script>
								{script}
						</script>
						</html>
				"""

	dir = f'{tempfile.gettempdir()}/{name}'
	fname = f'{dir}/index.html'

	if not os.path.isdir(dir):
		os.mkdir(dir)

	with open(fname, 'w') as f:
		f.write(html())

	func = components.declare_component(name, path=str(dir))

	def f(**params):
		component_value = func(**params)
		return component_value

	return f
