# Mapa Arquitetural do Projeto: Capta+ (CaptaMais v3.0)

Guia oficial do **Capta+** (Gestao Inteligente de Editais e Captacao de Recursos). Referencia rapida e estruturada sobre a arquitetura do projeto, pipeline completo e todos os modulos do sistema.

---

## 1. Visao Geral do Pipeline

O sistema implementa um **pipeline automatizado de 4 etapas**:

```
BUSCAR → BAIXAR → ANALISAR → GERAR PROJETO
```

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│  1. BUSCAR (buscar-editais.sh -> API -> fetcher -> scrapers)    │
│     Prosas API V2 -> OAuth2 -> Paginacao -> Detalhes            │
│     Filtros: Whitelist TI -> OpenAI -> Blacklist                │
│     Resultado: array de Edital[]                                │
├─────────────────────────────────────────────────────────────────┤
│  2. BAIXAR (pdf-downloader.ts)                                  │
│     Cascata: S3 -> Link externo -> HTML -> Descricao API        │
│     Extracao: LlamaParse -> pdf-parse                           │
│     Salva PDF em data/downloads/edital-{id}.pdf                 │
├─────────────────────────────────────────────────────────────────┤
│  3. ANALISAR (analyzer.ts + validator.ts + scoring.ts)          │
│     LangChain + OpenAI gpt-4o-mini                              │
│     Schema Zod: datas, valores, elegibilidade, documentos      │
│     Validacao: datas, valores, completude, coerencia            │
│     Score: whitelist(30%) + IA(40%) + PDF(20%) + portal(5%)    │
│     Status: pendente -> pdf_baixado -> analisado                │
├─────────────────────────────────────────────────────────────────┤
│  4. GERAR PROJETO (writer.ts + prompts-projeto.ts)              │
│     Tavily: busca web para fundamentacao                        │
│     Prompt Anti-IA: sem cliches, tom tecnico                    │
│     Saida: 8 secoes + compliance + fontes                       │
│     Export: PDF ou Markdown                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Tecnologica

| Camada | Tecnologia |
|--------|------------|
| Framework | Next.js 14 (App Router) |
| Frontend | React 18, TypeScript 5.2 |
| Estilizacao | CSS Puro (Vanilla CSS) com Design Tokens |
| Banco | SQLite (better-sqlite3) + Drizzle ORM |
| IA | OpenAI GPT-4o/mini, LangChain |
| Busca Web | Tavily API |
| Extração PDF | LlamaParse, pdf-parse |
| Scraping | Axios, Cheerio |
| Validacao | Zod schemas |
| Testes | Vitest |
| Auth | bcrypt + cookies HTTP-only |
| Icones | Lucide React |

---

## 3. Estrutura de Diretorios

