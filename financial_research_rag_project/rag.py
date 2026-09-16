from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv
import os


# =========================================================
# LANGCHAIN IMPORTS
# =========================================================

# Webpage loader
from langchain_community.document_loaders import (
    WebBaseLoader,
)

# Text splitter
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

# Embeddings
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)

# Vector database
from langchain_chroma import Chroma

# LLM
from langchain_groq import ChatGroq

# Prompt
from langchain_core.prompts import (
    ChatPromptTemplate,
)


# =========================================================
# 1. PROJECT PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent


# =========================================================
# 2. LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv(
    BASE_DIR / ".env"
)


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


USER_AGENT = os.getenv(
    "USER_AGENT"
)


if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY is missing from .env"
    )


if not USER_AGENT:

    raise RuntimeError(
        "USER_AGENT is missing from .env.\n\n"
        "Example:\n"
        "USER_AGENT=RealEstateRAGBot/1.0 "
        "(your-email@example.com)"
    )


# =========================================================
# 3. SETTINGS
# =========================================================

CHUNK_SIZE = 1500

CHUNK_OVERLAP = 200

RETRIEVAL_K = 6


EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


COLLECTION_NAME = "real_estate"


VECTORSTORE_DIR = (
    BASE_DIR
    / "resources"
    / "vectorstore"
)


VECTORSTORE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Set True while debugging.
# Change to False after everything works.

DEBUG_MODE = True


# =========================================================
# 4. HTTP HEADERS
# =========================================================

HEADERS = {

    "User-Agent": USER_AGENT,

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "*/*;q=0.8"
    ),

    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
}


# =========================================================
# 5. BLOCK / ERROR PAGE DETECTION
# =========================================================

BLOCKED_PAGE_MARKERS = [

    "access denied",

    "you don't have permission to access",

    "please set a user-agent",

    "respect our robot policy",

    "forbidden",

    "request blocked",

    "captcha",

    "verify you are human",
]


# =========================================================
# 6. GLOBAL COMPONENTS
# =========================================================

llm: ChatGroq | None = None

vector_store: Chroma | None = None


# =========================================================
# 7. DEBUG FUNCTION
# =========================================================

def debug_print(title, value):

    if not DEBUG_MODE:
        return


    print("\n")
    print("=" * 70)

    print(title)

    print("=" * 70)

    print(value)

    print("=" * 70)


# =========================================================
# 8. INITIALIZE COMPONENTS
# =========================================================

def initialize_components():

    global llm
    global vector_store


    # -----------------------------------------------------
    # LLM
    # -----------------------------------------------------

    if llm is None:

        llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            max_tokens=700
        )


    # -----------------------------------------------------
    # EMBEDDING MODEL
    # -----------------------------------------------------

    if vector_store is None:

        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )


        # -------------------------------------------------
        # CHROMA VECTOR DATABASE
        # -------------------------------------------------

        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(
                VECTORSTORE_DIR
            )
        )


# =========================================================
# 9. CHECK IF PAGE CONTENT IS VALID
# =========================================================

def validate_page_text(
    text,
    url
):

    cleaned_text = (
        text
        .strip()
    )


    if len(cleaned_text) < 200:

        raise RuntimeError(
            f"The page returned too little text:\n"
            f"{url}\n\n"
            f"Only {len(cleaned_text)} characters "
            f"were extracted."
        )


    lower_text = (
        cleaned_text.lower()
    )


    for marker in BLOCKED_PAGE_MARKERS:

        if marker in lower_text:

            raise RuntimeError(
                "The website blocked the loader.\n\n"
                f"URL:\n{url}\n\n"
                f"Detected message:\n{marker}"
            )


# =========================================================
# 10. PROCESS URLS
# =========================================================

