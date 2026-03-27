EVALUATOR_PROMPT = """Você está anotando dados de uma consulta de emergência.

A partir do prontuário estruturado abaixo, organize a consulta da seguinte maneira:

**QP:** [queixa principal em uma frase simples]

**HDA:** [história da doença atual — início, caráter, evolução, sintomas associados]

**Exame Físico:**
BEG, LOTE CHAAE, BNFRR2T, MV+, ARA, sem edemas em MMII.
[Adicione dados específicos se forem reportados no prontuário acima.
Inclua sinais vitais se disponíveis. Marque como [info indeterminada]
se algum dado foi mencionado mas estava ambíguo no texto original.]

**Conduta:** [condutas, exames solicitados, medicações]

Se disponíveis no prontuário acima, inclua também (não obrigatório):
**HPP:** [histórico patológico pregresso]
**AF:** [antecedentes familiares]
**MH:** [medicações em uso]

Regras:
- Texto final com aproximadamente 1000 caracteres
- Não invente informações — use apenas o que está no prontuário fornecido
- Linguagem técnica e concisa

Prontuário estruturado:
{prontuario_1}"""
