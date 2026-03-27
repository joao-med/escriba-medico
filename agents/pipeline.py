"""
Pipeline de execução dos agentes.
Cada função corresponde a um agente do fluxo.
"""

import logging
from datetime import datetime
from .base import run_agent
from prompts import (
    TRANSLATOR_PROMPT,
    EVALUATOR_PROMPT,
    EMERGENCY_PROMPT,
    SUMMARIZER_PROMPT,
    REVISION_PROMPT,
)

logger = logging.getLogger(__name__)


def run_agent1_translator(texto_anonimizado: str, api_key: str, provider: str) -> str:
    """Agente 1 — Converte texto bruto em Prontuário 1 estruturado."""
    logger.info("Agente 1 (Tradutor) iniciado")
    return run_agent(
        TRANSLATOR_PROMPT,
        {"texto": texto_anonimizado},
        api_key,
        provider,
    )


def run_agent2_evaluator(prontuario_1: str, api_key: str, provider: str) -> str:
    """Agente 2 — Avalia lacunas e inconsistências do Prontuário 1."""
    logger.info("Agente 2 (Avaliador) iniciado")
    return run_agent(
        EVALUATOR_PROMPT,
        {"prontuario_1": prontuario_1},
        api_key,
        provider,
    )


def run_agent3_emergency(prontuario_1: str, api_key: str, provider: str) -> str:
    """Agente 3 — Gera bloco de decisão clínica de emergência."""
    logger.info("Agente 3 (Emergencista) iniciado")
    return run_agent(
        EMERGENCY_PROMPT,
        {"prontuario_1": prontuario_1},
        api_key,
        provider,
    )


def run_agent4_summarizer(
    prontuario_1: str,
    decisao_clinica: str,
    api_key: str,
    provider: str,
) -> str:
    """Agente 4 — Gera Prontuário 2 final consolidado."""
    logger.info("Agente 4 (Sumarista) iniciado")
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return run_agent(
        SUMMARIZER_PROMPT,
        {
            "prontuario_1": prontuario_1,
            "decisao_clinica": decisao_clinica,
            "data_hora": data_hora,
        },
        api_key,
        provider,
    )


def run_agent4_revision(
    prontuario_2_atual: str,
    instrucao_medico: str,
    api_key: str,
    provider: str,
) -> str:
    """Agente 4 — Modo revisão: aplica instrução do médico ao Prontuário 2."""
    logger.info("Agente 4 (Revisão) iniciado")
    return run_agent(
        REVISION_PROMPT,
        {
            "prontuario_2_atual": prontuario_2_atual,
            "instrucao_medico": instrucao_medico,
        },
        api_key,
        provider,
    )
