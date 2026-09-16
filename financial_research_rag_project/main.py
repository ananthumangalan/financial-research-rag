import streamlit as st

from rag import process_urls, generate_answer


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Financial extractor",
    page_icon="🏠",
    layout="wide"
)


st.title("Financial Research Tool")


# =========================================================
# STREAMLIT SESSION STATE
# =========================================================

if "urls_processed" not in st.session_state:
    st.session_state.urls_processed = False


# =========================================================
# URL INPUTS
# =========================================================

st.sidebar.header("Article URLs")


url1 = st.sidebar.text_input(
    "URL 1"
)

url2 = st.sidebar.text_input(
    "URL 2"
)

url3 = st.sidebar.text_input(
    "URL 3"
)


process_button = st.sidebar.button(
    "Process URLs"
)


# =========================================================
# STATUS AREA
# =========================================================

status_placeholder = st.empty()


# =========================================================
# PROCESS URLS
# =========================================================

if process_button:

    urls = [
        url.strip()
        for url in (url1, url2, url3)
        if url.strip()
    ]


    if not urls:

        status_placeholder.error(
            "Please enter at least one URL."
        )

        st.session_state.urls_processed = False


    else:

        try:

            st.session_state.urls_processed = False


            for status in process_urls(urls):

                status_placeholder.info(
                    status
                )


            st.session_state.urls_processed = True


            status_placeholder.success(
                "URLs processed successfully. "
                "You can now ask a question."
            )


        except Exception as e:

            st.session_state.urls_processed = False


            status_placeholder.error(
                f"URL processing failed:\n\n{e}"
            )


# =========================================================
# QUESTION FORM
# =========================================================

st.subheader("Ask a Question")


with st.form("question_form"):

    query = st.text_input(
        "Question",
        placeholder=(
            "Ask something about the "
            "processed articles..."
        )
    )


    ask_button = st.form_submit_button(
        "Ask"
    )


# =========================================================
# GENERATE ANSWER
# =========================================================

if ask_button:

    if not query.strip():

        st.warning(
            "Please enter a question."
        )


    elif not st.session_state.urls_processed:

        st.warning(
            "Please process the URLs first."
        )


    else:

        try:

            with st.spinner(
                "Searching the articles..."
            ):

                answer, sources = generate_answer(
                    query.strip()
                )


            st.header("Answer")

            st.write(
                answer
            )


            if sources:

                st.subheader("Sources")


                for source in sources.split("\n"):

                    if source.strip():

                        st.markdown(
                            f"- {source}"
                        )


        except Exception as e:

            st.error(
                f"Answer generation failed:\n\n{e}"
            )