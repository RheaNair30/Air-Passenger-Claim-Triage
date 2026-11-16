
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0,
    timeout=90,
    max_retries=3,
)
