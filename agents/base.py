"""
Lógica base de execução de agentes.
Cada agente é uma chamada ao LLM com um prompt específico.
"""

import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


def get_llm(api_key: str, provider: str = "google"):
    """
    Retorna o LLM configurado.
    provider: "google" (Gemma/Gemini) ou "anthropic" (Claude)
    """
    if provider == "anthropic":
        return ChatAnthropic(
            model="claude-sonnet-4-5",
            anthropic_api_key=api_key,
            max_tokens=4096,
        )
    else:
        return ChatGoogleGenerativeAI(
            model="gemma-3-27b-it",
            google_api_key=api_key,
            max_output_tokens=4096,
        )


def run_agent(prompt_template: str, inputs: dict, api_key: str, provider: str = "google") -> str:
    """
    Executa um agente com o prompt e inputs fornecidos.
    Retorna o texto gerado pelo LLM.
    """
    try:
        llm = get_llm(api_key, provider)
        prompt = PromptTemplate.from_template(prompt_template)
        chain = prompt | llm
        response = chain.invoke(inputs)
        return response.content
    except Exception as e:
        logger.error(f"Erro no agente: {e}")
        return f"⚠️ Erro ao executar agente: {str(e)}"
