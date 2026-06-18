# app/dependencies.py
# Modulado para injeção de dependência flexível no FastAPI

from app.config import settings

def get_settings():
    return settings
