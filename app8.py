import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import trafilatura
import requests
import tempfile
import glob
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
chain = prompt | llm | StrOutputParser()

# ================== Helper: Extract Video ID ==================
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# ================== Helper: YouTube via yt-dlp ==================
def extract_youtube_transcript(url):
    try:
        import yt_dlp
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "skip_download": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                "subtitleslangs": ["en", "ar", "en-US"],
                "subtitlesformat": "vtt",
                "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            vtt_files = glob.glob(f"{tmpdir}/*.vtt")
            if not vtt_files:
                return None

            with open(vtt_files[0], "r", encoding="utf-8") as f:
                lines = f.readlines()

            text_lines = []
            for line in lines:
                line = line.strip()
                if (not line or line.startswith("WEBVTT") or
                        "-->" in line or line.startswith("NOTE") or
                        re.match(r"^\d+$", line)):
                    continue
                clean = re.sub(r"<[^>]+>", "", line).strip()
                if clean:
                    text_lines.append(clean)

            # Deduplicate consecutive lines
            deduped = [text_lines[0]] if text_lines else []
            for line in text_lines[1:]:
                if line != deduped[-1]:
                    deduped.append(line)

            return " ".join(deduped)

    except Exception as e:
        st.warning(f"yt-dlp error: {e}")
        return None

# ================== Helper: Extract URL Content ==================
def extract_url_content(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        text = trafilatura.extract(response.text, include_tables=True, no_fallback=False)
        if text and len(text.strip()) > 100:
            return text.strip()
    except Exception:
        pass

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text.strip()) > 100:
                return text.strip()
    except Exception:
        pass

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

                if "youtube.com" in generic_url or "youtu.be" in generic_url:
                    video_id = extract_video_id(generic_url)
                    if not video_id:
                        st.error("❌ Could not extract video ID")
                        st.stop()

                    with st.status("📥 Fetching YouTube transcript..."):
                        text = extract_youtube_transcript(generic_url)

                    if not text:
                        st.error("❌ No captions found. The video may not have subtitles.")
                        st.stop()
                else:
                    text = extract_url_content(generic_url)
                    if not text:
                        st.error("❌ Could not extract content from this URL.")
                        st.stop()

                with st.spinner("✍️ Summarizing..."):
                    output = chain.invoke({"text": text})
                st.success(output)

        except Exception as e:
            st.exception(f"Error: {e}")
