import csv
import json
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event, Thread

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.connector import connect
from snowflake.core import Root

from utils.system_prompts import (
	COACH_SYSTEM_PROMPT,
	KEYWORD_EXTRACTOR_SYSTEM_PROMPT,
	KEYWORD_SELECTOR_SYSTEM_PROMPT,
	KNOWLEDGE_BASE_TRANSFORM_PROMPT,
)

MODEL_NAME = 'mistral-large2'
LOG_TOKENS = False


class SnowflakeConnector:
	# ----------------
	# INITIALIZATION
	# ----------------
	# https://docs.snowflake.com/en/user-guide/key-pair-auth
	def _load_private_key(self, private_key_str):
		try:
			private_key = serialization.load_pem_private_key(
				private_key_str.encode(), password=None, backend=default_backend()
			)
			return private_key.private_bytes(
				encoding=serialization.Encoding.DER,
				format=serialization.PrivateFormat.PKCS8,
				encryption_algorithm=serialization.NoEncryption(),
			)

		except ValueError as e:
			raise ValueError(
				'Failed to load private key. Ensure it is in the correct PEM format.'
			) from e

	def __init__(self, streamlit_secrets):
		self.connection = connect(
			account=streamlit_secrets['snowflake']['account'],
			user=streamlit_secrets['snowflake']['user'],
			private_key=self._load_private_key(streamlit_secrets['snowflake']['private_key']),
			warehouse=streamlit_secrets['snowflake']['warehouse'],
			database=streamlit_secrets['snowflake']['database'],
			schema=streamlit_secrets['snowflake']['schema'],
		)

		self.root = Root(self.connection)

	# ----------------
	# UTILS
	# ----------------

	def _clean_prompt(self, prompt):
		prompt = prompt.replace("'", "\\'")
		return prompt

	def _generate_chat_history(self, chat_history):
		chat_history_str = ''

		for message in chat_history:
			role = message['role']
			content = self._clean_prompt(message['content'])
			chat_history_str += f"{{ 'role': '{role}', 'content': '{content}' }},"

		return chat_history_str

	def _do_simple_cortex_query(self, system_prompt, prompt):
		cursor = self.connection.cursor()

		cmd = f"""
		SELECT SNOWFLAKE.CORTEX.COMPLETE(
			'{MODEL_NAME}',
			[
				{{ 'role': 'system', 'content': '{self._clean_prompt(system_prompt)}' }},
				{{ 'role': 'user', 'content': '{self._clean_prompt(prompt)}' }}
			], 
			{{
				'temperature': 0
			}}
		) as response;
		"""

		cursor.execute(cmd)

		response = cursor.fetchall()[0][0]
		result = json.loads(response)

		cursor.close()
		return result

	def _log_token_usage(self, result):
		if LOG_TOKENS:
			usage = result['usage']
			for key in usage:
				print(f'{key}: {usage[key]}')

	def _safe_return_cortex_response(self, response):
		try:
			return response['choices'][0]['messages']
		except KeyError:
			print('Error: Cortex response does not contain expected data.')
			print(response)
			return ''

	# ----------------
	# STREAMLIT COACH
	# ----------------

	def generate_coach_prompt(
		self,
		video_tags,
		video_transcript,
		user_timestamp,
		# external_knowledge_base,
		user_question,
	):
		video_tags_str = json.dumps(video_tags)
		video_transcript_str = json.dumps(video_transcript)
		# external_knowledge_base_str = json.dumps(external_knowledge_base)

		coach_prompt = f"""
		<video-tags>{video_tags_str}</video-tags>
		<video-transcript>{video_transcript_str}</video-transcript>
		<user-timestamp>{user_timestamp}</user-timestamp>
		<user-question>{user_question}</user-question>
		"""

		# coach_prompt = f"""
		# <video-tags>{video_tags_str}</video-tags>
		# <video-transcript>{video_transcript_str}</video-transcript>
		# <user-timestamp>{user_timestamp}</user-timestamp>
		# <external-knowledge-base>{external_knowledge_base_str}</external-knowledge-base>
		# <user-question>{user_question}</user-question>
		# """

		return self._clean_prompt(coach_prompt)

	def query_cortex_chat(self, prompt, chat_history):
		cursor = self.connection.cursor()

		# Limit chat history to the last 10 messages
		chat_history = chat_history[-10:]

		# Build query for LLM
		# Getting the chat history into the prompt was all kinds of hard.
		# We should be using bind variables but there seems to be no way to get
		# a list of dictionaries into a bind variable without errors. Provide the
		# entire list and you get an error about the "replace method" not found on the dict object.
		# give it a JSON dumps and it gets mad about the param being a VARCHAR not and ARRAY.
		# If you try to json dump right into the query the double quotes cause syntax errors.
		# So we're just going to build the query string manually with a helper function.
		cmd = f"""
			SELECT SNOWFLAKE.CORTEX.COMPLETE(
				'{MODEL_NAME}',
				[
					{{ 'role': 'system', 'content': '{self._clean_prompt(COACH_SYSTEM_PROMPT)}' }},
					{self._generate_chat_history(chat_history)}
					{{ 'role': 'user', 'content': '{prompt}' }}
				], 
				{{
					'temperature': 0
				}}
			) as response;
		"""

		cursor.execute(cmd)

		response = cursor.fetchall()[0][0]
		result = json.loads(response)
		self._log_token_usage(result)

		cursor.close()
		return self._safe_return_cortex_response(result)

	# ----------------
	# KNOWLEDGE BASE
	# ----------------
	def get_cortex_keywords_from_transcript(self, transcript: str):
		result = self._do_simple_cortex_query(KEYWORD_EXTRACTOR_SYSTEM_PROMPT, transcript)
		self._log_token_usage(result)

		return self._safe_return_cortex_response(result)

	def tag_page_with_cortex(self, available_tags: list, page_summary: str):
		prompt = f"""
			<available-keywords>
			{','.join(available_tags)}
			</available-keywords>

			<wikipedia-summary>
			{page_summary}
			</wikipedia-summary>
		"""
		result = self._do_simple_cortex_query(KEYWORD_SELECTOR_SYSTEM_PROMPT, prompt)
		self._log_token_usage(result)

		return self._safe_return_cortex_response(result)

	def write_knowledge_base_csv(self, knowledge_base_entries: list, output_file_path: str):
		csv_row_queue = Queue()
		stop_write_request = Event()
		csv_file = open(output_file_path, 'w', newline='')  # noqa: SIM115

		# Clear the CSV file before writing to it
		csv_file.truncate(0)

		writer = csv.DictWriter(
			csv_file,
			fieldnames=['SOURCE', 'SOURCE_ID', 'CHUNK_TEXT', 'TAGS', 'REFERENCE_URL'],
		)
		writer.writeheader()

		def write_csv():
			while True:
				if not stop_write_request.is_set():
					row = csv_row_queue.get()
					print(
						f'Writing transformed data to {output_file_path} with reference URL: {row["REFERENCE_URL"]}'
					)
					writer.writerow(row)

				else:
					print('Queue is empty, ending write loop.')
					break

		csv_writer_thread = Thread(target=write_csv)
		csv_writer_thread.daemon = True
		csv_writer_thread.start()

		with ThreadPoolExecutor(max_workers=10) as executor:
			for index, entry in enumerate(knowledge_base_entries):
				executor.submit(
					self.prepare_kb_entry,
					csv_row_queue,
					entry,
					f'Processing entry {index + 1} of {len(knowledge_base_entries)}',
				)

		stop_write_request.set()
		csv_writer_thread.join()
		csv_file.close()

		print('Data writing complete.')

	def prepare_kb_entry(self, queue: Queue, knowledge_base_entry: dict, hello_log: str):
		print(hello_log)

		transformed_chunk_text = knowledge_base_entry['CHUNK_TEXT']

		if knowledge_base_entry.get('prompt'):
			prompt = (
				knowledge_base_entry['prompt']
				+ ' <original-text>'
				+ knowledge_base_entry['CHUNK_TEXT']
				+ '</original-text>'
			)
			# print(f'Generated prompt: {prompt}')

			result = self._do_simple_cortex_query(KNOWLEDGE_BASE_TRANSFORM_PROMPT, prompt)
			transformed_chunk_text = result['choices'][0]['messages']
			# print(f'Transformed CHUNK_TEXT: {transformed_chunk_text}')

		transformed_entry = {
			'SOURCE': knowledge_base_entry['SOURCE'],
			'SOURCE_ID': knowledge_base_entry['SOURCE_ID'],
			'CHUNK_TEXT': transformed_chunk_text,
			'TAGS': knowledge_base_entry['TAGS'],
			'REFERENCE_URL': knowledge_base_entry['REFERENCE_URL'],
		}

		# print(f"\nProcessed entry: {knowledge_base_entry['SOURCE_ID']}")
		# print(f"Processed CHUNK_TEXT: {transformed_entry['CHUNK_TEXT'][:120]}...")
		# print(f"Tags: {transformed_entry['TAGS']}")
		# print(f"Processed Reference URL: {transformed_entry['REFERENCE_URL']}")

		queue.put(transformed_entry)
