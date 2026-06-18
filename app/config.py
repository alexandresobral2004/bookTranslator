import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Configuração de leitura do arquivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Diretórios de Dados
    MODEL_CACHE_DIR: str = Field(default="./data/models")
    UPLOAD_DIR: str = Field(default="./data/uploads")
    OUTPUT_DIR: str = Field(default="./data/outputs")
    GLOSSARY_DIR: str = Field(default="./data/glossary")

    # Configurações de Upload
    MAX_FILE_MB: int = Field(default=5)

    # Configurações do MarianMT
    MARIAN_MODEL_NAME: str = Field(default="Helsinki-NLP/opus-mt-tc-big-en-pt")
    CHUNK_SIZE_TOKENS: int = Field(default=400)
    BATCH_SIZE: int = Field(default=16)
    TRANSLATION_WORKERS: int = Field(default=3)
    # Número de beams para decodificação: 1 = greedy (mais rápido), 4 = beam search (melhor qualidade)
    TRANSLATION_NUM_BEAMS: int = Field(default=1)
    # Threads PyTorch para inferência CPU (0 = automático, usa todos os cores)
    TORCH_NUM_THREADS: int = Field(default=0)

    # Configurações de RAG / Glossário
    GLOSSARY_FILE_NAME: str = Field(default="glossary.csv")
    GLOSSARY_INDEX_DIR: str = Field(default="glossary_index")
    EMBEDDING_MODEL_NAME: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    RAG_K_NEIGHBORS: int = Field(default=3)

    # Configurações de Pós-Edição OpenAI (Opcional)
    USE_OPENAI_POSTEDIT: bool = Field(default=False)
    OPENAI_API_KEY: str = Field(default="")
    QUALITY_THRESHOLD: float = Field(default=0.6)

    # Cleanup e Retenção
    JOB_RETENTION_HOURS: int = Field(default=24)

    @property
    def max_content_length(self) -> int:
        return self.MAX_FILE_MB * 1024 * 1024

    def create_directories(self) -> None:
        """Garante que todos os diretórios de dados existam."""
        for path in [self.MODEL_CACHE_DIR, self.UPLOAD_DIR, self.OUTPUT_DIR, self.GLOSSARY_DIR]:
            os.makedirs(path, exist_ok=True)

settings = Settings()
# Auto-criar pastas se necessário ao importar
settings.create_directories()
