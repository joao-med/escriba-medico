"""
Camada de anonimização leve.
Remove nomes próprios e dados de identificação do texto bruto do STT.
Roda localmente — nenhum dado sai antes de passar por aqui.
"""

import re

# Prefixos médicos comuns em PT-BR
PREFIXOS_MEDICOS = [
    r"Dr\.?\s+", r"Dra\.?\s+", r"doutor\s+", r"doutora\s+",
    r"enfermeiro\s+", r"enfermeira\s+", r"técnico\s+"
]

# Padrões de dados sensíveis
REGEX_SENSIVEIS = [
    (r"\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?\d{2}", "[CPF]"),
    (r"\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}", "[TELEFONE]"),
    (r"\d{6,}", "[NÚMERO]"),
]

def anonymize(text: str) -> str:
    """
    Anonimiza texto bruto do STT.
    Substitui nomes e dados sensíveis por placeholders genéricos.
    Preserva toda informação clinicamente relevante.
    """
    if not text or not text.strip():
        return text

    result = text

    # 1. Remove dados sensíveis por regex
    for pattern, replacement in REGEX_SENSIVEIS:
        result = re.sub(pattern, replacement, result)

    # 2. Substitui "Dr. Nome" / "Dra. Nome" → "médico"
    for prefixo in PREFIXOS_MEDICOS:
        # Captura o prefixo + uma ou duas palavras (nome próprio)
        pattern = prefixo + r"[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][a-záéíóúàâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][a-záéíóúàâêôãõç]+)?"
        result = re.sub(pattern, "médico", result, flags=re.IGNORECASE)

    # 3. Tenta detectar padrão "paciente Nome Sobrenome" → "paciente"
    result = re.sub(
        r"\bpaciente\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][a-záéíóúàâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][a-záéíóúàâêôãõç]+){1,3}",
        "paciente",
        result,
        flags=re.IGNORECASE
    )

    # 4. Substitui "o senhor/a senhora Nome" → "o paciente"
    result = re.sub(
        r"\b(o senhor|a senhora|o sr\.?|a sra\.?)\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][a-záéíóúàâêôãõç]+",
        "o paciente",
        result,
        flags=re.IGNORECASE
    )

    return result


def get_anonymization_summary(original: str, anonymized: str) -> str:
    """Retorna um resumo do que foi anonimizado."""
    if original == anonymized:
        return "Nenhuma substituição realizada."

    changes = []
    for pattern, replacement in REGEX_SENSIVEIS:
        matches = re.findall(pattern, original)
        if matches:
            changes.append(f"{len(matches)}x {replacement}")

    return f"Anonimizações: {', '.join(changes) if changes else 'nomes substituídos'}"