```
captaMais/
├── app/                          # Roteamento e Paginas (App Router)
│   ├── api/
│   │   ├── editais/
│   │   │   ├── route.ts              # GET editais (com filtros)
│   │   │   ├── busca/route.ts        # POST busca de editais
│   │   │   ├── analisar/route.ts     # POST analise IA
│   │   │   ├── carregar-downloads/   # POST carregar PDFs
│   │   │   ├── revisar/route.ts      # POST aprovar/rejeitar
│   │   │   ├── notificar/route.ts    # POST notificacoes
│   │   │   └── deletar/              # DELETE edital
│   │   ├── jobs/
│   │   │   └── run-weekly-scan/route.ts  # POST varredura semanal
│   │   ├── v1/
│   │   │   ├── projetos/
│   │   │   │   ├── route.ts          # GET/POST projetos
│   │   │   │   └── [id]/
│   │   │   │       ├── route.ts      # GET/PUT/DELETE projeto
│   │   │   │       ├── gerar/route.ts  # POST gerar proposta IA
│   │   │   │       └── export/route.ts # GET exportar PDF/MD
│   │   │   ├── editais/              # v1 editais API
│   │   │   ├── usuarios/             # CRUD usuarios + login
│   │   │   ├── areas/                # API areas tematicas
│   │   │   └── tags/                 # API tags
│   │   └── teste/
│   │       └── validacao-keywords/   # Teste de validacao
│   ├── dashboard/page.tsx            # Painel com metricas
│   ├── editais/page.tsx              # Listagem e revisao de editais
│   ├── projetos/
│   │   ├── page.tsx                  # Listagem de projetos
│   │   └── [id]/page.tsx             # Detalhe e geracao de projeto
│   ├── usuarios/page.tsx             # Gestao de usuarios
│   ├── configuracoes/page.tsx        # Configuracoes
│   ├── login/page.tsx                # Login
│   ├── layout.tsx                    # Layout raiz
│   ├── page.tsx                      # Landing page
│   └── globals.css                   # Design Tokens
├── lib/
│   ├── scraper/                      # *** CAMADA DE SCRAPING ***
│   │   ├── config.ts                 # Config de portais
│   │   ├── fetcher.ts                # Orquestrador de busca
│   │   ├── prosas-scraper.ts         # Scraper Prosas (OAuth2)
│   │   ├── capta-scraper.ts          # Scraper Capta
│   │   ├── portais-finep-cnpq-capes.ts  # Scrapers FINEP/CNPq/CAPES
│   │   ├── pipeline.ts               # Pipeline download+analise
│   │   ├── pipeline-keywords.ts      # Pipeline com filtro keywords
│   │   ├── pdf-downloader.ts         # Download em cascata
│   │   ├── pdf-extractor.ts          # Extracao de URLs PDF
│   │   ├── llamaparse-extractor.ts   # Extracao via LlamaParse
│   │   ├── edital-extractor.ts       # Extracao de conteudo
│   │   ├── worker.ts                 # Worker background
│   │   ├── filtros-ti.ts             # Whitelist/Blacklist/OpenAI
│   │   ├── keyword-map.ts            # Mapeamento de keywords
│   │   ├── keyword-validator.ts      # Validacao de keywords
│   │   ├── keyword-logger.ts         # Log de keywords
│   │   └── utils/path-utils.ts       # Utilitarios de caminho
│   ├── ai/                           # *** CAMADA DE INTELIGENCIA ***
│   │   ├── analyzer.ts               # Analise estruturada de edital
│   │   ├── classifier.ts             # Classificacao (e edital?)
│   │   ├── validator.ts              # Validacao de campos
│   │   ├── writer.ts                 # Geracao de propostas
│   │   ├── prompts.ts                # Prompts de analise
│   │   ├── prompts-projeto.ts        # Prompts Anti-IA de projeto
│   │   ├── schema-analise.ts         # Schema Zod da analise
│   │   ├── schema-projeto.ts         # Schema Zod do projeto
│   │   ├── scoring.ts                # Pontuacao composta
│   │   ├── classification-cache.ts   # Cache de classificacao
│   │   ├── search.service.ts         # Servico de busca
│   │   └── tavily-mcp.client.ts      # Integracao Tavily
│   ├── database/                     # *** CAMADA DE DADOS ***
│   │   ├── db.ts                     # Conexao SQLite
│   │   ├── schema.ts                 # Schema Drizzle ORM
│   │   ├── seed.ts                   # Seed admin
│   │   ├── repositories/
│   │   │   ├── base.repository.ts    # Repository base
│   │   │   ├── edital.repository.ts  # CRUD editais
│   │   │   ├── analise.repository.ts # Repository analise
│   │   │   ├── projeto.repository.ts # Repository projeto
│   │   │   ├── usuario.repository.ts # Repository usuario
│   │   │   ├── palavra-chave.repository.ts
│   │   │   └── search.repository.ts  # Repository busca
│   │   └── services/
│   │       ├── edital.service.ts     # Servico de editais
│   │       ├── projeto.service.ts    # Servico de projetos
│   │       ├── usuario.service.ts    # Servico de usuarios
│   │       ├── file.service.ts       # Servico de arquivos
│   │       └── import.service.ts     # Servico de importacao
│   ├── db/
│   │   └── editais-store.ts          # Store legado + interface Edital
│   ├── api/
│   │   ├── auth.ts                   # Verificacao de auth
│   │   └── validators/index.ts       # Validadores de API
│   ├── api-client/
│   │   └── edital.client.ts          # Client-side edital API
│   └── jobs/
│       └── scheduler.ts              # Cron scheduler (segunda 8h)
├── components/
│   ├── EditalReviewPanel.tsx         # Painel de revisao
│   ├── EditalReviewCard.tsx          # Card de revisao
│   ├── NotificacaoBell.tsx           # Campainha de notificacoes
│   ├── layout/
│   │   ├── main-layout.tsx           # Wrapper principal
│   │   ├── sidebar.tsx               # Menu lateral
│   │   └── topbar.tsx                # Barra superior
│   └── ui/
│       ├── badge.tsx, button.tsx, card.tsx, drawer.tsx
│       ├── input.tsx, spinner.tsx, textarea.tsx
├── scripts/
│   ├── buscar-editais.sh             # *** PONTO DE ENTRADA ***
│   ├── resumir-editais.sh            # Resumir editais
│   ├── reset-db.ts                   # Reset do banco
│   ├── migrate-json-to-sqlite.ts     # Migracao JSON->SQLite
│   └── setup-cron.sh                 # Setup cron job
├── base/                             # Modelos de referencia (PDFs)
├── data/
│   ├── capta.db                      # Banco SQLite
│   ├── editais.json                  # Dados legados
│   ├── portais-config.json           # Config de portais
│   ├── downloads/                    # PDFs baixados
│   └── notificacoes/                 # Notificacoes
├── docs/
│   ├── fluxo-busca-cadastro-editais.md
│   └── analise-completa-pipeline.md  # Analise completa
├── __tests__/                        # Testes
├── logs/                             # Logs de execucao
└── .agent/skills/                    # Skills do agente
```

---

## 4. ETAPA 1: BUSCAR EDITAL (Detalhamento)

### 4.1 Ponto de Entrada: `scripts/buscar-editais.sh` (460 linhas)

Shell script, UNICO ponto de entrada para buscas. A interface web NAO faz buscas automaticas.

**Funcoes:**
- `validate_prerequisites()` — valida Node.js, npm, curl
- `check_server()` — verifica se Next.js esta rodando, inicia se necessario
- `execute_search()` — chama POST em `/api/jobs/run-weekly-scan`
- `generate_report()` — gera relatorio de PDFs baixados
- `save_result()` — salva resultado em JSON

