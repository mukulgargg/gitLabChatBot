# GitLab Handbook Chatbot

## Project Overview

This project implements a Retrieval-Augmented Generation (RAG) chatbot that answers questions about GitLab’s Handbook and Direction pages. It combines a custom web crawler, semantic chunking, embedding with Sentence Transformers, and a Pinecone vector database for retrieval, with a generative LLM (Gemini) for synthesis. The chatbot is delivered via a Streamlit web UI.

---

## 1. Project Documentation

### Approach & Architecture

- **Retrieval-Augmented Generation (RAG):**
  - The chatbot first retrieves relevant context from a vector database (Pinecone) using semantic search, then synthesizes an answer using a generative LLM.
- **Pipeline Steps:**
  1. **Crawling:**
     - A respectful, multi-threaded crawler fetches allowed pages from GitLab’s Handbook and Direction, following include/exclude rules.
     - Crawl status (success/failure/reason) is logged in a CSV for robust, resumable ingestion.
  2. **Parsing & Chunking:**
     - HTML is cleaned and parsed to extract main content.
     - Documents are split into overlapping semantic chunks for better retrieval granularity.
  3. **Embedding & Indexing:**
     - Each chunk is embedded using a Sentence Transformer (all-MiniLM-L6-v2).
     - Embeddings are stored in Pinecone, using the URL as the vector ID to ensure deduplication.
     - Metadata (URL, text) is saved in meta.json for fast lookup.
  4. **Evaluation:**
     - The pipeline includes scripts for Q&A evaluation and retrieval hit-rate measurement.
  5. **Chatbot UI:**
     - A Streamlit app provides a conversational interface, calling the RAG pipeline for each user query.

### Key Technical Decisions
- **Pinecone for Vector DB:**
  - Chosen for scalability, cloud support, and fast similarity search. URLs are used as vector IDs for deduplication.
- **Threaded Crawler:**
  - Multi-threading is used for efficient crawling. Crawl status is tracked in a CSV with reasons for failure, supporting robust retries.
- **Semantic Chunking:**
  - Overlapping chunks improve retrieval accuracy for long documents.
- **Sentence Transformers:**
  - all-MiniLM-L6-v2 balances speed and semantic quality for embedding.
- **Gemini LLM:**
  - Used for answer synthesis, with prompt templates for system and answer formatting.
- **Streamlit UI:**
  - Chosen for rapid prototyping and ease of deployment.
- **.env for Secrets:**
  - API keys for Pinecone and Gemini are loaded from a .env file for security and portability.

---

## 2. GitHub Repository Structure

```
gitlab-handbook-chatbot/
├─ app/
│  ├─ ui.py           # Streamlit app (chat UI)
│  ├─ api.py          # RAG pipeline (retrieval + synthesis)
│  ├─ guards.py       # Safety, grounding, answer policy
│  ├─ prompts.py      # System & answer templates
│  ├─ __init__.py
├─ ingest/
│  ├─ crawl.py        # Multi-threaded crawler
│  ├─ parse.py        # HTML -> text, section titles, canonical URLs
│  ├─ chunk.py        # Semantic chunking
│  ├─ embed.py        # Build Pinecone index
│  ├─ domains.yaml    # Seed URLs + include/exclude rules
│  └─ run_ingest.py   # Orchestrates crawl -> parse -> chunk -> index
├─ data/
│  ├─ corpus/         # Raw html/text cache
│  ├─ index/          # Pinecone index metadata
├─ eval/
│  ├─ qna_devset.jsonl# Seed questions w/ references
│  └─ run_eval.py     # Evaluation scripts
├─ .env.example       # Example for API keys
├─ requirements.txt   # All dependencies
├─ README.md          # This file
├─ PROJECT_WRITEUP.md # Extended write-up
```

---

## 3. Setup & Running Locally

### Prerequisites
- Python 3.12
- [Pinecone account](https://www.pinecone.io/) (API key, index, region)
- [Gemini API key](https://ai.google.dev/)

### Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/mukulgargg/gitLabChatBot.git
   cd gitlab-handbook-chatbot
   ```
2. **Set up a virtual environment:**
   ```sh
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   ```
    Edit .env with your keys
   ```


### Data Ingestion Pipeline
1. **Configure domains:**
   - Edit `ingest/domains.yaml` to set seed URLs and include/exclude rules.
2. **Run the ingestion pipeline:**
   ```sh
   python -m ingest.run_ingest
   # To retry only failed URLs:
   python -m ingest.run_ingest --retry-failed
   ```
   - This will crawl, parse, chunk, embed, and index the data in Pinecone.

### Running the Chatbot UI
```sh
streamlit run app/ui.py
```
- Open the provided local URL in your browser.

---

## 4. Core Functionality

### a. Data Processing
- **Crawling:**
  - Multi-threaded, respectful crawler with include/exclude rules.
  - Logs crawl status and reasons for robust, resumable ingestion.
- **Parsing:**
  - Cleans and extracts main content from HTML.
- **Chunking:**
  - Splits documents into overlapping semantic chunks.
- **Embedding & Indexing:**
  - Embeds chunks with Sentence Transformers.
  - Stores in Pinecone with URL as vector ID for deduplication.
  - Saves metadata for fast lookup.

### b. Chatbot Implementation
- **Retrieval:**
  - Encodes user query, retrieves top-k similar chunks from Pinecone.
- **Synthesis:**
  - Uses Gemini LLM to synthesize answers from retrieved context.
- **UI:**
  - Streamlit app for interactive Q&A.
- **Safety & Policy:**
  - Guards and prompt templates ensure safe, grounded, and policy-compliant answers.

---

## 5. Extending & Customizing
- **Add new domains:** Edit `domains.yaml` and rerun ingestion.
- **Change chunking/embedding:** Modify `chunk.py` or `embed.py`.
- **Switch LLM:** Update `app/api.py` to use a different model/provider.
- **Deploy:** Streamlit Cloud or any Python web host.

---

## 6. Troubleshooting
- **meta.json not found:** Run the ingestion pipeline first.
- **Duplicate URLs in index:** Not possible—deduplication is enforced by using URL as vector ID.
- **API key errors:** Ensure `.env` is set up and loaded.
- **Pinecone errors:** Check index name, region, and API key.

---

## 8. Acknowledgments
- [GitLab Handbook](https://about.gitlab.com/handbook/)
- [Pinecone](https://www.pinecone.io/)
- [Google Gemini](https://ai.google.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [Streamlit](https://streamlit.io/)