def process_urls(urls):

    """
    Ingestion pipeline:

    URL
      ↓
    WebBaseLoader
      ↓
    LangChain Documents
      ↓
    RecursiveCharacterTextSplitter
      ↓
    Chunks
      ↓
    HuggingFace embeddings
      ↓
    Chroma vector database
    """

    global vector_store


    # -----------------------------------------------------
    # INITIALIZE COMPONENTS
    # -----------------------------------------------------

    yield "Initializing RAG components..."

    initialize_components()


    # -----------------------------------------------------
    # RESET OLD COLLECTION
    # -----------------------------------------------------

    yield "Clearing old vector data..."

    vector_store.reset_collection()


    # -----------------------------------------------------
    # LOAD WEB PAGES
    # -----------------------------------------------------

    yield "Loading webpages..."

    loaded_documents = []

    successful_urls = []

    failed_urls = []


    for url in urls:

        try:

            yield (
                f"Loading: {url}"
            )


            loader = WebBaseLoader(

                web_paths=(url,),

                header_template=HEADERS,

                requests_kwargs={
                    "timeout": 30
                },

                raise_for_status=True,

                bs_get_text_kwargs={
                    "separator": "\n",
                    "strip": True
                }
            )


            documents = loader.load()


            if not documents:

                raise RuntimeError(
                    "Loader returned no documents."
                )


            # ---------------------------------------------
            # COMBINE TEXT FOR VALIDATION
            # ---------------------------------------------

            page_text = "\n".join(

                document.page_content

                for document in documents
            )


            validate_page_text(
                page_text,
                url
            )


            # ---------------------------------------------
            # ENSURE SOURCE METADATA EXISTS
            # ---------------------------------------------

            for document in documents:

                document.metadata[
                    "source"
                ] = url


            loaded_documents.extend(
                documents
            )


            successful_urls.append(
                url
            )


            debug_print(

                f"SUCCESSFULLY LOADED: {url}",

                (
                    f"Characters loaded: "
                    f"{len(page_text)}\n\n"
                    f"First 1000 characters:\n\n"
                    f"{page_text[:1000]}"
                )
            )


        except Exception as e:

            failed_urls.append(
                (
                    url,
                    str(e)
                )
            )


            debug_print(
                f"FAILED URL: {url}",
                str(e)
            )


            yield (
                f"Could not load URL: {url}"
            )


    # -----------------------------------------------------
    # CHECK IF AT LEAST ONE URL WORKED
    # -----------------------------------------------------

    if not loaded_documents:

        error_details = "\n\n".join(

            f"{url}\n{error}"

            for url, error in failed_urls
        )


        raise RuntimeError(
            "None of the supplied URLs could "
            "be loaded successfully.\n\n"
            f"{error_details}"
        )


    yield (
        f"Successfully loaded "
        f"{len(successful_urls)} URL(s)."
    )


    # -----------------------------------------------------
    # SPLIT DOCUMENTS
    # -----------------------------------------------------

    yield "Splitting webpage text into chunks..."


    splitter = (
        RecursiveCharacterTextSplitter(

            chunk_size=CHUNK_SIZE,

            chunk_overlap=CHUNK_OVERLAP,

            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )
    )


    chunks = splitter.split_documents(
        loaded_documents
    )


    if not chunks:

        raise RuntimeError(
            "The webpages loaded, but no "
            "text chunks were created."
        )


    yield (
        f"Created {len(chunks)} chunks."
    )


    # -----------------------------------------------------
    # DEBUG CHUNKS
    # -----------------------------------------------------

    if DEBUG_MODE:

        for index, chunk in enumerate(
            chunks[:5],
            start=1
        ):

            debug_print(

                f"CHUNK {index}",

                chunk.page_content[:1000]
            )


    # -----------------------------------------------------
    # UNIQUE CHROMA IDS
    # -----------------------------------------------------

    document_ids = [

        str(uuid4())

        for _ in chunks
    ]


    # -----------------------------------------------------
    # STORE IN VECTOR DATABASE
    # -----------------------------------------------------

    yield (
        "Creating embeddings and storing "
        "chunks in Chroma..."
    )


    vector_store.add_documents(

        documents=chunks,

        ids=document_ids
    )


    count = (
        vector_store
        ._collection
        .count()
    )


    debug_print(
        "CHROMA DATABASE",
        f"Documents stored: {count}"
    )


    yield (
        f"Vector database ready. "
        f"{count} chunks stored ✅"
    )


