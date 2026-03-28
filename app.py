"""
Escriba Médico — Fase 0 MVP
Sistema multiagente de apoio clínico para pronto-socorro.
Baseado no amie-agents (fabianonbfilho).
"""

import os
import logging
import gradio as gr
from datetime import datetime

from agents import (
    run_agent1_translator,
    run_agent2_evaluator,
    run_agent3_emergency,
)
from utils import anonymize, get_anonymization_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API key do ambiente (opcional — usuário pode inserir na UI)
API_KEY_ENV = os.environ.get("GOOGLE_API_KEY", "")
PROVIDER_ENV = os.environ.get("LLM_PROVIDER", "google")  # "google" ou "anthropic"

# ── Templates de protocolo rápido ───────────────────────────────────────────────
TEMPLATES = {
    "\U0001F195 Consulta livre": "",
    "\U0001F534 Emergência": "Paciente deu entrada no pronto-socorro com [descreva a queixa]. ",
    "\U0001FAC0 Dor Torácica / SCA": (
        "Paciente com dor torácica. Descreva: início, caráter, irradiação, "
        "fatores de melhora/piora, sintomas associados (dispneia, sudorese, náusea), "
        "antecedentes (HAS, DM, dislipidemia, tabagismo, IAM prévio), medicações. "
    ),
    "\U0001F9E0 AVC": (
        "Paciente com suspeita de AVC. Descreva: déficit neurológico (motor, fala, face), "
        "horário de início ou última vez visto bem, antecedentes (HAS, FA, AVE prévio), "
        "medicações anticoagulantes. "
    ),
    "\U0001FA78 Sepse": (
        "Paciente com possível foco infeccioso. Descreva: foco suspeito, tempo de evolução, "
        "febre, sinais vitais, estado mental, comorbidades, medicações em uso. "
    ),
    "\U0001F624 Dispneia": (
        "Paciente com dispneia. Descreva: início, caráter (progressiva/súbita), "
        "ortopneia, DPN, sibilância, febre, edema, antecedentes cardiopulmonares. "
    ),
    "\U0001F915 Politrauma": (
        "Paciente politraumatizado. Descreva: mecanismo do trauma, queixas principais, "
        "nível de consciência, sinais vitais, áreas de lesão aparente. "
    ),
    "\U0001F48A Intoxicação": (
        "Paciente com suspeita de intoxicação. Descreva: substância (se conhecida), "
        "quantidade, via, horário, sintomas atuais, tratamentos realizados. "
    ),
    "\U0001F531 PCR / ACLS": (
        "Paciente em PCR ou pós-RCE. Descreva: ritmo inicial, tempo de PCR, "
        "manobras realizadas, drogas administradas, ritmo atual, Glasgow pós-RCE. "
    ),
}

EXEMPLO = {
    "texto": (
        "Paciente do sexo masculino, 58 anos, hipertenso, diabético, tabagista há 30 anos. "
        "Chegou ao PS às 14h com dor torácica há 2 horas, constrictiva, irradiando para o "
        "braço esquerdo, EVA 8, associada a sudorese fria e dispneia leve. Nega melhora com "
        "repouso. Usa Metformina 850mg 2x ao dia, Losartana 50mg 1x ao dia e AAS 100mg. "
        "PA 150x90, FC 98, FR 18, SpO2 96%, Tax 36.8. Pai faleceu de infarto aos 60 anos."
    )
}


# ── Funções principais ───────────────────────────────────────────────────────────
def load_template(template_name: str) -> str:
    return TEMPLATES.get(template_name, "")


def load_example() -> str:
    return EXEMPLO["texto"]


def validate(texto: str, api_key: str) -> str | None:
    if not texto.strip():
        return "\u26a0\ufe0f Preencha o texto da consulta antes de analisar."
    effective_key = api_key.strip() or API_KEY_ENV
    if not effective_key:
        return "\u26a0\ufe0f Insira uma API Key para executar a análise."
    return None


def analisar(
    texto: str,
    api_key: str,
    provider: str,
    progress=gr.Progress(),
) -> tuple:
    """
    Fluxo principal: texto → anonimizar → Agente 1 → Agente 2 → prontuário único.
    Retorna: (prontuario_final, status_anonimizacao, prontuario_final_state)
    """
    error = validate(texto, api_key)
    if error:
        return error, "", ""

    effective_key = api_key.strip() or API_KEY_ENV

    try:
        # 1. Anonimização
        progress(0.05, desc="Anonimizando texto...")
        texto_anonimizado = anonymize(texto)
        status_anon = get_anonymization_summary(texto, texto_anonimizado)
        logger.info(f"Anonimização: {status_anon}")

        # 2. Agente 1 — extrai e estrutura
        progress(0.2, desc="Agente 1: extraindo dados da consulta...")
        prontuario_bruto = run_agent1_translator(texto_anonimizado, effective_key, provider)

        # 3. Agente 2 — formata prontuário final
        progress(0.65, desc="Agente 2: formatando prontuário...")
        prontuario_final = run_agent2_evaluator(prontuario_bruto, effective_key, provider)

        progress(1.0, desc="Concluído!")
        return prontuario_final, f"\u2705 {status_anon}", prontuario_final

    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        err = f"\u274c Erro durante análise: {str(e)}"
        return err, "", ""


