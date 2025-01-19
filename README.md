# 🎓 Professor Prompt - Your Interactive Video Learning Assistant

## Snowflake Rag 'n' Roll Hackathon Submission

Turn any educational video into an interactive learning experience with Professor Prompt, your AI teaching assistant that recreates the classroom experience by allowing you to ask questions in real-time.

### 🛠️ Technical Stack

- Streamlit
- Snowflake
- Terraform
- Mistral (LLM)
- Snowflake Cortex Search
- Python Scripting

### 👥 Team

[Polar Labs Development Inc](https://polarlabs.ca)

### 🌟 Key Features

- **Interactive Learning**: Pause anytime to ask questions about the content
- **Contextual Understanding**: Professor Prompt understands where you are in the video
- **Knowledge Enhancement**: Automatically enriched with relevant Wikipedia knowledge
- **Classroom Experience**: Natural dialogue with an AI teaching assistant
- **Fully Reproducible**: Built with Terraform and idempotency in mind, this entire project can be regenerated in any account with any video

### 🏗️ Technical Architecture

#### Frontend (Streamlit)

The frontend is built with Streamlit and consists of two main columns:

1. **Main Column (Video Player)**

   - Contains a Mux video player implementation
   - Uses custom JavaScript injection through Streamlit components to bypass iframe limitations
   - Tracks video timestamp and pause state
   - Displays video title and description
   - Implements cookie-based user warnings about pausing requirement

2. **Side Column (Chat Interface)**
   - Provides an interactive chat interface with Professor Prompt
   - Maintains chat history in session state
   - Displays status indicators for Professor Prompt's responses
   - Handles error states and loading states
   - Shows references for knowledge sources

The components communicate through:

- Session state for video timestamp tracking
- Snowflake connector class for all database and LLM operations
- Custom prompts that combine video context, transcript, and external knowledge

When a user asks a question:

1. Video timestamp is captured
2. Question is enhanced via Snowflake Cortex in preparation for Cortex Search
3. Relevant knowledge is retrieved from Cortex Search
4. Context is assembled including video tags, transcript, and external knowledge
5. Response is generated using mistral-large2
6. Answer is displayed with relevant references

NOTE: We wanted to use a fine-tuned model, but ran into issues where when we fine-tuned
      a model in Snowflake it was incredibly slow (up to 8min to answer 1 question). Though
      the quality of the answers was greatly improved, due to the time contraints for this submission
      we defaulted back to mistral-large2 and focused on prompt engineering.

#### Snowflake Infrastructure (Terraform)

The infrastructure is managed through Terraform and creates all necessary Snowflake resources:

1. **Core Infrastructure**

   - Dedicated warehouses for RAG operations and Cortex Search
   - Custom database and schema for the application
   - Service user with RSA key authentication
   - Custom role with precise permissions

2. **Knowledge Base Components**

   - Knowledge base table for storing document chunks
   - CSV file format for data ingestion
   - Internal stage for file uploads
   - Cortex Search service for semantic search

3. **Workflow**
   The terraform apply process:

   - Creates all Snowflake resources
   - Triggers a local Python script to generate knowledge base
   - Uploads the generated CSV to Snowflake stage
   - Loads data into the knowledge base table
   - Configures Cortex Search on the loaded data

4. **Security & Permissions**

   - All resources are owned by the custom role
   - Granular permissions for stage access and search service usage
   - Follows Snowflake best practices with SYSADMIN ownership

5. **State Management**
   - Resources are created idempotently
   - Includes cleanup commands for failed states
   - Manages dependencies between resources

The infrastructure can be completely recreated by running terraform apply with appropriate credentials in terraform.tfvars.

#### Knowledge Base Generation

The knowledge base generation process is automated through `scripts/populate_kb.py` and works in the following stages:

1. **Initial Setup & Tag Generation**

   - Loads configuration from secrets.toml
   - Initializes Snowflake connection
   - Either uses predefined video tags from secrets or:
     - Fetches video transcript from Mux using playback and track IDs
     - Uses Cortex to extract relevant keywords from transcript

2. **Wikipedia Content Retrieval**

   - Searches Wikipedia for each keyword
   - Filters out disambiguation pages
   - For each result:
     - Fetches page content and summary
     - Generates SHA256 hash as unique identifier
     - Uses Cortex to tag content with relevant video keywords
     - Saves page content, summary, images, and URL
   - Stores results in wiki_data.json as checkpoint

3. **Knowledge Base Processing**
   - Chunks content into 200-word segments with 10-word overlap
   - Processes images with contextual prompts
   - Uses thread pool for parallel processing
   - Implements queue system for CSV writing
   - Preserves original content while adding contextual enhancements

The system employs checkpoints (wiki_data.json, knowledge_base.csv) to prevent data loss during lengthy operations and uses threading to optimize performance when processing large volumes of Wikipedia content.

#### LLM Integration and Context Processing

The LLM integration leverages multiple stages of prompt engineering and context enhancement:

1. **Question Enhancement**

- Raw user questions are first processed through a query enhancement prompt
- This converts natural language questions into search-optimized terms
- Expands acronyms, adds technical terminology, and related concepts
- Improves RAG retrieval by broadening the semantic search space

2. **Context Assembly**
   The full context provided to Professor Prompt includes:

- Video metadata (tags for topic identification)
- External knowledge from RAG results
- Full video transcript
- Current video timestamp
- Original user question
- Limited chat history (last 4 messages)

3. **System Prompts**
   Multiple specialized system prompts handle different tasks:

- COACH_SYSTEM_PROMPT: Core teaching assistant personality and response guidelines
- QUERY_ENHANCER_SYSTEM_PROMPT: Converts questions to search terms
- KEYWORD_EXTRACTOR_SYSTEM_PROMPT: Pulls relevant terms from video transcripts
- KEYWORD_SELECTOR_SYSTEM_PROMPT: Matches knowledge base content to video topics
- KNOWLEDGE_BASE_TRANSFORM_PROMPT: Enhances RAG content with additional context

4. **Fine-Tuning (Not used in final submission)**

- Training data generated from simulated student interactions
- Questions crafted to match natural viewing patterns
- Each training example includes:
  - Timestamp context
  - RAG results
  - Expected response format
- Model fine-tuned to maintain educational tone and format

5. **Response Generation**
   The final Professor Prompt response:

- Uses system prompts and careful prompt engineering for consistent educational style
- Maintains context through limited chat history
- Automatically includes relevant knowledge base references
- Formats output in markdown for readability
- Focuses on content up to current video timestamp

### 🚀 Getting Started

#### Prerequisites

- A video uploaded to Mux
- A valid `.streamlit/secrets.toml` file and `terraform/terraform.tfvars`

#### Installation

1. **Install Poetry**:

   Follow the instructions on the [Poetry website](https://python-poetry.org/docs/#installation) to install Poetry for your operating system.

2. **Install the required dependencies**:

   ```sh
   poetry install
   ```

3. **Install Terraform**:

   Follow the instructions on the [Terraform website](https://learn.hashicorp.com/tutorials/terraform/install-cli) to install Terraform for your operating system.

4. **Initialize and apply Terraform**:

   ```sh
   cd terraform
   terraform init
   terraform apply
   ```

5. **Start the Streamlit application**:
   ```sh
   streamlit run app.py
   ```

Your interactive video learning assistant should now be up and running.

#### Fine-tuning a model

**Note:** This step is optional. Professor Prompt will work out of the box with mistral-large2, but a fine-tuned model may provide more consistent and reliable responses.

Due to time constraints during development, our fine-tuning notebook isn't as polished or reusable as our other components. However, you can use it as a starting point:

1. **Import the notebook**:

   - Open Snowflake's web interface
   - Navigate to Snowsight > Worksheets
   - Click "Create" > "Import Worksheet"
   - Select the `notebook_app.ipynb` file

2. **Customize the notebook**:
   The notebook will need modifications for your use case:

   - Adjust the training data generation prompts
   - Modify the system prompts if needed
   - Update the video transcript
   - Change any hardcoded values specific to your implementation

3. **Run the notebook**:
   - Execute cells in order
   - Review generated questions and responses
   - Adjust prompts if needed to get better quality training data
