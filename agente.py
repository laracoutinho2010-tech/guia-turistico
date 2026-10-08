import os
from flask import Flask, render_template_string, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração da API da Groq
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key) if groq_api_key else None

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

REQUISITO DE FORMATAÇÃO OBRIGATÓRIA:
- Não utilize nenhum caractere especial de formatação em suas respostas. 
- Proibido o uso de asteriscos (ou símbolos como *), negritos, itálicos, mais (+), barras (/), hashtags (#) ou qualquer outra marcação de markdown. 
- Escreva todo o conteúdo em texto puro, fluido e objetivo, estruturando suas respostas apenas com parágrafos simples e pontuação comum.

"""


# HTML embutido para mantermos o projeto com o mínimo de arquivos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guia Turístico & SOS Viagem</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 320px;
            background: #faf5ff;
            border-right: 1px solid #f3e8ff;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .header {
            padding: 20px 24px;
            background: white;
            border-bottom: 1px solid #e2e8f0;
        }
        .chat-container {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            padding: 12px 16px;
            border-radius: 16px;
            max-width: 70%;
            line-height: 1.5;
            font-size: 0.95rem;
        }
        .user {
            background: #0f172a;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .assistant {
            background: white;
            color: #1e293b;
            align-self: flex-start;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 12px;
        }
        input, button {
            font-family: 'Plus Jakarta Sans', sans-serif;
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            outline: none;
        }
        input { flex: 1; }
        button {
            background: #db2777;
            color: white;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background: #be185d; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 0.85rem; }
        .input-group input { width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div>
            <h2>📍 Configurações</h2>
            <div class="input-group">
                <label>Onde você está agora?</label>
                <input type="text" id="loc" placeholder="Ex: Coliseu, Roma">
            </div>
            <div class="input-group">
                <label>Destino de interesse:</label>
                <input type="text" id="dest" placeholder="Ex: Tóquio, Japão">
            </div>
        </div>
        <button onclick="limparChat()" style="background: #64748b; width: 100%;">🗑️ Limpar Conversa</button>
    </div>

    <div class="main">
        <div class="header">
            <h1 style="margin:0; font-size: 1.5rem;">✈️ Guia Turístico & SOS Viagem</h1>
            <p style="margin:4px 0 0 0; color: #64748b; font-size: 0.9rem;">Seu assistente de bolso para roteiros e resgates rápidos.</p>
        </div>
        
        <div class="chat-container" id="chat">
            <div class="message assistant">Olá! Sou seu agente de turismo. Como posso te ajudar hoje? Vai planejar uma trip ou precisa de socorro com a rota? 🎒🌍</div>
        </div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Digite sua dúvida ou peça ajuda..." onkeypress="if(event.key === 'Functi' || event.key === 'Enter') enviarMensagem()">
            <button onclick="enviarMensagem()">Enviar 🚀</button>
        </div>
    </div>

    <script>
        let historico = [];

        async function enviarMensagem() {
            const input = document.getElementById('userInput');
            const chat = document.getElementById('chat');
            const loc = document.getElementById('loc').value;
            const dest = document.getElementById('dest').value;

            if (!input.value.trim()) return;

            let textoUsuario = input.value;
            let textoExibicao = textoUsuario;

            if (loc || dest) {
                textoUsuario = `[Localização: ${loc || 'Não informada'} | Destino: ${dest || 'Não informado'}] ${textoUsuario}`;
            }

            // Adiciona mensagem do usuário na tela
            chat.innerHTML += `<div class="message user">${textoExibicao}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;

            historico.push({ role: "user", content: textoUsuario });

            // Envia para o backend Flask
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: historico })
            });

            const data = await response.json();
            
            if (data.resposta) {
                chat.innerHTML += `<div class="message assistant">${data.resposta}</div>`;
                historico.push({ role: "assistant", content: data.resposta });
            } else {
                chat.innerHTML += `<div class="message assistant">Erro ao conectar com a IA.</div>`;
            }
            chat.scrollTop = chat.scrollHeight;
        }

        function limparChat() {
            historico = [];
            document.getElementById('chat').innerHTML = `<div class="message assistant">Conversa reiniciada! Para onde vamos agora?</div>`;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({"resposta": "⚠️ Chave da API da Groq não configurada no servidor."})
    
    data = request.json
    mensagens = data.get("messages", [])
    
    # Insere o System Prompt no topo das mensagens para manter o comportamento do agente
    payload_mensagens = [{"role": "system", "content": SYSTEM_PROMPT}] + mensagens

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=payload_mensagens,
            temperature=0.1,
            max_tokens=1024,
        )
        resposta_ia = completion.choices[0].message.content
        return jsonify({"resposta": resposta_ia})
    except Exception as e:
        return jsonify({"resposta": f"Ops, ocorreu um erro técnico: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