**Opcoes:** `--verbose`, `--dry-run`, `--url`, `--token`, `--help`

### 4.2 Orquestrador: `lib/scraper/fetcher.ts` (194 linhas)

**`buscarEditaisPortais()`** — orquestra busca em portais ativos:
- **Prosas** (prosas.com.br) — via API V2 com OAuth2
- **Capta** (capta.org.br) — scraping HTML

**`filtrarComClassificador()`** — prepara editais para analise IA (score neutro=50)

### 4.3 Scraper Prosas: `lib/scraper/prosas-scraper.ts` (456 linhas)

**Fluxo de autenticacao:**
1. `realizarLoginProsas()` — login via formulario Rails (email/senha do `.env.local`)
2. `carregarSessaoSalva()` — cache de sessao com expiracao de 8 horas
3. Re-autenticacao automatica em caso de falha (401)

**Fluxo de busca:**
1. Obtem token OAuth2 (client_credentials)
2. Consulta API V2 com paginacao (ate 10 paginas, 50 itens/pagina)
3. Para CADA edital, busca detalhe individual com `include=arquivos,sites`
4. Extrai PDFs do S3, datas, valores, anexos
5. Aplica **3 filtros**: Whitelist TI → OpenAI → Blacklist
6. Monta objeto `Edital` com campos enriquecidos

### 4.4 Filtros de TI: `lib/scraper/filtros-ti.ts` (902 linhas)

**Whitelist — 3 categorias:**
- `tecnologia` — 120+ termos (software, IA, cloud, blockchain, IoT, etc.)
- `contexto_institucional` — universidades, institutos federais, pesquisa
- `contexto_geral` — projeto, bolsa, edital

**Blacklist** — 80+ termos de areas irrelevantes. **DESATIVADA** — retorna sempre `true`.

**Validacao OpenAI** (`gpt-4o-mini`):
- Classifica em `TecnologiaFoco` (60+ categorias)
- Classifica em `TipoFerramenta` (framework, linguagem, plataforma, etc.)
- Retorna score (0-100) e confianca (0-100)
- Cache em memoria com TTL de 24 horas
- **Fallback permissivo** — se OpenAI falhar, aceita edital automaticamente

**Enums:**
- `TecnologiaFoco` — 60+ categorias: IA_MACHINE_LEARNING, BIG_DATA, CLOUD_COMPUTING, CYBERSECURITY, DEVOPS, WEB_MOBILE, BLOCKCHAIN, IOT, DATA_SCIENCE, PESQUISA_ACADEMICA, INOVACAO_TECNOLOGICA, etc.
- `TipoFerramenta` — FRAMEWORK, LINGUAGEM, BANCO_DADOS, IDE, PLATAFORMA, BIBLIOTECA, FERRAMENTA_DESENVOLVIMENTO, OUTRO

### 4.5 API de Varredura: `app/api/jobs/run-weekly-scan/route.ts` (271 linhas)

**5 fases:**
1. Buscar editais nos portais
2. Classificar com IA
3. Baixar e ler PDFs
4. Analisar com IA
5. Criar notificacao

**Autenticacao:** token de script OU cookie de admin

---

## 5. ETAPA 2: BAIXAR PDF (Detalhamento)

### 5.1 Arquivo Principal: `lib/scraper/pdf-downloader.ts` (477 linhas)

### 5.2 Estrategia de Download em Cascata (3 niveis)

```
ESTRATEGIA 1: PDF pre-assinado S3 (prioridade maxima)
    ↓ falha
ESTRATEGIA 2: Link externo
    ├── 2a: Link e PDF direto (.pdf)
    └── 2b: Link e pagina web → buscar PDF dentro
        ↓ falha
        FALLBACK: extrair texto do HTML
    ↓ falha
ESTRATEGIA 3: Descricao HTML da API
    ↓ falha
RESULTADO: sem_pdf
```

### 5.3 Funcoes

- `baixarELerPDFEdital()` — funcao principal, orquestra as 3 estrategias
- `baixarArquivo()` — download via axios com `responseType: arraybuffer`
- `extrairTextoPdf()` — 2 estrategias:
  1. **LlamaParse** (prioridade) — preserva tabelas e formatacao Markdown
  2. **pdf-parse** (fallback) — extracao local do PDF
- `buscarPdfNaPaginaHtml()` — busca links `.pdf` dentro de paginas web (Cheerio)
- `extrairTextoHtml()` — extrai texto limpo de HTML
- `limparHtmlParaTexto()` — remove tags HTML e converte entities
- `validarERegistrarConteudo()` — valida com keywords e registra em log

### 5.4 Funcao Principal

```typescript
baixarELerPDFEdital(id, opcoes, orgao, titulo, dataLimite) → {
  texto: string;
  fonte: 'pdf_s3' | 'pdf_link' | 'html_link' | 'descricao_api' | 'sem_pdf';
  pdfUrlEncontrada?: string;
  caminhoArquivo: string;
  tamanhoBytes?: number;
  validacaoKeywords?: any;
}
```

### 5.5 Pipeline: `lib/scraper/pipeline.ts` (109 linhas)

