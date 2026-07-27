# Pipeline Estruturado

Esta pasta contém o ETL em Python usado para coletar, organizar, tratar, validar e consolidar dados públicos estruturados do Observatório de Dados Públicos.

O projeto começou com dados ligados à Previdência e ao orçamento público, mas sua arquitetura permite incorporar progressivamente outras bases. A versão atual já integra dados do IBGE, da PNAD Contínua, do IPEAData e do SIOP, preservando os dados originais e produzindo tabelas analíticas nas camadas `bronze`, `silver` e `gold`.

## Objetivo

O objetivo do pipeline é oferecer um fluxo reproduzível de ETL para dados públicos estruturados.

ETL significa:

- **Extract:** coletar dados em APIs, bibliotecas e serviços públicos;
- **Transform:** limpar, converter, padronizar e validar os dados coletados;
- **Load:** salvar os resultados em formatos adequados para análise, integração e consulta.

O fluxo foi dividido em três camadas:

```text
data/bronze
data/silver
data/gold
```

- A camada `bronze` preserva os retornos próximos ao formato original.
- A camada `silver` organiza os dados em estruturas padronizadas.
- A camada `gold` produz tabelas consolidadas e indicadores prontos para análise.

## Fontes integradas

### IBGE e PNAD Contínua

Os dados do IBGE e da PNAD Contínua são consultados por meio da API do SIDRA.

A versão atual trabalha com indicadores relacionados a:

- população do Brasil;
- Produto Interno Bruto nominal;
- Índice Nacional de Preços ao Consumidor Amplo;
- estrutura etária;
- população com 60 anos ou mais;
- força de trabalho;
- população ocupada e desocupada;
- taxa de desocupação;
- quantidade de pessoas em ocupações informais;
- taxa de informalidade;
- quantidade de pessoas ocupadas que contribuem para a Previdência;
- percentual de ocupados que contribuem para a Previdência.

Os produtos anuais do IBGE utilizam, como regra geral, o intervalo de 2015 a 2026. A existência de uma linha para determinado exercício não significa que todos os indicadores estejam disponíveis. Valores ausentes são preservados como nulos e recebem um status de período.

Os status usados são:

```text
completo
parcial
indisponivel
```

O pipeline não cria valores artificiais para preencher anos sem informação oficial.

### IPEAData

O IPEAData é usado para consultar séries macroeconômicas.

As séries atualmente cadastradas são:

| Dataset | Código da série | Descrição |
|---|---|---|
| `ipea_ipca_indice_mensal` | `PRECOS12_IPCA12` | Número-índice mensal do IPCA |
| `ipea_pib_real_trimestral` | `PAN4_PIBPMG4` | Variação real interanual do PIB trimestral |

Na coleta validada em julho de 2026:

- o IPCA mensal possui observações de dezembro de 1979 a junho de 2026;
- o PIB real trimestral possui observações do primeiro trimestre de 1997 ao quarto trimestre de 2025.

Esses períodos podem avançar em novas execuções, conforme a atualização da API.

A série `PAN4_PIBPMG4` não representa um valor monetário do PIB. Ela representa a variação percentual de cada trimestre em relação ao mesmo trimestre do ano anterior.

### SIOP

O SIOP é usado para consultar a Lei Orçamentária Anual e a execução orçamentária por meio da biblioteca `orcamentobr`.

A versão atual consulta os exercícios de 2015 a 2026.

Cada exercício é coletado separadamente, preservando todas as dimensões configuradas da LOA na camada `bronze` e produzindo recortes consolidados na camada `gold`.

Entre as dimensões coletadas estão:

```text
esfera
orgao
unidade orcamentaria
funcao
subfuncao
programa
acao
plano orcamentario
subtitulo
categoria economica
grupo de natureza da despesa
modalidade de aplicacao
elemento de despesa
fonte de recursos
identificador de uso
resultado primario
```

Entre os valores coletados estão:

```text
PLOA
dotacao inicial
dotacao atualizada
valor empenhado
valor liquidado
valor pago
```

## Estrutura da pasta

