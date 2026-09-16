# Financial Research Tool

A Retrieval-Augmented Generation (RAG) application that lets users provide article URLs and ask questions based on the content of those articles.

The application loads webpage content, validates it, splits it into smaller chunks, creates semantic embeddings, stores them in a Chroma vector database, retrieves the most relevant chunks for a user question, and sends that context to a Groq-hosted LLM to generate a grounded answer with sources.

## Features

- Accepts up to three article URLs
- Loads webpage content using `WebBaseLoader`
- Detects common blocked/error pages before indexing
- Splits documents with `RecursiveCharacterTextSplitter`
- Creates embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Stores and searches vectors using Chroma
- Retrieves the most relevant chunks for each question
- Uses a Groq-hosted LLM to generate answers
- Displays source URLs used for retrieval
- Streamlit-based user interface
- Optional debug output for loaded content, chunks, retrieval, and Chroma storage

## Architecture

```text
                    INGESTION PIPELINE

Article URLs
     |
     v
WebBaseLoader
     |
     v
Page Validation
     |
     v
LangChain Documents
     |
     v
RecursiveCharacterTextSplitter
     |
     v
Text Chunks
     |
     v
Hugging Face Embeddings
     |
     v
Chroma Vector Database


                      QUERY PIPELINE

User Question
     |
     v
Chroma Retriever
     |
     v
Semantic Similarity Search
     |
     v
Relevant Chunks
     |
     v
Build Context
     |
     v
ChatPromptTemplate
     |
     v
Groq LLM
     |
     v
Answer + Sources
     |
     v
Streamlit UI
```

## Project Structure

```text
project/
├── main.py
├── rag.py
├── requirements.txt
├── README.md
├── .env
└── resources/
    └── vectorstore/
```

`main.py` contains the Streamlit user interface and controls the application flow.

`rag.py` contains the RAG pipeline: webpage loading, validation, chunking, embeddings, Chroma storage, retrieval, prompt construction, LLM invocation, and source extraction.

## Requirements

- Python 3.10 or newer
- A Groq API key
- Internet access for loading webpages and calling the Groq API

## Installation

Clone the repository:

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

Create and activate a virtual environment.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
USER_AGENT=FinancialResearchRAG/1.0 (your-email@example.com)
```

Do not commit your `.env` file to GitHub.

The `USER_AGENT` is used when requesting webpages and should identify your application when a website requires it.

## Run the Application

Start Streamlit with:

```bash
python -m streamlit run main.py
```

Open the local Streamlit URL shown in the terminal.

Then:

1. Enter one or more article URLs.
2. Click **Process URLs**.
3. Wait until the vector database is ready.
4. Enter a question about the processed articles.
5. Click **Ask**.
6. Review the generated answer and displayed sources.

## How the RAG Pipeline Works

### 1. Load and validate webpages

The application uses `WebBaseLoader` to retrieve article content. HTTP headers include a configurable User-Agent.

Before indexing, the extracted text is checked for very short responses and common blocked-page messages such as access-denied, CAPTCHA, or robot-policy responses.

### 2. Split documents

Valid documents are split using `RecursiveCharacterTextSplitter`.

Current configuration:

```python
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
```

This creates smaller overlapping text chunks that are more suitable for semantic retrieval.

### 3. Create embeddings

The project uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Each text chunk is converted into a vector representation of its semantic meaning.

### 4. Store vectors in Chroma

The chunks, embeddings, and source metadata are stored in a persistent Chroma collection under:

```text
resources/vectorstore/
```

Whenever URLs are processed, the existing collection is reset and rebuilt using the newly supplied sources.

### 5. Retrieve relevant chunks

When the user asks a question, Chroma performs semantic similarity search.

The current configuration retrieves up to:

```python
RETRIEVAL_K = 6
```

relevant chunks.

### 6. Build the LLM context

The retrieved chunks are combined into a context containing each chunk's source URL and content.

That context, together with the user's question, is formatted using `ChatPromptTemplate`.

### 7. Generate the answer

The application sends the formatted messages to a Groq-hosted LLM.

The prompt instructs the model to answer only from retrieved context, preserve important numerical values and dates, avoid inventing information, and say that it does not know when the answer cannot be determined from the supplied sources.

### 8. Display sources

The source metadata from retrieved chunks is collected, duplicates are removed, and the URLs are displayed below the answer.

## Debugging

The backend currently uses:

```python
DEBUG_MODE = True
```

This prints useful diagnostic information such as loaded webpage text, sample chunks, the number of stored Chroma records, and retrieved documents with their source URLs.

After development and testing, you can change it to:

```python
DEBUG_MODE = False
```

to reduce terminal output.

## Important Limitation

Some websites block automated requests, require authentication, use CAPTCHA protection, or rely heavily on JavaScript rendering.

If a site blocks the loader, the project may not be able to process that URL using `WebBaseLoader`. The application includes validation to prevent common block/error pages from being stored in the vector database.

## Technologies Used

- Python
- Streamlit
- LangChain
- Hugging Face Sentence Transformers
- ChromaDB
- Groq
- BeautifulSoup

## Security

Never commit API keys or secrets to GitHub.

A recommended `.gitignore` should include:

```gitignore
.env
.venv/
__pycache__/
.idea/
resources/vectorstore/
```

If an API key has ever been exposed publicly, revoke it and create a new one.

## Future Improvements

Possible enhancements include PDF and CSV support, multiple document collections, metadata filtering, hybrid search, reranking, chat history, authentication, evaluation datasets, and more precise source citation.

## License

Add a license of your choice before publishing if you want others to reuse or modify the project.