```typescript
processarEditalUnico(edital) → boolean
  // 1. Verificar foraDoEscopo
  // 2. baixarELerPDFEdital()
  // 3. delay(3000) — evitar rate limit
  // 4. analisarEditalComIA()
  // 5. saveEdital()

processarFilaDeEditais() → void
  // Busca pendentes e processa cada um (delay 5s)
```

---

## 6. ETAPA 3: ANALISAR COM IA (Detalhamento)

### 6.1 Arquivos

| Arquivo | Linhas | Funcao |
|---------|--------|--------|
| `lib/ai/analyzer.ts` | 279 | Orquestrador de analise |
| `lib/ai/schema-analise.ts` | 82 | Schema Zod da analise |
| `lib/ai/validator.ts` | 455 | Validacao pos-analise |
| `lib/ai/classifier.ts` | 200 | Classificacao preliminar |
| `lib/ai/scoring.ts` | 158 | Pontuacao composta |
| `lib/ai/prompts.ts` | — | Prompts de analise |

### 6.2 Schema de Analise (`AnaliseEditalSchema`)

```typescript
{
  datas: {
    publicacao: string | null,    // DD/MM/YYYY
    abertura: string | null,
    limite: string | null,
    resultado: string | null
  },
  valores: {
    valorMin: number | null,
    valorMax: number | null,
    valorReferencia: string | null,
    moeda: string | null,
    unidade: string | null
  },
  elegibilidade: {
    tiposProponentes: string[],
    requisitos: string[],
    restricoes: string[],
    abrangencia: string,
    areasTematicas: string[],
    focoGeografico: string[]
  },
  documentos: {
    obrigatorios: string[],
    opcionais: string[],
    tecnicos: string[],
    fiscais: string[],
    bancarios: string[],
    totalDocumentos: number | null
  },
  resumo: string,              // ate 5 frases
  objetivo: string,            // 1-2 frases
  criterios: string[],
  avaliacao: {
    criteriosDetalhados: string[],
    penalizacoes: string[],
    pontuacaoMinima: number | null
  },
  contato: string | null,
  consistencia: {
    status: 'ok' | 'duvida' | 'incompleto',
    alertas: string[]
  },
  confiancas: {
    datas: { publicacao, limite, resultado },
    valores: { valorMin, valorMax, valorReferencia },
    tiposProponentes, requisitos, documentos, resumo, criterios
  }
}
```

### 6.3 Dois Modos de Analise

**Modo Completo (padrao):**
- LangChain `ChatOpenAI` com `withStructuredOutput(AnaliseEditalSchema)`
- 1 chamada OpenAI preenche TODOS os campos
- `temperature: 0.1`
- Limite de 60.000 caracteres

**Modo Simplificado (fallback):**
- OpenAI SDK direto com `response_format: json_object`
- Prompt mais simples

### 6.4 Validacao: `lib/ai/validator.ts` (455 linhas)

- **Datas** — formato, sequencia (publicacao < limite < resultado), nao expiradas
- **Valores** — nao negativos, min < max, diferenca razoavel
- **Completude** — campos obrigatorios (titulo >10 chars, descricao >50 chars)
- **Confianca IA** — campos com confianca <70% geram avisos
- **Coerencia** — verifica contradicoes
- `calcularHealthScore()` — score 0-100 para priorizacao
- `validarCampoEspecifico()` — validacao customizada por campo

### 6.5 Classificacao: `lib/ai/classifier.ts` (200 linhas)

- IA: `gpt-4o-mini` com `json_object` response
- Heuristica (fallback): contagem de palavras positivas/negativas
- Score minimo: 60% para ser edital
- `classificarEmLote()` — processa multiplos itens

### 6.6 Pontuacao: `lib/ai/scoring.ts` (158 linhas)

| Fonte | Peso | Detalhe |
|-------|------|---------|
| Whitelist TI | 30% | alta=30, media=22, baixa=12 |
| Blacklist | -35 | se bloqueado |
| PDF encontrado | +20 | PDF real |
| PDF alternativo | +12 | conteudo alternativo |
| Conteudo extenso | +5 | >1500 chars |
| Portal confiavel | +5 | FINEP, CNPq, CAPES, Prosas |
| IA confirmou edital | +40 | ate +40 baseado em confianca |
| IA indicou nao-edital | -30 | — |

**Decisao:**
- `score >= 80` + PDF real → `analise_completa`
- `score >= 60` → `analise_simplificada`
- `score < 60` ou sem PDF → `ignorar`

---

## 7. ETAPA 4: GERAR PROJETO (Detalhamento)

### 7.1 Arquivos

| Arquivo | Linhas | Funcao |
|---------|--------|--------|
| `lib/ai/writer.ts` | 109 | ProposalWriter class |
| `lib/ai/prompts-projeto.ts` | 288 | Prompts Anti-IA |
| `lib/ai/schema-projeto.ts` | 147 | Schema Zod do projeto |
| `lib/ai/tavily-mcp.client.ts` | 83 | Busca web Tavily |
| `app/api/v1/projetos/[id]/gerar/route.ts` | 143 | API de geracao |

### 7.2 ProposalWriter Class

