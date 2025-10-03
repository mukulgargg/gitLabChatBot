import os, streamlit as st
from app.api import RAG
from app.guards import is_safe

st.set_page_config(page_title="GitLab Handbook Chat", layout="centered")

st.title("GitLab Handbook & Direction Chatbot")
st.caption("Answers grounded in official GitLab Handbook and Product Direction pages.")

with st.sidebar:
    st.subheader("Settings")
    api = st.text_input("GEMINI_API_KEY", type="password", value=os.getenv("GEMINI_API_KEY",""))
    k = st.slider("Retriever k", 3, 10, 5)
    show_ctx = st.checkbox("Show retrieved chunks", value=False)
    st.markdown("[Project direction pages](https://about.gitlab.com/direction/)")
    st.markdown("[Handbook home](https://handbook.gitlab.com/handbook/)")

if "rag" not in st.session_state and api:
    os.environ["GEMINI_API_KEY"] = api
    st.session_state.rag = RAG(k=k)

if user_q := st.chat_input("Ask about GitLab processes, values, or product direction…"):
    st.chat_message("user").write(user_q)
    ok, msg = is_safe(user_q)
    if not ok:
        st.chat_message("assistant").warning(msg)
    else:
        if "rag" not in st.session_state:
            st.chat_message("assistant").error("Please set GEMINI_API_KEY in the sidebar.")
        else:
            with st.spinner("Thinking…"):
                ans, sources = st.session_state.rag.answer(user_q)
            st.chat_message("assistant").markdown(ans)
            if show_ctx:
                with st.expander("Retrieved context"):
                    for s in sources:
                        st.write(f"- {s}")
