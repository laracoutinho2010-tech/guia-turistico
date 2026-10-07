import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Carrega variáveis de ambiente (localmente)
load_dotenv()

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Guia Turístico & Socorro",
    page_icon="✈️",
    layout="centered"
)

# Inicializa o cliente Groq usando os secrets do Streamlit Cloud ou arquivo .env local
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("⚠️ Chave da API da Groq não encontrada! Configure o arquivo .env ou os Secrets do Streamlit.")
    st.stop()

client = Groq(api_key=groq_api_key)

# Prompt Mestre do Agente
SYSTEM_PROMPT = """
Você é um Agente de Turismo especializado em suporte a viajantes. 

Sua Missão e Função:
- Auxiliar pessoas que estão planejando uma viagem, dar ideias criativas de lugares turísticos imperdíveis e prestar socorro imediato caso o viajante se perca.
- O principal problema que você resolve é orientar com precisão quem está desorientado ou perdido durante o passeio.

Público-Alvo:
- Pessoas que estão viajando no momento ou planejando uma próxima aventura.

Estilo de Comunicação:
- Seja objetivo, descontraído, divertido e muito bem-informado sobre todos os pontos turísticos do destino.
- Utilize um formato educado, porém acessível e sem formalidades chatas, adequado para todos os públicos.

Informações a Considerar:
- Considere sempre o contexto fornecido pelo usuário (como a localização atual que ele informar) para traçar rotas, sugerir atrações próximas ou ajudar no resgate de orientação.

O que EVITAR Estritamente:
- Nunca envie informações de localização errada ou imprecisas. Se faltar dado sobre a localização exata, peça educadamente para o usuário detalhar onde está.
"""

# Interface visual
st.title("✈️ Guia Turístico & SOS Viagem")
st.markdown("O seu assistente de bolso para planejar roteiros ou te salvar se você se perder por aí! 🗺️")

# Sidebar com controles extras (simulando a localização em tempo real)
with st.sidebar:
    st.header("📍 Configurações de Viagem")
    localizacao_atual = st.text_input("Onde você está agora? (Ex: Roma, Itália / Perdido perto do Coliseu)")
    destino_interesse = st.text_input("Para onde quer ir ou planeja viajar?")
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Inicializa o histórico de mensagens no Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Olá! Sou seu agente de turismo. Como posso te ajudar hoje? Vai planejar uma trip ou precisa de socorro com a rota? 🎒🌍"}
    ]

# Exibe o histórico de mensagens (ignorando a system message na tela)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrada do usuário pelo chat
if prompt := st.chat_input("Digite sua dúvida ou peça ajuda com sua localização..."):
    
    # Adiciona contexto de localização se o usuário preencheu na barra lateral
    user_input_with_context = prompt
    if localizacao_atual:
        user_input_with_context = f"[Minha localização atual informada: {localizacao_atual}] {prompt}"
    if destino_interesse:
        user_input_with_context = f"[Destino de interesse: {destino_interesse}] " + user_input_with_context

    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input_with_context})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chamada para a API da Groq (usando um modelo rápido como llama-3.3-70b-versatile)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            
            full_response = completion.choices[0].message.content
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"Ops! Tive um probleminha técnico para me conectar com a central de turismo: `{e}`"
            message_placeholder.markdown(full_response)

    # Salva a resposta do assistente no histórico
    st.session_state.messages.append({"role": "assistant", "content": full_response})