def executar_sugestao(
    prontuario: str,
    api_key: str,
    provider: str,
    progress=gr.Progress(),
) -> str:
    """Agente 3 sob demanda — gera sugestão clínica a partir do prontuário."""
    if not prontuario.strip():
        return "\u26a0\ufe0f Execute a análise primeiro."
    effective_key = api_key.strip() or API_KEY_ENV
    if not effective_key:
        return "\u26a0\ufe0f Insira uma API Key."
    try:
        progress(0.3, desc="Gerando sugestão clínica...")
        resultado = run_agent3_emergency(prontuario, effective_key, provider)
        progress(1.0)
        return resultado
    except Exception as e:
        logger.error(f"Erro na sugestão clínica: {e}")
        return f"\u274c Erro: {str(e)}"


def nova_consulta():
    """Limpa todos os campos para nova consulta."""
    return ("", "", "", "", "")


# ── CSS ───────────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Força light mode via CSS — reforçado pelo JS abaixo */
:root, html { color-scheme: light only !important; }

body, .gradio-container {
    font-family: 'Inter', system-ui, sans-serif !important;
    background: #f8f9fa !important;
    color: #111827 !important;
}

.header-title { font-size: 1.4rem; font-weight: 700; color: #1a1a2e; }
.header-sub   { font-size: 0.85rem; color: #666; }
.status-bar   { font-size: 0.75rem; color: #666; padding: 4px 0; }

/* Botão de gravação de áudio (Speech-to-Text) */
.stt-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 16px;
    background: #2563eb !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
}
.stt-btn:hover { background: #1d4ed8 !important; }
.stt-status { font-size: 0.78rem; color: #dc2626; font-weight: 500; }

footer { display: none !important; }
"""

# ── JS: light-mode + Speech-to-Text ──────────────────────────────────────────────
# raw string: Python NÃO processa backslashes aqui.

APP_JS = r"""
() => {
  /* Força light mode — remove classe 'dark' e observa mudanças futuras */
  const forceLight = () => {
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    document.documentElement.style.colorScheme = 'light';
  };
  forceLight();
  new MutationObserver(forceLight).observe(document.documentElement, {
    attributes: true, attributeFilter: ['class', 'style']
  });

  /* Speech-to-Text — pt-BR, Chrome Web Speech API */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null, isRec = false;

  function updateTextbox(txt) {
    const el = document.querySelector('#texto-consulta textarea');
    if (!el) return;
    /* Usa o setter nativo para disparar o evento React corretamente */
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(el, (el.value ? el.value + ' ' : '') + txt.trim());
    el.dispatchEvent(new Event('input', {bubbles: true}));
  }

  window.toggleSTT = function() {
    const btn = document.getElementById('stt-btn');
    const st  = document.getElementById('stt-status');
    if (!SR) {
      if (st) st.textContent = 'Use Chrome para speech-to-text';
      return;
    }
    if (isRec) { recognition.stop(); return; }

    recognition = new SR();
    recognition.lang = 'pt-BR';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRec = true;
      if (btn) { btn.innerHTML = '&#9209; Parar'; btn.style.background = '#dc2626'; }
      if (st)  st.textContent = 'REC Gravando...';
    };
    recognition.onresult = (e) => {
      let t = '';
      for (let i = e.resultIndex; i < e.results.length; i++)
        if (e.results[i].isFinal) t += e.results[i][0].transcript + ' ';
      if (t) updateTextbox(t);
    };
    recognition.onend = () => {
      isRec = false;
      if (btn) { btn.innerHTML = '&#127908; Gravar &aacute;udio'; btn.style.background = ''; }
      if (st)  st.textContent = '';
    };
    recognition.onerror = (e) => {
      if (st) st.textContent = 'Erro: ' + e.error;
      isRec = false;
      if (btn) { btn.innerHTML = '&#127908; Gravar &aacute;udio'; btn.style.background = ''; }
    };
    recognition.start();
  };
}
"""

STT_HTML = """
<div style="margin: 6px 0 10px 0; display: flex; align-items: center; gap: 10px;">
  <button class="stt-btn" id="stt-btn"
          onclick="window.toggleSTT && window.toggleSTT()"
          title="Transcrição por voz em português — requer Chrome">
    &#127908; Gravar áudio
  </button>
  <span class="stt-status" id="stt-status"></span>
</div>
"""


# ── Interface Gradio ──────────────────────────────────────────────────────────────
with gr.Blocks(
    css=CSS,
    title="Escriba Médico",
    theme=gr.themes.Default(),
    js=APP_JS,
) as demo:

    prontuario_state = gr.State("")

    # Header
    gr.HTML("""
    <div style="padding: 16px 0 8px 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 16px;">
        <span class="header-title">&#129658; Escriba Médico</span>
        <span class="header-sub" style="margin-left: 12px;">
            Suporte clínico multiagente &middot; Pronto-Socorro
        </span>
    </div>
    """)

    with gr.Row():

        # ── Coluna esquerda — INPUT ────────────────────────────────────────────────
        with gr.Column(scale=1):

            gr.Markdown("**Protocolo rápido**")
            template_selector = gr.Dropdown(
                choices=list(TEMPLATES.keys()),
                value="\U0001F195 Consulta livre",
                label="",
                container=False,
            )

            with gr.Accordion("\u2699\ufe0f Configuração", open=False):
                api_key_input = gr.Textbox(
                    label="API Key",
                    placeholder="Cole sua chave aqui (ou configure via variável de ambiente)",
                    type="password",
                )
                provider_radio = gr.Radio(
                    choices=["google", "anthropic"],
                    value=PROVIDER_ENV,
                    label="Provedor LLM",
                )
                gr.Markdown(
                    "_Google: Gemma 27B (grátis) · Anthropic: Claude Sonnet (melhor qualidade)_",
                )

            texto_input = gr.Textbox(
                label="Texto da consulta",
                placeholder=(
                    "Digite ou cole o texto da consulta aqui.\n\n"
                    "Pode ser:\n"
                    "\u2022 Transcrição de áudio\n"
                    "\u2022 Anotações rápidas\n"
                    "\u2022 Relato em linguagem livre\n\n"
                    "Ex: 'Paciente 58 anos, dor torácica há 2h, constrictiva, "
                    "irradiando para MSE, EVA 8...'"
                ),
                lines=14,
                max_lines=30,
                elem_id="texto-consulta",
            )

            # Botão de microfone (Speech-to-Text)
            gr.HTML(STT_HTML)

            status_anon = gr.Markdown("", elem_classes=["status-bar"])

            with gr.Row():
                btn_exemplo = gr.Button("\U0001F4CB Exemplo", variant="secondary", size="sm")
                btn_limpar  = gr.Button("\U0001F5D1\ufe0f Limpar",  variant="secondary", size="sm")

            btn_analisar = gr.Button(
                "\U0001F50D Analisar Consulta",
                variant="primary",
                size="lg",
            )

        # ── Coluna direita — OUTPUT ────────────────────────────────────────────────
        with gr.Column(scale=1):

            with gr.Tabs():
                with gr.Tab("\U0001F4CB Prontuário"):
                    prontuario_out = gr.Markdown(
                        value="_Execute a análise para gerar o prontuário._"
                    )

                with gr.Tab("\U0001F4A1 Sugestão Clínica"):
                    btn_sugestao = gr.Button(
                        "\U0001F4A1 Gerar Sugestão Clínica", variant="secondary"
                    )
                    sugestao_out = gr.Markdown(
                        value="_Clique em 'Gerar Sugestão Clínica' após executar a análise._"
                    )

            btn_nova = gr.Button("\U0001F195 Nova Consulta", variant="secondary")

    gr.HTML("""
    <div style="margin-top: 16px; padding: 10px; background: #fff8e1;
                border-left: 3px solid #f59e0b; border-radius: 4px;
                font-size: 0.78rem; color: #555;">
        &#9877;&#65039; <strong>Ferramenta de suporte clínico</strong> &mdash;
        não substitui o julgamento médico.
        Toda conduta deve ser validada por profissional habilitado.
        Inspirado no AMIE (Google DeepMind).
    </div>
    """)

    # ── Eventos ────────────────────────────────────────────────────────────────────
    template_selector.change(
        fn=load_template, inputs=[template_selector], outputs=[texto_input]
    )
    btn_exemplo.click(fn=load_example, outputs=[texto_input])
    btn_limpar.click(fn=lambda: "", outputs=[texto_input])

    btn_analisar.click(
        fn=analisar,
        inputs=[texto_input, api_key_input, provider_radio],
        outputs=[prontuario_out, status_anon, prontuario_state],
    )

    btn_sugestao.click(
        fn=executar_sugestao,
        inputs=[prontuario_state, api_key_input, provider_radio],
        outputs=[sugestao_out],
    )

    btn_nova.click(
        fn=nova_consulta,
        outputs=[texto_input, prontuario_out, sugestao_out, status_anon, prontuario_state],
    )


if __name__ == "__main__":
    demo.launch()