```text
pipeline_estruturado/
├── config/
│   └── sources.json
├── data/
│   ├── bronze/
│   │   ├── ibge/
│   │   ├── ipea/
│   │   ├── pnad/
│   │   └── siop/
│   │       └── execucao_orcamentaria/
│   ├── silver/
│   │   ├── ibge/
│   │   ├── ipea/
│   │   ├── pnad/
│   │   └── siop/
│   │       └── execucao_orcamentaria/
│   └── gold/
│       ├── ibge/
│       ├── ipea/
│       ├── siop/
│       ├── catalogo_series.csv
│       ├── series_consolidadas.csv
│       └── series_consolidadas.parquet
├── docs/
│   ├── COMO_PROGRAMAR_ETL.md
│   └── LEGENDA_PREVIDENCIA_PUBLICA.md
├── logs/
├── notebooks/
├── outputs/
├── scripts/
│   └── run_etl.py
├── src/
│   └── observatorio_etl/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── http_client.py
│       ├── ibge.py
│       ├── ipea_gold.py
│       ├── ipeadata.py
│       ├── paths.py
│       ├── runner.py
│       ├── sidra.py
│       ├── siop.py
│       └── storage.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Configuração das fontes

O arquivo principal de configuração é:

```text
config/sources.json
```

Cada entrada informa:

- nome do dataset;
- tipo da fonte;
- instituição ou domínio de origem;
- tema;
- parâmetros específicos de consulta;
- regras opcionais para construção da camada `gold`.

Os tipos atualmente reconhecidos são:

```text
sidra
ipeadata
siop
```

A ideia é permitir que novas consultas sejam cadastradas sem reescrever toda a estrutura do pipeline.

## Camada bronze

A camada `bronze` guarda os dados brutos ou próximos ao formato original recebido das fontes.

Ela permite:

- conferir o retorno da API ou biblioteca;
- reproduzir transformações;
- investigar problemas sem realizar uma nova coleta;
- preservar os metadados usados na interpretação das séries.

### SIDRA

Para fontes SIDRA, podem ser salvos:

```text
consulta.json
metadados.json
bruto.json
bruto.csv
```

### IPEAData

Para cada série do IPEAData, são salvos:

```text
metadata.json
values.json
values.csv
```

Exemplo:

```text
data/bronze/ipea/inflacao/
├── ipea_ipca_indice_mensal_metadata.json
├── ipea_ipca_indice_mensal_values.json
└── ipea_ipca_indice_mensal_values.csv
```

### SIOP

Para cada exercício, são salvos:

- um arquivo JSON com os parâmetros usados;
- um arquivo CSV com o retorno bruto completo.

Exemplo:

```text
data/bronze/siop/execucao_orcamentaria/
├── siop_loa_completa_2015_consulta.json
├── siop_loa_completa_2015_bruto.csv
├── ...
├── siop_loa_completa_2026_consulta.json
└── siop_loa_completa_2026_bruto.csv
```

## Camada silver

A camada `silver` contém os dados tratados e padronizados.

As transformações incluem:

- padronização de nomes de colunas;
- conversão de valores numéricos;
- identificação da fonte, tema e dataset;
- derivação de exercício, mês e trimestre;
- registro da data e hora da coleta;
- preservação do valor original quando aplicável;
- organização de classificações e dimensões.

Os arquivos são salvos em CSV e Parquet.

### Estrutura comum das séries

Os dados do SIDRA e do IPEAData utilizam uma estrutura longa com campos como:

```text
fonte
tema
dataset
codigo_serie
periodicidade
periodo_codigo
periodo_nome
exercicio
mes
trimestre
territorio_codigo
territorio_nome
variavel_codigo
variavel_nome
unidade_codigo
unidade
valor_original
valor
coletado_em
extra_json
```

Nem todas as fontes fornecem todos os campos. Quando a informação não existe na origem, ela permanece nula.

### SIOP tratado

Os arquivos tratados do SIOP preservam as dimensões da LOA e os valores monetários convertidos.

```text
data/silver/siop/execucao_orcamentaria/
├── siop_loa_completa_2015.csv
├── siop_loa_completa_2015.parquet
├── ...
├── siop_loa_completa_2026.csv
└── siop_loa_completa_2026.parquet
```

## Camada gold

A camada `gold` contém produtos analíticos e consolidados.

### Catálogo de séries

O catálogo registra as fontes executadas:

```text
data/gold/catalogo_series.csv
```

Estrutura:

```text
dataset
tipo
fonte
tema
estrutura
linhas
atualizado_em
```

### Séries consolidadas

Quando todas as fontes são executadas em uma única chamada, as séries temporais são reunidas em:

```text
data/gold/series_consolidadas.csv
data/gold/series_consolidadas.parquet
```

Esses arquivos possuem caráter técnico e servem como ponto de entrada para consultas gerais. Para análises específicas, devem ser preferidos os produtos temáticos das pastas `ibge`, `ipea` e `siop`.

### Produtos Gold do IBGE

Os produtos anuais ficam em:

```text
data/gold/ibge/
```

São gerados em CSV e Parquet:

| Produto | Finalidade |
|---|---|
| `populacao_brasil_por_ano` | População anual do Brasil |
| `pib_nominal_brasil_por_ano` | PIB nominal anual |
| `ipca_brasil_por_ano` | Indicadores anuais do IPCA |
| `estrutura_etaria_brasil_por_ano` | População total da PNAD e população com 60 anos ou mais |
| `mercado_trabalho_brasil_por_ano` | Força de trabalho, ocupação, desocupação e informalidade |
| `contribuicao_previdenciaria_brasil_por_ano` | Quantidade e percentual de ocupados contribuintes |
| `nucleo_ibge_anual` | Integração anual dos principais indicadores do IBGE e da PNAD |

Exemplo:

```text
data/gold/ibge/
├── populacao_brasil_por_ano.csv
├── populacao_brasil_por_ano.parquet
├── pib_nominal_brasil_por_ano.csv
├── pib_nominal_brasil_por_ano.parquet
├── ipca_brasil_por_ano.csv
├── ipca_brasil_por_ano.parquet
├── estrutura_etaria_brasil_por_ano.csv
├── estrutura_etaria_brasil_por_ano.parquet
├── mercado_trabalho_brasil_por_ano.csv
├── mercado_trabalho_brasil_por_ano.parquet
├── contribuicao_previdenciaria_brasil_por_ano.csv
├── contribuicao_previdenciaria_brasil_por_ano.parquet
├── nucleo_ibge_anual.csv
└── nucleo_ibge_anual.parquet
```

O arquivo `nucleo_ibge_anual` facilita análises que combinam demografia, atividade econômica, inflação, mercado de trabalho, informalidade e contribuição previdenciária.

### Produtos Gold do IPEAData

Os produtos ficam em:

```text
data/gold/ipea/
```

São gerados em CSV e Parquet.

#### `ipca_brasil_por_ano`

Contém:

```text
exercicio
ipca_indice_medio
ipca_indice_fim_periodo
ipca_variacao_acumulada_calculada
meses_disponiveis
status_periodo
```

A variação acumulada é calculada por:

```text
(indice do ultimo mes disponivel do ano
÷ indice de dezembro do ano anterior - 1) × 100
```

Quando o ano possui 12 meses, o status é `completo`. Quando possui entre 1 e 11 meses, o status é `parcial`.

O primeiro ano disponível pode ter a variação acumulada nula por não existir dezembro do ano anterior na série.

#### `pib_real_variacao_interanual_trimestral`

Contém:

```text
exercicio
trimestre
periodo
taxa_variacao_pib_real_interanual
unidade
status_periodo
```

Cada linha representa um trimestre. A série não é somada nem transformada em PIB anual monetário.

Exemplo:

```text
data/gold/ipea/
├── ipca_brasil_por_ano.csv
├── ipca_brasil_por_ano.parquet
├── pib_real_variacao_interanual_trimestral.csv
└── pib_real_variacao_interanual_trimestral.parquet
```

### Produtos Gold do SIOP

Os produtos consolidados ficam em:

```text
data/gold/siop/
```

São produzidos:

```text
data/gold/siop/loa_total_por_ano.csv
data/gold/siop/loa_previdencia_publica_por_ano.csv
```

Os dois arquivos possuem a mesma estrutura básica:

```text
fonte
tema
dataset
exercicio
valor_empenhado
valor_liquidado
valor_pago
coletado_em
```

#### `loa_total_por_ano.csv`

Contém uma linha por exercício.

Cada linha representa a soma de todos os registros da LOA do respectivo exercício, sem recorte por função, órgão, programa ou outra dimensão.

#### `loa_previdencia_publica_por_ano.csv`

Contém uma linha por exercício.

Cada linha representa a soma dos registros classificados na função:

```text
09 - Previdencia Social
```

## Critério do recorte de Previdência Pública

O recorte considera todas as linhas da LOA classificadas na função 09.

As subfunções associadas são:

| Código | Descrição |
|---|---|
| 271 | Previdência Básica |
| 272 | Previdência do Regime Estatutário |
| 273 | Previdência Complementar |
| 274 | Previdência Especial |

Todas as linhas classificadas na função 09 são incluídas, independentemente do órgão, unidade orçamentária, programa, ação, plano orçamentário, natureza da despesa, fonte de recursos ou outra categoria.

Não são incluídas linhas de outras funções apenas porque o nome do órgão, programa ou ação contém expressões como `INSS`, `previdência`, `aposentadoria` ou `pensão`.

Esse critério evita decisões baseadas apenas em palavras e torna o recorte reproduzível entre os exercícios.

A explicação metodológica completa fica registrada em:

```text
docs/LEGENDA_PREVIDENCIA_PUBLICA.md
```

## Principais módulos do código

### `scripts/run_etl.py`

Ponto de entrada para execução pelo terminal.

### `src/observatorio_etl/cli.py`

Define os comandos da interface de linha de comando.

### `src/observatorio_etl/config.py`

Lê e valida o arquivo `config/sources.json`.

### `src/observatorio_etl/http_client.py`

Centraliza as requisições HTTP e as políticas de tentativa.

### `src/observatorio_etl/sidra.py`

Consulta a API do SIDRA e transforma os retornos em estrutura longa.

### `src/observatorio_etl/ibge.py`

Constrói os produtos Gold anuais do IBGE e da PNAD.

Entre suas responsabilidades estão:

- seleção das variáveis oficiais;
- conversão de unidades;
- consolidação anual;
- preservação de valores ausentes;
- atribuição dos status de disponibilidade;
- integração do núcleo anual do IBGE.

### `src/observatorio_etl/ipeadata.py`

Consulta metadados e valores do IPEAData.

Também padroniza:

- periodicidade;
- exercício;
- mês;
- trimestre;
- código territorial;
- unidade;
- valor original;
- valor numérico.

### `src/observatorio_etl/ipea_gold.py`

Constrói os produtos Gold do IPEAData:

- IPCA anual derivado do número-índice mensal;
- variação real interanual do PIB por trimestre.

### `src/observatorio_etl/siop.py`

Consulta, valida e transforma os dados do SIOP.

Entre suas responsabilidades estão:

1. validar os parâmetros da consulta;
2. consultar um exercício por vez;
3. repetir a tentativa em falhas temporárias;
4. padronizar as colunas;
5. converter valores monetários;
6. preservar as dimensões da LOA;
7. construir o total anual;
8. filtrar a função 09;
9. construir o recorte anual da Previdência Pública.

### `src/observatorio_etl/runner.py`

Coordena a execução do ETL.

O módulo:

1. lê as fontes cadastradas;
2. seleciona as fontes solicitadas;
3. chama o coletor correspondente;
4. salva os dados na camada `bronze`;
5. transforma e salva os dados na camada `silver`;
6. gera os produtos Gold do IBGE;
7. gera os produtos Gold do IPEAData;
8. gera os consolidados do SIOP;
9. atualiza o catálogo de séries;
10. gera as séries consolidadas quando todas as fontes são executadas.

### `src/observatorio_etl/paths.py`

Organiza os caminhos principais do projeto.

### `src/observatorio_etl/storage.py`

Salva dados em JSON, CSV e Parquet.

## Instalação

Acesse a pasta:

```bash
cd pipeline_estruturado
```

Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

Ative no Linux:

```bash
source .venv/bin/activate
```

Ative no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Entre as principais dependências estão:

```text
requests
pandas
pyarrow
orcamentobr
```

## Execução

### Listar as fontes

```bash
python scripts/run_etl.py list-sources
```

### Executar todas as fontes

```bash
python scripts/run_etl.py run
```

A execução completa pode levar mais tempo por causa das consultas anuais do SIOP.

### Executar uma fonte específica

```bash
python scripts/run_etl.py run \
  --source ipea_ipca_indice_mensal
