import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import trafilatura
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

# ================== LLM ==================
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=api_key)

# ================== UI ==================
st.set_page_config(page_title="Summarizer", page_icon="🦜")
st.title("🦜 URL & YouTube Summarizer")
st.subheader("Summarize any URL or YouTube video")
generic_url = st.text_input("Enter URL", label_visibility="collapsed")

# ================== Prompt ==================
prompt_template = """
Provide a summary of the following content in 300 words:
Content:{text}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# ================== Chain (No load_summarize_chain needed) ==================
chain = prompt | llm | StrOutputParser()

# ================== Helper: Extract Video ID ==================
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# ================== Helper: Extract URL Content ==================
def extract_url_content(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    # Method 1: trafilatura via requests
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        text = trafilatura.extract(response.text, include_tables=True, no_fallback=False)
        if text and len(text.strip()) > 100:
            return text.strip()
    except Exception:
        pass

    # Method 2: trafilatura direct fetch
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text.strip()) > 100:
                return text.strip()
    except Exception:
        pass

    # Method 3: BeautifulSoup fallback
    try:
        from bs4 import BeautifulSoup
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if text and len(text.strip()) > 100:
            return text.strip()[:8000]
    except Exception:
        pass

    return None

# ================== Main Logic ==================
if st.button("Summarize"):
    if not generic_url.strip():
        st.warning("⚠️ Please enter a URL first.")
    else:
        try:
            with st.spinner("Processing..."):
                text = ""

                # ===== YouTube Case =====
                if "youtube.com" in generic_url or "youtu.be" in generic_url:
                    video_id = extract_video_id(generic_url)
                    if not video_id:
                        st.error("❌ Could not extract video ID from URL")
                        st.stop()

                    proxy_config = WebshareProxyConfig(
                        proxy_username=st.secrets["WEBSHARE_USER"],
                        proxy_password=st.secrets["WEBSHARE_PASS"],
                    )
                    ytt = YouTubeTranscriptApi(proxy_config=proxy_config)
                    transcript = ytt.fetch(video_id, languages=["en", "ar"])
                    text = " ".join([t.text for t in transcript])

                # ===== Website Case =====
                else:
                    text = extract_url_content(generic_url)
                    if not text:
                        st.error("❌ Could not extract content. The site may block bots or require login.")
                        st.stop()

                # ================== Summarization ==================
                output = chain.invoke({"text": text})
                st.success(output)

        except Exception as e:
            st.exception(f"Error: {e}")
