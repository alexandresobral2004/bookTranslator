# BookTranslator — Tradutor de Livros PDF

BookTranslator é um sistema web em Python para tradução de livros técnicos PDF de inglês para português. Utiliza **FastAPI** no backend, tradução local offline com **MarianMT**, RAG com glossário via **FAISS** e geração de PDF final com **WeasyPrint**.

---

## 🚀 Como Implantar no Railway

O sistema está preparado para deploy automático no **Railway** através do Dockerfile.

### 1. Requisitos de Configuração no Railway
Ao criar o serviço no Railway a partir do seu repositório GitHub, certifique-se de configurar:

#### Variáveis de Ambiente (Variables)
- `PORT`: O Railway definirá isso automaticamente. O Dockerfile já está preparado para ler essa variável dinamicamente.
- `USE_OPENAI_POSTEDIT`: Defina como `true` se quiser ativar a revisão via OpenAI.
- `OPENAI_API_KEY`: Sua chave de API da OpenAI (caso a revisão esteja ativa).
- `MODEL_CACHE_DIR`: `/app/data/models` (Opcional, recomendado manter o padrão).

#### Armazenamento Persistente (Volumes)
Como os modelos MarianMT e Sentence-Transformers possuem cerca de 300MB e 500MB respectivamente, baixá-los a cada reinicialização do container causará alta latência.
1. Vá nas configurações do serviço no Railway.
2. Adicione um **Volume** de armazenamento persistente.
3. Configure o **Mount Path** do volume para:
   ```
   /app/data
   ```
Isso persistirá a pasta `/app/data/models` (cache dos modelos de IA), `/app/data/uploads` e `/app/data/outputs`, mantendo a velocidade de inicialização do servidor instantânea após a primeira execução.

---

## 🛠️ Como Executar Localmente

Consulte as instruções detalhadas em [walkthrough.md](walkthrough.md).
