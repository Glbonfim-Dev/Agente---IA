# BetCoach AI

Chatbot local e leve para consultar e tirar dúvidas educacionais sobre apostas esportivas. Não possui cadastro, painel de banca, login, e-mail ou dependências externas.

## Executar

Com Python 3.11 ou superior:

```powershell
cd betcoach-chatbot
python run.py
```

O navegador abre em `http://localhost:8501`. Não é necessário criar `.venv` nem instalar pacotes.

## Ollama opcional

Sem Ollama, o chatbot consulta os documentos locais e usa respostas básicas. Para respostas generativas, instale o Ollama e baixe o modelo:

```powershell
ollama pull llama3.2
```

## Estrutura

```text
app.py               servidor local do chat
run.py               inicializador
static/              interface visual
database.py          histórico SQLite
knowledge_base.py    busca local leve
local_llm.py         Ollama opcional
fallback.py          respostas sem Ollama
knowledge/           conteúdo educacional
prompts/             regras do assistente
data/                histórico local
```

O projeto usa somente a biblioteca padrão do Python. Não consulta estatísticas esportivas em tempo real e não promete resultados.
