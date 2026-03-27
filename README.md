---
title: Escriba Médico
emoji: 🩺
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Escriba Médico

Sistema multiagente de apoio clínico para pronto-socorro.
Baseado no [amie-agents](https://huggingface.co/spaces/fabianonbfilho/amie-agents) (fabianonbfilho).

## Agentes

| Agente | Função |
|---|---|
| **1 — Tradutor Clínico** | Texto livre → Prontuário 1 estruturado (SOAP) |
| **2 — Avaliador** | Detecta lacunas, inconsistências e red flags |
| **3 — Emergencista** | Diagnósticos, exames, conduta, scores de gravidade |
| **4 — Sumarista** | Consolida Prontuário 2 final · aceita revisão manual |

## Configuração

Adicione a secret `GOOGLE_API_KEY` com sua chave do [Google AI Studio](https://aistudio.google.com).

Ou use `ANTHROPIC_API_KEY` com `LLM_PROVIDER=anthropic` para usar Claude.

## Aviso

> Ferramenta de suporte clínico — não substitui o julgamento médico.
> Toda conduta deve ser validada por profissional habilitado.