```typescript
class ProposalWriter {
  constructor(model: 'mini' | 'full')  // gpt-4o-mini ou gpt-4o

  async gerarPropostaCompleta(edil, proposal) → PropostaCompleta
  async gerarSecao(secao, edil, proposal, secoesAnteriores?) → SecaoGerada
  async polirTexto(texto, tipo) → string
}

export const proposalWriter = new ProposalWriter('mini');
export const proposalWriterFull = new ProposalWriter('full');
```

### 7.3 Schema de Saida (`PropostaCompleta`)

```typescript
{
  resumoExecutivo: string,        // 5 paragrafos
  justificativa: string,          // 4-5 paragrafos
  objetivos: string,              // JSON { geral, especificos[{cod, descricao, indicador, meta}] }
  metodologia: string,            // 6 paragrafos
  resultadosEsperados: string,    // JSON { curtoPrazo, medioPrazo, longoPrazo }
  cronograma: string,
  orcamentoDetalhado: string,     // JSON { administracao, divulgacao, equipe, materiais, outros, total }
  valorSolicitado: number,
  prazoMeses: number,
  equipe: string,                 // JSON [{ nome, funcao, qualificacao, dedicacao }]
  criteriosAtendidos: string[],
  criteriosPendentes: string[],
  scoreCompliance: number,
  fontes: string[]
}
```

### 7.4 Prompt Anti-IA (`prompts-projeto.ts`)

**Formato:** "ATUE COMO" especialista senior em formulacao de projetos

**Elementos do prompt:**
- Lista de 22 palavras proibidas (cliches IA): "mergulhe", "jornada", "sinergia", "catalisador", etc.
- DADOS DE BUSCA do Tavily (fontes reais para fundamentacao)
- CONTEXTO DO EDITAL completo (titulo, orgao, valor, objetivo, criterios)
- PROPOSTA DO USUARIO (titulo, descricao, area, proposta detalhada)

**REQUISITOS MINIMOS OBRIGATORIOS por secao:**
- **Resumo Executivo:** exatamente 5 paragrafos (3-4 frases cada)
- **Justificativa:** 4-5 paragrafos com citacoes [1], [2]
- **Objetivos:** JSON com objetivo geral + 4-5 especificos (formato SMARTER)
- **Metodologia:** 6 paragrafos
- **Resultados:** 3 horizontes temporais com indicadores e metas
- **Orcamento:** 5 categorias (administracao max 15%), total = soma
- **Equipe:** 3-5 membros com funcoes distintas

**DIRETRIZES ANTI-IA:**
1. Variacao sintatica (frases curtas + compostas)
2. Tom impessoal e tecnico (3a pessoa)
3. Proibicao absoluta de cliches
4. Objetividade (sem introducoes amigaveis)

### 7.5 Tavily MCP Client (`tavily-mcp.client.ts`)

```typescript
buscarDadosProjetoMCP(tema, areaAtuacao?) → {
  results: [{ title, url, content }],
  query: string
}
```

- Query: `tema + areaAtuacao + "dados estatisticas 2024 2025 Brasil"`
- Ate 5 resultados
- Se falhar, continua sem search

### 7.6 API de Geracao (`/api/v1/projetos/[id]/gerar`)

1. Busca projeto e edital associado
2. Valida que edital tem analise IA
3. Monta `EditalContext` normalizando arrays
4. Monta `UserProposal` com dados do usuario
5. Chama `writer.gerarPropostaCompleta()`
6. Salva com status `'gerado'` e incrementa versao

---

## 8. Banco de Dados (SQLite + Drizzle ORM)

### 8.1 Configuracao
- **Localizacao:** `data/capta.db`
- **Driver:** better-sqlite3
- **ORM:** Drizzle ORM
- **Config:** `lib/database/db.ts`
- **Schema:** `lib/database/schema.ts`

### 8.2 Tabelas

#### `editais` (tabela principal — 50+ campos)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | TEXT PK | ID unico (ex: prosas-123) |
| `titulo` | TEXT NOT NULL | Titulo do edital |
| `orgao` | TEXT NOT NULL | Orgao responsavel |
| `valor` | TEXT | Valor estimado |
| `valorMin` | REAL | Valor minimo (BRL) |
| `valorMax` | REAL | Valor maximo (BRL) |
| `dataPublicacao` | TEXT | Data de publicacao |
| `dataAbertura` | TEXT | Data de abertura |
| `dataLimite` | TEXT NOT NULL | Data limite inscricao |
| `dataResultado` | TEXT | Data de resultado |
| `status` | TEXT | Aberto/Prorrogado/Em Analise/Fechado |
| `statusAnalise` | TEXT | pendente/pdf_baixado/analisado/sem_pdf/descartado/erro |
| `link` | TEXT NOT NULL | Link do edital |
| `pdfUrl` | TEXT | URL do PDF |
| `pdfPath` | TEXT | Caminho do PDF local |
| `conteudoCompleto` | TEXT | Texto extraido do PDF |
| `fonteConteudo` | TEXT | pdf_s3/pdf_link/html_link/descricao_api/mock/sem_pdf |
| `tecnologiaFoco` | TEXT | Categoria de tecnologia |
| `tipoFerramenta` | TEXT | Tipo de ferramenta |
| `scoreRelevancia` | INTEGER | Score de relevancia (0-100) |
| `scoreConfiancaIa` | INTEGER | Confianca da IA (0-100) |
| `validadoPorIa` | BOOLEAN | Se foi validado por IA |
| `foraDoEscopo` | BOOLEAN | Se esta fora do escopo |
| `scorePontuacao` | INTEGER | Score composto |
| `nivelPontuacao` | TEXT | baixo/medio/alto |
| `confiancaPorCampo` | TEXT | JSON com confianca por campo |
| `descricao` | TEXT | Descricao completa |
| `arquivosAnexos` | TEXT | JSON de anexos |
| `tipoProponente` | TEXT | JSON array |
| `areasTematicas` | TEXT | JSON array |
| `codigo` | TEXT UNIQUE | Codigo EDT-001 |
| `deletedAt` | TEXT | Soft-delete |