```

### Executar várias fontes específicas

O parâmetro `--source` pode ser repetido:

```bash
python scripts/run_etl.py run \
  --source ipea_ipca_indice_mensal \
  --source ipea_pib_real_trimestral
```

Outro exemplo:

```bash
python scripts/run_etl.py run \
  --source pnad_condicao_trabalho_brasil \
  --source pnad_taxa_desocupacao_brasil
```

## Fluxo da execução

Quando o comando `run` é executado, o pipeline:

1. lê `config/sources.json`;
2. seleciona todas as fontes ou apenas as fontes informadas;
3. identifica o tipo de cada fonte;
4. realiza a coleta;
5. salva os dados originais na camada `bronze`;
6. padroniza os dados;
7. salva CSV e Parquet na camada `silver`;
8. gera produtos Gold específicos;
9. atualiza `catalogo_series.csv`;
10. gera `series_consolidadas` quando todas as fontes são processadas.

## Como adicionar uma nova fonte

Edite:

```text
config/sources.json
```

### Exemplo SIDRA

```json
{
  "name": "ibge_populacao_estimada_brasil",
  "type": "sidra",
  "source": "ibge",
  "theme": "populacao",
  "table": "6579",
  "variable": "9324",
  "period": "all",
  "territorial_level": "1",
  "localities": "all",
  "decimals": "0",
  "periodicity": "anual",
  "gold_builder": "populacao_estimada",
  "gold_start_year": 2015,
  "gold_end_year": 2026
}
```

O parâmetro `gold_builder` identifica o construtor usado na consolidação anual do IBGE.

### Exemplo IPEAData

```json
{
  "name": "ipea_ipca_indice_mensal",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "inflacao",
  "series_code": "PRECOS12_IPCA12"
}
```

### Exemplo SIOP

```json
{
  "name": "siop_loa_completa_2015_2026",
  "type": "siop",
  "source": "siop",
  "theme": "execucao_orcamentaria",
  "exercicios": [
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026
  ],
  "esfera": true,
  "orgao": true,
  "uo": true,
  "funcao": true,
  "sub_funcao": true,
  "programa": true,
  "acao": true,
  "plano_orcamentario": true,
  "subtitulo": true,
  "categoria_economica": true,
  "gnd": true,
  "modalidade_aplicacao": true,
  "elemento_despesa": true,
  "fonte": true,
  "id_uso": true,
  "resultado_primario": true,
  "valor_ploa": true,
  "valor_loa": true,
  "valor_loa_mais_credito": true,
  "valor_empenhado": true,
  "valor_liquidado": true,
  "valor_pago": true,
  "inclui_descricoes": true,
  "detalhe_maximo": true,
  "ignore_secure_certificate": true,
  "timeout": 600000,
  "print_url": false
}
```

Depois de editar o arquivo:

```bash
python scripts/run_etl.py list-sources
```

Em seguida, execute a fonte cadastrada ou o pipeline completo.

## Validações aplicadas

As validações atuais incluem:

- datas convertíveis;
- valores numéricos;
- identificação de registros duplicados;
- continuidade mensal e trimestral;
- verificação de percentuais entre 0 e 100;
- verificação de quantidades não negativas;
- consistência entre força de trabalho, ocupados e desocupados;
- comparação entre quantidade e percentual de contribuintes;
- preservação de anos sem dados como nulos;
- identificação de períodos completos, parciais e indisponíveis;
- verificação do recorte funcional da Previdência no SIOP.

As validações ajudam a identificar problemas técnicos e diferenças metodológicas, mas não substituem a leitura da documentação oficial de cada fonte.

## Possibilidades de análise

Os produtos Gold permitem construir análises sobre:

- crescimento populacional;
- envelhecimento da população;
- mercado de trabalho;
- desemprego;
- informalidade;
- cobertura contributiva previdenciária;
- evolução nominal do PIB;
- inflação anual e mensal;
- crescimento real trimestral do PIB;
- evolução da LOA;
- evolução do orçamento relacionado à Previdência;
- participação da Previdência no orçamento;
- valores orçamentários corrigidos pela inflação;
- relações entre emprego, contribuição, demografia e orçamento público.

As comparações entre fontes devem respeitar a granularidade e a unidade de cada indicador.

## Situação atual

Nesta versão, o pipeline já permite:

- listar as fontes cadastradas;
- executar todas as fontes;
- executar uma ou várias fontes específicas;
- consultar o IBGE e a PNAD pelo SIDRA;
- consultar séries do IPEAData;
- consultar a LOA completa do SIOP;
- preservar os retornos originais;
- gerar arquivos tratados em CSV e Parquet;
- consolidar indicadores anuais do IBGE e da PNAD;
- gerar produtos mensais, trimestrais e anuais do IPEAData;
- gerar o total anual da LOA;
- gerar o recorte anual da Previdência Pública;
- registrar status de disponibilidade;
- manter um catálogo das séries executadas;
- produzir uma base adequada para análises e futura carga em banco de dados.

## Próximas etapas

Entre os próximos desenvolvimentos estão:

- criar tabelas de comparação entre IBGE, IPEAData e SIOP;
- produzir um painel anual integrado;
- criar regras automáticas de auditoria e inconsistências;
- incorporar a camada Gold em banco de dados;
- criar notebooks analíticos;
- desenvolver visualizações e dashboards;
- adicionar testes automatizados;
- ampliar a documentação das variáveis;
- adicionar novas fontes públicas;
- estudar o uso de microdados da PNAD;
- avaliar outras fontes orçamentárias;
- criar logs mais detalhados;
- reduzir o tempo de consultas mais pesadas.

## Observações sobre os dados

### Exercício de 2026

O exercício de 2026 ainda está em andamento.

Por isso:

- valores do SIOP representam o acumulado disponível no momento da coleta;
- algumas séries anuais podem estar parciais;
- indicadores com meses futuros permanecem nulos;
- o status do período deve ser consultado antes de realizar comparações.

### IPEAData e IBGE

Algumas séries disseminadas pelo IPEAData têm origem no próprio IBGE.

O IPEAData funciona, nesses casos, como plataforma de disseminação. Portanto, diferenças entre produtos do IBGE e do IPEAData podem resultar de:

- periodicidade;
- metodologia de agregação;
- momento da atualização;
- revisão da série;
- arredondamento;
- recorte temporal.

### Certificado do SIOP

A opção:

```json
"ignore_secure_certificate": true
```

foi usada porque o endpoint do SIOP apresentou falha de validação do certificado SSL durante os testes.

Essa configuração deve permanecer restrita à consulta do SIOP.

### Preservação da camada bronze

Os dados da camada `bronze` devem ser preservados sempre que possível.

Alterações, filtros, padronizações e consolidações devem ocorrer nas camadas seguintes. Essa separação facilita auditoria, reprocessamento e rastreabilidade.

## Estado do projeto

O projeto continua em desenvolvimento.

A arquitetura atual já permite ampliar as fontes e criar produtos analíticos sem misturar dados brutos, dados tratados e resultados consolidados. As próximas etapas deverão concentrar-se no cruzamento entre fontes, na auditoria automática e na disponibilização dos produtos Gold em banco de dados e ferramentas de visualização.