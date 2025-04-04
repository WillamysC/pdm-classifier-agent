# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    google_api_key: str
    pdm_file_path: str = "G:/.shortcut-targets-by-id/1UwC7m1xfbSIiGfjl_jHzZz9GkeMnqpOE/CENTRAL CADASTRO/01. BASE LEVEL/BASE LEVEL PDM's _ Atualizado em 16.10 - Sem Caracteres Especiais (1).xlsx"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    default_llm_model: str = "llama-3.1-8b-instant"
    google_llm_model: str = "gemini-2.0-flash-exp"

    
    class Config:
        env_file = ".env"
