import hashlib
import json
import os
import pathlib
import sys
from pprint import pprint

import toml
import wikipedia

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

from utils.snowflake import SnowflakeConnector  # noqa: E402
from utils.video_details import get_video_transcript  # noqa: E402


def load_secrets(file_path):
	with open(file_path) as f:
		return toml.load(f)


def get_transcript(secrets):
	playback_id = secrets['mux']['playback_id']
	track_id = secrets['mux']['track_id']
	return json.loads(get_video_transcript(playback_id, track_id))


def search_wikipedia_and_populate_dict(snowflake, keywords):
	pages_dict = {}
	failed_pages = []
	results_per_search = 5

	for keyword in keywords:
		print(f'Searching Wikipedia for keyword: {keyword}')
		search_results = [
			result
			for result in wikipedia.search(keyword, results=results_per_search, suggestion=False)
			if '(disambiguation)' not in result
		]
		print(f'Found {len(search_results)} results for keyword: {keyword}: {search_results}')

		for title in search_results:
			print(f'Processing result: {title}')
			try:
				wiki_page = wikipedia.page(title, auto_suggest=False)
				wiki_page_summary = wikipedia.summary(title, auto_suggest=False)
			except wikipedia.exceptions.DisambiguationError:
				print(f'DisambiguationError for result: {title}')
				failed_pages.append({'title': title, 'error': 'DisambiguationError'})
				continue
			except wikipedia.exceptions.PageError:
				print(f'PageError for result: {title}')
				failed_pages.append({'title': title, 'error': 'PageError'})
				continue

			page_content = f'{wiki_page.title}\n{wiki_page.content}'
			page_hash = hashlib.sha256(page_content.encode()).hexdigest()

			print('generating page tags...')
			page_tags_str = snowflake.tag_page_with_cortex(keywords, wiki_page_summary)
			page_tags = [tag.strip() for tag in page_tags_str.split(',')]
			print('page tagged with:', page_tags)

			try:
				pages_dict[page_hash] = {
					'page_content': page_content,
					'page_summary': wiki_page_summary,
					'images': wiki_page.images,
					'page_url': wiki_page.url,
					'page_tags': page_tags,
				}
			except Exception as e:
				print(f'Unexpected error building dict for result: {title}')
				failed_pages.append({'title': title, 'error': e.__str__()})
				continue

			print(f'Added page {wiki_page.title} to dictionary with hash: {page_hash}')

	return pages_dict, failed_pages


def convert_pages_to_kb_format(pages_dict):
	knowledge_base_data = []
	source = 'Wikipedia'
	chunk_size = 200
	overlap = 10

	for page_hash, page_info in pages_dict.items():
		page_content = page_info['page_content']
		page_summary = page_info['page_summary']
		images = page_info['images']
		page_url = page_info['page_url']
		page_tags = page_info['page_tags']

		# Chunk page content into chunks of `chunk_size` words each with `overlap`
		words = page_content.split()
		chunks = []
		for i in range(0, len(words), chunk_size - overlap):
			chunk = ' '.join(words[i : i + chunk_size])
			chunks.append(chunk)

		for chunk in chunks:
			knowledge_base_data.append(
				{
					'SOURCE': source,
					'SOURCE_ID': page_hash,
					'CHUNK_TEXT': chunk,
					'TAGS': page_tags,
					'REFERENCE_URL': page_url,
					'prompt': None,  # set this if you want to enhance the chunks, but get a tea cause it's gunna be awhile
				}
			)

		# Add entries for images
		for image_url in images:
			knowledge_base_data.append(
				{
					'SOURCE': source,
					'SOURCE_ID': page_hash,
					'CHUNK_TEXT': image_url,
					'TAGS': page_tags,
					'REFERENCE_URL': page_url,
					'prompt': f'Provide the best possible description of what this image is based on the filename and provided context. Context: {page_summary}',
				}
			)

	return knowledge_base_data


def main():
	# -------------------------
	# INITIAL SETUP
	# -------------------------
	print('Loading secrets...')
	secrets_file_path = os.path.join(root_path, '.streamlit', 'secrets.toml')
	secrets = load_secrets(secrets_file_path)
	print('Secrets loaded.')

	print('Initializing Snowflake connector...')
	snowflake = SnowflakeConnector(secrets)
	print('Snowflake connector initialized.')

	print('Setting Wikipedia rate limiting...')
	wikipedia.set_rate_limiting(True)
	print('Wikipedia rate limiting set.')

	# -------------------------
	# GET TAGS FROM TRANSCRIPT
	# -------------------------
	if 'video_tags' in secrets['mux']:
		print('Video tags found in secrets.')
		keywords = secrets['mux']['video_tags']
	else:
		print('Getting transcript...')
		transcript = get_transcript(secrets)
		print('Transcript obtained.')

		print('Extracting keywords from transcript...')
		keywords = snowflake.get_cortex_keywords_from_transcript(transcript).split(',')
		print('Keywords extracted:', keywords)

	# -------------------------
	# GET WIKIPEDIA PAGES
	# -------------------------
	wiki_data_file = pathlib.Path(root_path, 'generated_files/wiki_data.json')

	if wiki_data_file.exists():
		print('wiki_data.json file exists. Loading data from file...')
		with open(wiki_data_file) as f:
			pages_dict = json.load(f)

		print('Data loaded from wiki_data.json.')

	else:
		failed_pages = []

		print(
			'wiki_data.json file does not exist. Searching Wikipedia and populating dictionary...'
		)
		pages_dict, failed_pages = search_wikipedia_and_populate_dict(snowflake, keywords)
		print('Dictionary populated with Wikipedia pages.')

		print('Saving pages_dict to wiki_data.json...')
		os.makedirs(wiki_data_file.parent, exist_ok=True)

		with open(wiki_data_file, 'w') as f:
			json.dump(pages_dict, f)

		print('pages_dict saved to wiki_data.json.')

		print('Failed pages')
		pprint(failed_pages)

	# -------------------------
	# GENERATE CSVS FOR SNOWFLAKE
	# -------------------------
	output_file_path = os.path.join(root_path, 'generated_files', 'knowledge_base.csv')

	if pathlib.Path(output_file_path).exists():
		print(f'{output_file_path} already exists. Skipping CSV generation.')

	else:
		print('Writing CSV to be inserted to Snowflake...')
		knowledge_base_entries = convert_pages_to_kb_format(pages_dict)
		snowflake.write_knowledge_base_csv(knowledge_base_entries, output_file_path)


if __name__ == '__main__':
	main()
