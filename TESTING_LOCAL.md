# Guia de Testes e Execução Local (Sem Docker)

Este documento detalha o conjunto de testes disponíveis no sistema **BookTranslator** e as instruções para executá-los e validar o funcionamento completo da aplicação rodando nativamente no macOS/Linux.

---

## 🛠️ Passo 1: Configuração do Ambiente Local

Antes de rodar os testes, configure as dependências do sistema e do Python rodando o script de configuração:

```bash
# Permissão de execução (caso necessário)
chmod +x setup_local.sh

# Executa a configuração do sistema e ambiente virtual (.venv)
./setup_local.sh
```

**O que o script faz:**
1. Instala dependências nativas (`pango`, `cairo`, `libffi`) via Homebrew no macOS (necessárias para o WeasyPrint).
2. Cria o ambiente virtual em `.venv/`.
3. Instala todas as dependências do `requirements.txt`.
4. Cria as pastas de cache de dados e modelos.
5. Copia o arquivo `.env.example` para `.env`.

---

## 🔬 Plano de Testes do Sistema

O sistema possui 4 níveis de validação para garantir a integridade de todas as camadas.

### 1. Teste de Smoke (Sanidade de Bibliotecas)
Garante que todas as bibliotecas nativas de Deep Learning (`PyTorch`), processamento de PDFs (`PyMuPDF`), compilação visual (`WeasyPrint`) e banco vetorial (`FAISS`) foram instaladas corretamente e conseguem carregar dependências do SO.

**Como executar:**
```bash
# Ative o virtualenv
source .venv/bin/activate

# Execute o script de smoke test
python3 tests/smoke_test.py
```

**Resultado esperado:**
Deverá imprimir `[OK]` para todas as bibliotecas e compilar com sucesso um PDF teste em `/tmp/smoke_test_weasyprint.pdf` sem disparar erros de sistema (`Pango/Cairo`).

---

### 2. Testes Unitários (`pytest`)
Os testes unitários cobrem a lógica de negócio principal do pipeline de forma extremamente rápida (<100ms) sem baixar modelos de aprendizado de máquina reais (usando Mocks).

**Componentes testados:**
* **`Chunker`**: Divisão correta de parágrafos e conversão de spans de texto do PDF para tags HTML inline (`<b>`, `<i>`).
* **`QualityScorer`**: Avaliação de qualidade de tradução baseada em comprimento de caracteres, repetições de loopings e marcação `<unk>`.
* **`TermReplacer`**: Substituição semântica fuzzy por placeholders (`{{TERM_X}}`) e posterior restauração pós-tradução.

**Como executar:**
```bash
pytest tests/unit/test_pipeline_logic.py
```

---

### 3. Teste Manual E2E (Interface Gráfica)
Verifica o fluxo completo da aplicação desde a entrada do PDF à geração final de download via rotas SSE (Server-Sent Events).

**Como executar:**
1. Inicie o servidor local FastAPI com reload ativo:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Abra o navegador em: [http://localhost:8000](http://localhost:8000)
3. Selecione ou arraste um PDF técnico em inglês pequeno (de 1 a 3 páginas).
4. Clique em **Traduzir Livro**.
5. **Acompanhe visualmente as etapas do SSE:**
   - [ ] *Iniciando leitura e extração do PDF...*
   - [ ] *Texto extraído com sucesso. Iniciando segmentação...*
   - [ ] *Carregando dicionário e aplicando termos do glossário...*
   - [ ] *Iniciando tradução local via MarianMT...* (nota: o primeiro download do modelo de 300MB levará cerca de 1 a 2 minutos; depois será instantâneo).
   - [ ] *Reconstruindo layout e gerando HTML...*
   - [ ] *Compilando PDF final com WeasyPrint...*
   - [ ] *Tradução concluída com sucesso! Download pronto.*
6. Certifique-se de que o download do PDF traduzido foi disparado automaticamente e que o layout do arquivo final foi preservado.

---

### 4. Testes de Endpoints da API (Inspeção Manual)
Valida a saúde das rotas HTTP do servidor FastAPI.

* **Health Check**:
  ```bash
  curl http://localhost:8000/health
  ```
  *Resposta esperada:* `{"status":"healthy","app":"BookTranslator", ...}`

* **Documentação Automática Swagger**:
  Acesse no navegador: [http://localhost:8000/docs](http://localhost:8000/docs) para inspecionar os esquemas JSON de upload e jobs.

---

## ⚠️ Resolução de Problemas Comuns Locally

* **Erro: `ModuleNotFoundError: No module named 'faiss'`**
  Certifique-se de estar rodando o comando com o `.venv` ativo (`source .venv/bin/activate`).
* **Erro WeasyPrint: `broken library link / GDK-Pixbuf`**
  O WeasyPrint depende das bibliotecas Cairo e Pango. No macOS, rode `brew install pango cairo libffi` para reinstalar os links dinâmicos do macOS.
* **Consumo de Memória**:
  A primeira tradução local irá carregar o MarianMT na memória (aproximadamente 300MB-450MB). O pipeline utiliza automaticamente a aceleração **MPS** (Apple Silicon) se você estiver rodando em um Mac com processador M1/M2/M3.