# =========================================================
# 11. GENERATE ANSWER
# =========================================================

def generate_answer(query):

    """
    Query pipeline:

    Question
      ↓
    Chroma retriever
      ↓
    Relevant chunks
      ↓
    Prompt
      ↓
    Groq LLM
      ↓
    Answer
    """

    global llm
    global vector_store


    # -----------------------------------------------------
    # INITIALIZE COMPONENTS
    # -----------------------------------------------------

    initialize_components()


    # -----------------------------------------------------
    # CHECK VECTOR DATABASE
    # -----------------------------------------------------

    count = (
        vector_store
        ._collection
        .count()
    )


    if count == 0:

        raise RuntimeError(
            "The vector database is empty. "
            "Process the URLs first."
        )


    # -----------------------------------------------------
    # CREATE RETRIEVER
    # -----------------------------------------------------

    retriever = (
        vector_store.as_retriever(

            search_kwargs={
                "k": RETRIEVAL_K
            }
        )
    )


    # -----------------------------------------------------
    # RETRIEVE DOCUMENTS
    # -----------------------------------------------------

    retrieved_documents = (
        retriever.invoke(
            query
        )
    )


    if not retrieved_documents:

        raise RuntimeError(
            "No relevant documents were retrieved."
        )


    # -----------------------------------------------------
    # DEBUG RETRIEVAL
    # -----------------------------------------------------

    if DEBUG_MODE:

        for index, document in enumerate(
            retrieved_documents,
            start=1
        ):

            source = (
                document.metadata.get(
                    "source",
                    "Unknown source"
                )
            )


            debug_print(

                f"RETRIEVED DOCUMENT {index}",

                (
                    f"SOURCE:\n{source}\n\n"
                    f"TEXT:\n"
                    f"{document.page_content}"
                )
            )


    # -----------------------------------------------------
    # BUILD CONTEXT MANUALLY
    # -----------------------------------------------------

    context_parts = []


    for index, document in enumerate(
        retrieved_documents,
        start=1
    ):

        source = (
            document.metadata.get(
                "source",
                "Unknown source"
            )
        )


        context_parts.append(

            f"""
DOCUMENT {index}

SOURCE:
{source}

CONTENT:
{document.page_content}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    # -----------------------------------------------------
    # PROMPT
    # -----------------------------------------------------

    prompt = (
        ChatPromptTemplate.from_messages(
            [

                (
                    "system",
                    """
You are a real-estate research assistant.

Answer the user's question using ONLY the
retrieved context supplied below.

Read the context carefully.

If the answer appears in the context,
provide a clear and accurate answer.

Preserve important numerical values,
percentages, dates, prices, and terminology
exactly as they appear in the context.

If the answer genuinely cannot be determined
from the context, respond:

"I do not know based on the supplied sources."

Do not invent information.

Retrieved context:

{context}
"""
                ),

                (
                    "human",
                    "{question}"
                )

            ]
        )
    )


    # -----------------------------------------------------
    # FORMAT PROMPT
    # -----------------------------------------------------

    messages = (
        prompt.format_messages(

            context=context,

            question=query
        )
    )


    # -----------------------------------------------------
    # CALL GROQ LLM
    # -----------------------------------------------------

    response = llm.invoke(
        messages
    )


    answer = response.content


    # -----------------------------------------------------
    # GET SOURCES
    # -----------------------------------------------------

    sources = set()


    for document in retrieved_documents:

        source = (
            document.metadata.get(
                "source"
            )
        )


        if source:

            sources.add(
                source
            )


    sources_text = "\n".join(
        sorted(sources)
    )


    return (
        answer,
        sources_text
    )