import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.3-70b-versatile"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
