# 🎥📄 SummarizeAI - Multi-Source Content Summarizer

**SummarizeAI** is a Streamlit-powered web application that leverages Large Language Models (LLMs) via Groq and LangChain to provide concise summaries of YouTube videos and website articles.

👉 Simply paste a link, and get a **300-word summary in seconds**.

---

## ✨ Features

- 🎬 **YouTube Integration**  
  Automatically extracts transcripts from YouTube videos (supports English and Arabic).

- 🌐 **Web Scraping**  
  Fetches and cleans content from standard URLs using `UnstructuredURLLoader`.

- ⚡ **High-Speed LLM**  
  Powered by the **Llama-3.3-70b model via Groq** for near-instant processing.

- 🎨 **Clean UI**  
  Minimalist interface built with Streamlit.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **Orchestration:** LangChain  
- **LLM API:** Groq Cloud  
- **Data Loaders:** YouTubeLoader & UnstructuredURLLoader  

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9+ or Anaconda environment installed

---

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/summarize-ai.git
cd summarize-ai
pip install -r requirements.txt
```

## 3. Environment Variables

Create a `.env` file in the root directory and add:

```bash
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here  # optional
```

## 4. Run the App

```bash
streamlit run app8.py
```
## 📖 How It Works

### Input
The user provides a URL.

### Detection
The app detects if the link is a YouTube video or a website.

### Extraction
- **For YouTube** → pulls the transcript  
- **For Websites** → scrapes and cleans text content (with browser-like headers)

### Processing
The text is passed into a LangChain `load_summarize_chain` (Stuff method).

### Output
A formatted summary is displayed on the dashboard.

---

## ⚠️ Important Notes

### 📌 YouTube Transcripts
The video must have captions (manual or auto-generated).

### 🔐 SSL Verification
SSL verification is currently bypassed during scraping to improve compatibility with various websites.