#### `analise_ia`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `editalId` | TEXT FK | Referencia ao edital |
| `resumo` | TEXT | Resumo do edital |
| `objetivo` | TEXT | Objetivo principal |
| `elegibilidade` | TEXT | Elegibilidade |
| `contatoEdital` | TEXT | Canal de contato |
| `scoreAdequacao` | INTEGER | Score de adequacao |

#### `analise_requisitos`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `analiseId` | INTEGER FK | Referencia a analise |
| `requisito` | TEXT NOT NULL | Descricao do requisito |
| `ordem` | INTEGER | Ordem na lista |

#### `analise_itens_financiaveis`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `analiseId` | INTEGER FK | Referencia a analise |
| `item` | TEXT NOT NULL | Item financiavel |
| `ordem` | INTEGER | Ordem na lista |

#### `analise_documentos`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `analiseId` | INTEGER FK | Referencia a analise |
| `documento` | TEXT NOT NULL | Documento necessario |
| `ordem` | INTEGER | Ordem na lista |

#### `analise_criterios`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `analiseId` | INTEGER FK | Referencia a analise |
| `criterio` | TEXT NOT NULL | Criterio de avaliacao |
| `ordem` | INTEGER | Ordem na lista |

#### `analise_pontos_fracos`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `analiseId` | INTEGER FK | Referencia a analise |
| `pontoFraco` | TEXT NOT NULL | Ponto fraco identificado |
| `ordem` | INTEGER | Ordem na lista |

#### `palavras_chave`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `editalId` | TEXT FK | Referencia ao edital |
| `palavra` | TEXT NOT NULL | Palavra-chave |
| `frequencia` | INTEGER DEFAULT 1 | Frequencia |

#### `arquivos_anexos`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `editalId` | TEXT FK | Referencia ao edital |
| `descricao` | TEXT | Descricao do arquivo |
| `url` | TEXT | URL do arquivo |
| `tipo` | TEXT | Tipo/extensao |
| `caminhoLocal` | TEXT | Caminho local |
| `tamanhoBytes` | INTEGER | Tamanho em bytes |
| `hashArquivo` | TEXT | Hash do arquivo |

#### `motivos_pontuacao`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `editalId` | TEXT FK | Referencia ao edital |
| `motivo` | TEXT NOT NULL | Motivo da pontuacao |

#### `usuarios`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | TEXT PK | UUID |
| `nome` | TEXT NOT NULL | Nome completo |
| `email` | TEXT NOT NULL UNIQUE | Email login |
| `password` | TEXT NOT NULL | Hash bcrypt |
| `role` | TEXT DEFAULT 'leitor' | admin/editor/leitor |
| `status` | TEXT DEFAULT 'ativo' | ativo/inativo |

#### `projetos`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | TEXT PK | UUID |
| `editalId` | TEXT FK NOT NULL | Edital associado |
| `titulo` | TEXT NOT NULL | Titulo do projeto |
| `descricao` | TEXT | Descricao |
| `areaAtuacao` | TEXT | Area de atuacao |
| `propostaUsuario` | TEXT | Proposta livre do usuario |
| `resumoExecutivo` | TEXT | Resumo gerado por IA |
| `justificativa` | TEXT | Justificativa gerada |
| `objetivos` | TEXT | Objetivos (JSON) |
| `metodologia` | TEXT | Metodologia gerada |
| `resultadosEsperados` | TEXT | Resultados (JSON) |
| `cronograma` | TEXT | Cronograma |
| `orcamentoDetalhado` | TEXT | Orcamento (JSON) |
| `valorSolicitado` | REAL | Valor solicitado |
| `prazoMeses` | INTEGER | Prazo em meses |
| `equipe` | TEXT | Equipe (JSON array) |
| `criteriosAtendidos` | TEXT | Criterios OK (JSON) |
| `criteriosPendentes` | TEXT | Criterios pendentes (JSON) |
| `scoreCompliance` | INTEGER | Score 0-100 |
| `status` | TEXT | rascunho/em_geracao/revisando/finalizado |
| `versao` | INTEGER DEFAULT 1 | Versao do projeto |
| `fontes` | TEXT | Fontes utilizadas (JSON) |

#### `areas_tematicas`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `nome` | TEXT NOT NULL UNIQUE | Nome da area |

#### `tipos_proponente`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | INTEGER PK | Auto-increment |
| `nome` | TEXT NOT NULL UNIQUE | Nome do tipo |

