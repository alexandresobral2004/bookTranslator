import asyncio
import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class OpenAIEditor:
    async def postedit_translation_async(
        self,
        original_en: str,
        current_pt: str,
        user_api_key: Optional[str] = None
    ) -> str:
        """
        Usa o modelo GPT-4o-mini da OpenAI para revisar e corrigir traduções locais
        de baixa qualidade de forma assíncrona.
        Preserva as tags HTML inline (<b>/<i>).
        """
        # 1. Determina a API Key a ser usada
        api_key = user_api_key or settings.OPENAI_API_KEY
        
        if not api_key:
            logger.warning("Solicitada pós-edição OpenAI, mas nenhuma chave de API foi fornecida. Mantendo tradução original.")
            return current_pt

        # 2. Definição do prompt de pós-edição
        system_instruction = (
            "Você é um especialista em pós-edição e revisão de tradução técnica de livros do inglês para o português.\n"
            "Seu objetivo é ler a sentença original em inglês, ler a tradução inicial em português (que pode conter erros, "
            "repetições ou inconsistências) e retornar uma versão em português fluida, correta e natural.\n\n"
            "REGRAS IMPORTANTES:\n"
            "1. Retorne APENAS o texto revisado em português, sem introduções ou notas de rodapé.\n"
            "2. Mantenha exatamente as tags HTML inline de estilo como <b>, </b>, <i>, </i> nos termos equivalentes traduzidos.\n"
            "3. Se o texto em português estiver correto, retorne-o inalterado."
        )

        user_content = (
            f"Texto Original (EN):\n{original_en}\n\n"
            f"Tradução a ser revisada (PT):\n{current_pt}"
        )

        # Executa a chamada bloqueante da OpenAI em thread separada para não bloquear o event loop
        def call_openai_safe():
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()

        try:
            revised_text = await asyncio.to_thread(call_openai_safe)
            logger.info("Pós-edição OpenAI executada com sucesso para um bloco.")
            return revised_text
        except Exception as e:
            logger.error(f"Erro na chamada da API OpenAI para pós-edição: {str(e)}")
            # Em caso de falha da API, retorna a tradução do MarianMT original sem interromper o pipeline
            return current_pt

# Singleton do pós-editor
openai_editor = OpenAIEditor()
