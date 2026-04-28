## C:\Users\abdoa\anaconda3\Scripts\activate C:\Users\abdoa\anaconda3\envs\Ai_agent


import streamlit as st
#from langchain_huggingface import HuggingFaceEndpoint
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader, UnstructuredURLLoader

load_dotenv()

# ================== LLM ==================
#repo_id="google/gemma-2-9b"
#llm=HuggingFaceEndpoint(repo_id=repo_id,max_new_tokens=150,temperature=0.7,huggingfacehub_api_token=os.getenv("HF_TOKEN"),task="text-generation")
st.secrets["GROQ_API_KEY"]

api_key = os.getenv("GROQ_API_KEY")
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

# ================== Main Logic ==================
if st.button("Summarize"):

    try:
        with st.spinner("Processing..."):

            docs = []

            # ===== YouTube Case =====
            if "youtube.com" in generic_url or "youtu.be" in generic_url:

                # Try LangChain loader first
                loader = YoutubeLoader.from_youtube_url(generic_url,language=["en","ar"])
                docs = loader.load()


            # ===== Website Case =====
            # ===== Website Case =====
            else:
                try:
                    loader = UnstructuredURLLoader(
                        urls=[generic_url],
                        ssl_verify=False,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        }
                    )
                    docs = loader.load()
                    
                    # Check if we actually got text
                    if not docs or len(docs[0].page_content.strip()) < 50:
                        # Fallback for sites that block Unstructured
                        st.info("🔄 Standard extraction failed. Trying fallback method...")
                        import requests
                        from bs4 import BeautifulSoup
                        
                        response = requests.get(generic_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                            
                        text = soup.get_text(separator=' ')
                        # Clean up whitespace
                        text = " ".join(text.split())
                        
                        from langchain.schema import Document
                        docs = [Document(page_content=text)]
                        
                except Exception as e:
                    st.error(f"❌ Extraction Error: {e}")
                    st.stop()

                if not docs or not docs[0].page_content.strip():
                    st.error("❌ Could not extract content from this URL")
                    st.stop()

            # ================== Summarization ==================
            chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)

            output = chain.invoke(docs)

            st.success(output["output_text"])

    except Exception as e:
        st.exception(f"Error: {e}")