### 8.3 Relacionamentos

```
editais 1→1 analise_ia
editais 1→N palavras_chave
editais 1→N arquivos_anexos
editais 1→N motivos_pontuacao
analise_ia 1→N analise_requisitos
analise_ia 1→N analise_itens_financiaveis
analise_ia 1→N analise_documentos
analise_ia 1→N analise_criterios
analise_ia 1→N analise_pontos_fracos
editais 1→N projetos
```

---

## 9. API Routes

### 9.1 Editais

| Metodo | Rota | Descricao |
|--------|------|-----------|
| `GET` | `/api/editais` | Listar editais com filtros |
| `POST` | `/api/editais/busca` | Buscar editais nos portais |
| `POST` | `/api/editais/analisar` | Analisar edital com IA |
| `POST` | `/api/editais/carregar-downloads` | Carregar PDFs da pasta |
| `POST` | `/api/editais/revisar` | Aprovar/rejeitar edital |
| `POST` | `/api/editais/notificar` | Enviar notificacao |
| `DELETE` | `/api/editais/deletar` | Deletar edital |

### 9.2 Jobs

| Metodo | Rota | Descricao |
|--------|------|-----------|
| `POST` | `/api/jobs/run-weekly-scan` | Varredura semanal completa |

### 9.3 Projetos (v1)

| Metodo | Rota | Descricao |
|--------|------|-----------|
| `GET` | `/api/v1/projetos` | Listar projetos |
| `POST` | `/api/v1/projetos` | Criar projeto |
| `GET` | `/api/v1/projetos/[id]` | Detalhes do projeto |
| `PUT` | `/api/v1/projetos/[id]` | Atualizar projeto |
| `DELETE` | `/api/v1/projetos/[id]` | Deletar projeto |
| `POST` | `/api/v1/projetos/[id]/gerar` | Gerar proposta com IA |
| `GET` | `/api/v1/projetos/[id]/export` | Exportar PDF/Markdown |

### 9.4 Usuarios (v1)

| Metodo | Rota | Descricao |
|--------|------|-----------|
| `POST` | `/api/v1/usuarios/cadastrar` | Cadastro |
| `POST` | `/api/v1/usuarios/login` | Login |
| `GET` | `/api/v1/usuarios` | Listar todos |
| `GET` | `/api/v1/usuarios/[id]` | Buscar por ID |
| `PUT` | `/api/v1/usuarios/[id]` | Atualizar |
| `DELETE` | `/api/v1/usuarios/[id]` | Deletar |

---

## 10. Sistema de Autenticacao

### Fluxo de Login
1. Usuario envia email e password para `POST /api/v1/usuarios/login`
2. Service valida credenciais com `bcrypt.compare()`
3. Se valido, retorna dados do usuario e define cookie `usuario_logado`
4. Cookie e HTTP-only e seguro em producao

### Middleware (`middleware.ts`)
- **Rotas publicas:** `/`, `/login`, `/api/v1/usuarios/cadastrar`, `/api/v1/usuarios/login`
- **Rotas protegidas:** Todas as outras
- **Behavior:** Redireciona para `/login` (paginas) ou retorna 401 (API)

### Seed Admin
```bash
npx tsx lib/database/seed.ts
# Email: admin@capta.com
# Senha: admin123
```

---

## 11. Design System

### Modo Claro e Escuro (Theme Toggle)
O sistema suporta nativamente os temas Claro e Escuro.
- O modo claro utiliza as variaveis de cores e superficies definidas no seletor `:root` em `app/globals.css`.
- O modo escuro sobrepoe essas variaveis atraves do seletor `.dark`.
- A alternancia de temas e disponibilizada ao usuario pelo componente `ThemeToggleIcon` (localizado em `components/providers/theme-toggle.tsx`), o qual esta integrado diretamente na `TopBar`.

### Design Tokens (`app/globals.css`)

| Token | Valor | Uso |
|-------|-------|-----|
| `--color-primary` | `#2563eb` | Cor principal, botoes, links |
| `--color-primary-hover` | `#1d4ed8` | Hover do primario |
| `--color-secondary` | `#64748b` | Neutros secundarios |
| `--color-success` | `#10b981` | Status positivo |
| `--color-warning` | `#f59e0b` | Atencao |
| `--color-danger` | `#ef4444` | Erros, exclusao |
| `--spacing-xs` a `2xl` | 0.25rem a 3rem | Espacamento |
| `--radius-sm` a `lg` | 0.25rem a 0.75rem | Bordas |
| `--shadow-sm` a `lg` | Sombras CSS | Elevacao |

### Classes Utilitarias
- **Flexbox:** `.flex`, `.flex-col`, `.items-center`, `.justify-between`, `.gap-sm/md/lg`
- **Grid:** `.grid`, `.grid-cols-1/2/3/4`, `.md:grid-cols-2`, `.lg:grid-cols-3/4`
- **Espacamento:** `.p-sm/md`, `.px-md`, `.py-sm`, `.mb-md`, `.mt-sm`
- **Tipografia:** `.text-xs` a `.text-3xl`, `.font-medium/semibold/bold`
- **Estilos:** `.bg-white`, `.bg-gray-50`, `.rounded-lg`, `.border`, `.shadow-md`

