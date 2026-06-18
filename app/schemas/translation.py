from pydantic import BaseModel, Field
from typing import Optional

class TranslationOptions(BaseModel):
    use_glossary: bool = Field(default=True, description="Indica se deve aplicar o glossário técnico via RAG.")
    use_openai_postedit: bool = Field(default=False, description="Indica se deve utilizar o modelo OpenAI para pós-edição de trechos problemáticos.")
    openai_api_key: Optional[str] = Field(default=None, description="Chave API opcional do usuário para pós-edição OpenAI.")
