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
    run_agent4_summarizer,
    run_agent4_revision,
)
from utils import anonymize, get_anonymization_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY_ENV = os.environ.get("GOOGLE_API_KEY", "")
PROVIDER_ENV = os.environ.get("LLM_PROVIDER", "google")

TEMPLATES = {
    "🆕 Consulta livre": "",
    "🔴 Emergência": "Paciente deu entrada no pronto-socorro com [descreva a queixa]. ",
    "🫀 Dor Torácica / SCA": (
        "Paciente com dor torácica. Descreva: início, caráter, irradiação, "
        "fatores de melhora/piora, sintomas associados (dispneia, sudorese, náusea), "
        "antecedentes (HAS, DM, dislipidemia, tabagismo, IAM prévio), medicações. "
    ),
    "🧠 AVC": (
        "Paciente com suspeita de AVC. Descreva: déficit neurológico (motor, fala, face), "
        "horário de início ou última vez visto bem, antecedentes (HAS, FA, AVE prévio), "
        "medicações anticoagulantes. "
    ),
    "🩸 Sepse": (
        "Paciente com possível foco infeccioso. Descreva: foco suspeito, tempo de evolução, "
        "febre, sinais vitais, estado mental, comorbidades, medicações em uso. "
    ),
    "😤 Dispneia": (
        "Paciente com dispneia. Descreva: início, caráter (progressiva/súbita), "
        "ortopneia, DPN, sibilância, febre, edema, antecedentes cardiopulmonares. "
    ),
    "🤕 Politrauma": (
        "Paciente politraumatizado. Descreva: mecanismo do trauma, queixas principais, "
        "nível de consciência, sinais vitais, áreas de lesão aparente. "
    ),
    "💊 Intoxicação": (
        "Paciente com suspeita de intoxicação. Descreva: substância (se conhecida), "
        "quantidade, via, horário, sintomas atuais, tratamentos realizados. "
    ),
    "🔱 PCR / ACLS": (
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


def load_template(template_name: str) -> str:
    return TEMPLATES.get(template_name, "")


def load_example() -> str:
    return EXEMPLO["texto"]


def validate(texto: str, api_key: str) -> str | None:
    if not texto.strip():
        return "⚠️ Preencha o texto da consulta antes de analisar."
    effective_key = api_key.strip() or API_KEY_ENV
    if not effective_key:
        return "⚠️ Insira uma API Key para executar a análise."
    return None


def analisar(
    texto: str,
    api_key: str,
    provider: str,
    custom_prompt: str = "",
    progress=gr.Progress(),
) -> tuple:
    error = validate(texto, api_key)
    if error:
        return error, "", "", "", ""

    effective_key = api_key.strip() or API_KEY_ENV

    try:
        progress(0.05, desc="Anonimizando texto...")
        texto_anonimizado = anonymize(texto)
        status_anon = get_anonymization_summary(texto, texto_anonimizado)

        progress(0.2, desc="Agente 1: estruturando prontuário...")
        prontuario_1 = run_agent1_translator(
            texto_anonimizado, effective_key, provider, custom_prompt
        )

        progress(0.45, desc="Agente 2: avaliando lacunas...")
        avaliacao = run_agent2_evaluator(prontuario_1, effective_key, provider)

        progress(0.65, desc="Agente 3: raciocínio clínico...")
        decisao = run_agent3_emergency(prontuario_1, effective_key, provider)

        progress(0.85, desc="Agente 4: consolidando prontuário final...")
        prontuario_2 = run_agent4_summarizer(prontuario_1, decisao, effective_key, provider)

        progress(1.0, desc="Concluído!")
        return prontuario_1, avaliacao, decisao, prontuario_2, f"✅ {status_anon}"

    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        return f"❌ Erro durante análise: {str(e)}", "", "", "", ""


def regenerar_prontuario2(
    prontuario_2_atual: str,
    instrucao: str,
    api_key: str,
    provider: str,
    progress=gr.Progress(),
) -> str:
    if not prontuario_2_atual.strip():
        return "⚠️ Execute a análise primeiro para gerar o Prontuário 2."
    if not instrucao.strip():
        return "⚠️ Digite uma instrução de revisão antes de regenerar."
    effective_key = api_key.strip() or API_KEY_ENV
    if not effective_key:
        return "⚠️ Insira uma API Key."
    progress(0.3, desc="Aplicando revisão...")
    resultado = run_agent4_revision(prontuario_2_atual, instrucao, effective_key, provider)
    progress(1.0, desc="Revisão concluída!")
    return resultado


def nova_consulta():
    return ("", "", "", "", "", "", "")


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Force light mode */
:root, html { color-scheme: light only !important; }
.dark, html.dark, body.dark { all: unset !important; }

body, .gradio-container {
    font-family: 'Inter', system-ui, sans-serif !important;
    background: #f5f7fa !important;
    color: #111827 !important;
}

.header-title { font-size: 1.4rem; font-weight: 700; color: #1a1a2e; }
.header-sub   { font-size: 0.85rem; color: #666; }
.status-bar   { font-size: 0.75rem; color: #666; padding: 4px 0; }

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

# ── JS: light mode enforcement + Speech-to-Text ──────────────────────────────

APP_JS = """
() => {
  /* ---- Force light mode ---- */
  const forceLight = () => {
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    document.documentElement.style.colorScheme = 'light';
  };
  forceLight();
  new MutationObserver(forceLight).observe(document.documentElement, {
    attributes: true, attributeFilter: ['class', 'style']
  });

  /* ---- Speech-to-Text (Web Speech API, pt-BR) ---- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null, isRec = false;

  function updateTextbox(txt) {
    const el = document.querySelector('#texto-consulta textarea');
    if (!el) return;
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(el, (el.value ? el.value + ' ' : '') + txt.trim());
    el.dispatchEvent(new Event('input', {bubbles: true}));
  }

  window.toggleSTT = function() {
    const btn = document.getElementById('stt-btn');
    const st  = document.getElementById('stt-status');
    if (!SR) {
      if (st) st.textContent = '\u26a0\ufe0f Use Chrome para speech-to-text';
      return;
    }
    if (isRec) { recognition.stop(); return; }

    recognition = new SR();
    recognition.lang = 'pt-BR';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRec = true;
      if (btn) { btn.textContent = '\u23f9\ufe0f Parar grava\u00e7\u00e3o'; btn.style.background = '#dc2626'; }
      if (st)  st.textContent = '\ud83d\udd34 Gravando... fale agora';
    };
    recognition.onresult = (e) => {
      let t = '';
      for (let i = e.resultIndex; i < e.results.length; i++)
        if (e.results[i].isFinal) t += e.results[i][0].transcript + ' ';
      if (t) updateTextbox(t);
    };
    recognition.onend = () => {
      isRec = false;
      if (btn) { btn.textContent = '\ud83c\udfa4 Gravar \u00e1udio'; btn.style.background = ''; }
      if (st)  st.textContent = '';
    };
    recognition.onerror = (e) => {
      if (st) st.textContent = '\u26a0\ufe0f ' + e.error;
      isRec = false;
      if (btn) { btn.textContent = '\ud83c\udfa4 Gravar \u00e1udio'; btn.style.background = ''; }
    };
    recognition.start();
  };
}
"""

STT_HTML = """
<div style="margin: 6px 0 10px 0; display: flex; align-items: center; gap: 10px;">
  <button class="stt-btn" id="stt-btn"
          onclick="window.toggleSTT && window.toggleSTT()"
          title="Transcri\u00e7\u00e3o por voz em portugu\u00eas \u2014 requer Chrome">
    \ud83c\udfa4 Gravar \u00e1udio
  </button>
  <span class="stt-status" id="stt-status"></span>
</div>
"""

# ── Interface Gradio ──────────────────────────────────────────────────────────

with gr.Blocks(
    css=CSS,
    title="Escriba Médico",
    theme=gr.themes.Default(),
    js=APP_JS,
) as demo:

    gr.HTML("""
    <div style="padding: 16px 0 8px 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 16px;">
        <span class="header-title">🩺 Escriba Médico</span>
        <span class="header-sub" style="margin-left: 12px;">
            Suporte clínico multiagente · Pronto-Socorro
        </span>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):

            gr.Markdown("**Protocolo rápido**")
            template_selector = gr.Dropdown(
                choices=list(TEMPLATES.keys()),
                value="🆕 Consulta livre",
                label="",
                container=False,
            )

            with gr.Accordion("⚙️ Configuração", open=False):
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
                gr.Markdown("---")
                custom_prompt_input = gr.Textbox(
                    label="📝 Instruções adicionais para o Agente 1 (opcional)",
                    placeholder=(
                        'Ex: "Sempre adicione Escore HEART ao final do prontuário"\n'
                        '"Quando EF ausente, escreva N\u00e3o realizado ao inv\u00e9s de N\u00e3o informado"\n'
                        '"Destaque sinais de alarme em negrito"'
                    ),
                    lines=4,
                    info="Combinado com o prompt nativo. Deixe vazio para usar o padr\u00e3o.",
                )

            texto_input = gr.Textbox(
                label="Texto da consulta",
                placeholder=(
                    "Digite ou cole o texto da consulta aqui.\n\n"
                    "Pode ser:\n"
                    "• Transcrição de áudio\n"
                    "• Anotações rápidas\n"
                    "• Relato em linguagem livre\n\n"
                    "Ex: 'Paciente 58 anos, dor torácica há 2h, constrictiva, "
                    "irradiando para MSE, EVA 8...'"
                ),
                lines=14,
                max_lines=30,
                elem_id="texto-consulta",
            )

            gr.HTML(STT_HTML)

            status_anon = gr.Markdown("", elem_classes=["status-bar"])

            with gr.Row():
                btn_exemplo = gr.Button("📋 Exemplo", variant="secondary", size="sm")
                btn_limpar = gr.Button("🗑️ Limpar", variant="secondary", size="sm")

            btn_analisar = gr.Button(
                "🔍 Analisar Consulta",
                variant="primary",
                size="lg",
            )

        with gr.Column(scale=1):

            with gr.Tabs():
                with gr.Tab("📋 Prontuário 1"):
                    prontuario1_out = gr.Markdown(
                        value="_Execute a análise para gerar o Prontuário 1._"
                    )

                with gr.Tab("✅ Prontuário 2 Final"):
                    prontuario2_out = gr.Markdown(
                        value="_Execute a análise para gerar o Prontuário 2._"
                    )
                    gr.Markdown("---\n**💬 Revisar Prontuário 2**")
                    instrucao_input = gr.Textbox(
                        label="Instrução de revisão",
                        placeholder=(
                            'Ex: "inclua hipótese de TEP como diferencial", '
                            '"remova menção ao AAS da conduta", '
                            '"reformule o plano em tópicos numerados"'
                        ),
                        lines=3,
                    )
                    btn_regenerar = gr.Button(
                        "🔄 Regenerar Prontuário 2", variant="secondary"
                    )

                with gr.Tab("🧠 Decisão Clínica"):
                    decisao_out = gr.Markdown(
                        value="_Execute a análise para ver a decisão clínica._"
                    )

                with gr.Tab("⚠️ Avaliação"):
                    avaliacao_out = gr.Markdown(
                        value="_Execute a análise para ver as sugestões._"
                    )

            btn_nova = gr.Button("🆕 Nova Consulta", variant="secondary")

    gr.HTML("""
    <div style="margin-top: 16px; padding: 10px; background: #fff8e1;
                border-left: 3px solid #f59e0b; border-radius: 4px;
                font-size: 0.78rem; color: #555;">
        ⚕️ <strong>Ferramenta de suporte clínico</strong> — não substitui o julgamento médico.
        Toda conduta deve ser validada por profissional habilitado.
        Inspirado no AMIE (Google DeepMind).
    </div>
    """)

    template_selector.change(
        fn=load_template, inputs=[template_selector], outputs=[texto_input]
    )
    btn_exemplo.click(fn=load_example, outputs=[texto_input])
    btn_limpar.click(fn=lambda: "", outputs=[texto_input])

    btn_analisar.click(
        fn=analisar,
        inputs=[texto_input, api_key_input, provider_radio, custom_prompt_input],
        outputs=[prontuario1_out, avaliacao_out, decisao_out, prontuario2_out, status_anon],
    )

    btn_regenerar.click(
        fn=regenerar_prontuario2,
        inputs=[prontuario2_out, instrucao_input, api_key_input, provider_radio],
        outputs=[prontuario2_out],
    )

    btn_nova.click(
        fn=nova_consulta,
        outputs=[
            texto_input, prontuario1_out, avaliacao_out,
            decisao_out, prontuario2_out, instrucao_input, status_anon,
        ],
    )


if __name__ == "__main__":
    demo.launch()