---

## 12. Componentes UI

### Button (`components/ui/button.tsx`)
- `variant`: default (fundo primario, garantindo contraste), outline (borda transparente, cor do texto dependente do contexto), ghost (transparente)
- `size`: default (medio), sm (pequeno), lg (destaque)
- Notas de Design: Botoes de acao de alto impacto ou Call to Actions principais (como os botoes "Analisar" ou "Ver Catalogo IA") devem utilizar a variante `default` com o token `--color-primary` para background e texto `white`, destacando a acao e garantindo total legibilidade em ambos os modos de tema.

### Card (`components/ui/card.tsx`)
- Subcomponentes: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter

### Badge (`components/ui/badge.tsx`)
- `variant`: default (azul), success (verde), warning (laranja), danger (vermelho)

### Input (`components/ui/input.tsx`)
- Campo de texto padronizado com transicoes de foco

---

## 13. Mapa de Arquivos por Funcao

### Buscar Edital
| Arquivo | Funcao |
|---------|--------|
| `scripts/buscar-editais.sh` | Ponto de entrada shell |
| `lib/scraper/fetcher.ts` | Orquestrador de busca |
| `lib/scraper/prosas-scraper.ts` | Scraper Prosas |
| `lib/scraper/capta-scraper.ts` | Scraper Capta |
| `lib/scraper/config.ts` | Config de portais |
| `lib/scraper/filtros-ti.ts` | Whitelist/Blacklist/OpenAI |
| `app/api/jobs/run-weekly-scan/route.ts` | API endpoint |
| `lib/jobs/scheduler.ts` | Cron scheduler |

### Baixar PDF
| Arquivo | Funcao |
|---------|--------|
| `lib/scraper/pdf-downloader.ts` | Download em cascata |
| `lib/scraper/pdf-extractor.ts` | Extracao de URLs PDF |
| `lib/scraper/llamaparse-extractor.ts` | Extracao via LlamaParse |
| `lib/scraper/utils/path-utils.ts` | Utilitarios de caminho |

### Analisar com IA
| Arquivo | Funcao |
|---------|--------|
| `lib/ai/analyzer.ts` | Orquestrador de analise |
| `lib/ai/schema-analise.ts` | Schema Zod da analise |
| `lib/ai/classifier.ts` | Classificacao preliminar |
| `lib/ai/validator.ts` | Validacao pos-analise |
| `lib/ai/scoring.ts` | Pontuacao composta |
| `lib/ai/prompts.ts` | Prompts de analise |
| `lib/scraper/pipeline.ts` | Pipeline download+analise |

### Gerar Projeto
| Arquivo | Funcao |
|---------|--------|
| `lib/ai/writer.ts` | ProposalWriter class |
| `lib/ai/prompts-projeto.ts` | Prompts Anti-IA |
| `lib/ai/schema-projeto.ts` | Schema Zod do projeto |
| `lib/ai/tavily-mcp.client.ts` | Busca web Tavily |
| `app/api/v1/projetos/[id]/gerar/route.ts` | API de geracao |
| `app/api/v1/projetos/route.ts` | CRUD projetos |
| `app/api/v1/projetos/[id]/export/route.ts` | Export PDF/Markdown |

---

## 14. Comandos Uteis

```bash
# Desenvolvimento
npm run dev                  # Inicia servidor de desenvolvimento

# Build
npm run build                # Gera build de producao

# Lint
npm run lint                 # Verifica erros de lint

# Testes
npm run test                 # Roda testes uma vez
npm run test:watch           # Roda testes em watch mode

# Banco de Dados
npx tsx lib/database/seed.ts # Cria usuario admin

# Busca de Editais
./scripts/buscar-editais.sh           # Execucao manual
./scripts/buscar-editais.sh --verbose # Com logs detalhados
./scripts/buscar-editais.sh --dry-run # Simulacao

# Cron (toda segunda as 08:00)
0 8 * * 1 cd /caminho/captaMais && ./scripts/buscar-editais.sh >> logs/cron.log 2>&1
```

---

## 15. Variaveis de Ambiente (`.env.local`)

| Variavel | Uso |
|----------|-----|
| `OPENAI_API_KEY` | Chave da API OpenAI |
| `OPENAI_MODEL` | Modelo padrao (gpt-4o-mini) |
| `TAVILY_API_KEY` | Chave da API Tavily |
| `LLAMACLOUD_API_KEY` | Chave do LlamaParse |
| `PROSAS_EMAIL` | Email do Prosas |
| `PROSAS_PASSWORD` | Senha do Prosas |
| `SCAN_TOKEN` | Token para varredura |
| `NEXT_PUBLIC_API_URL` | URL da API |

---

## 16. Diretrizes de Codificacao

> **Preservar padroes esteticos** — Cantos arredondados, sombras suaves, micro-interacoes via CSS.

> **Evitar TailwindCSS** — Usar classes utilitarias nativas do `globals.css`.

> **Sem placeholders genericos** — Usar mocks realistas de editais brasileiros.

> **Senhas e seguranca** — Sempre bcrypt com 10+ rounds. Nunca texto plano.

> **Padrao Repository/Service** — Repository = acesso a dados, Service = logica de negocio, Route = HTTP.
