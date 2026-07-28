# Pipeline Estruturado

Esta pasta contém o pipeline de dados em Python do **Observatório de Dados Públicos**. O projeto coleta, preserva, transforma, valida, consolida e compara dados públicos estruturados provenientes do IBGE/SIDRA, da PNAD Contínua, do IPEAData e do SIOP.

A implementação segue uma arquitetura em camadas `bronze`, `silver` e `gold`. O fluxo combina características de ETL e ELT:

- os dados são extraídos das fontes públicas e preservados na camada `bronze`;
- os registros são limpos, tipados e padronizados na camada `silver`;
- as transformações analíticas, agregações e comparações são produzidas na camada `gold`.

## Objetivo

O objetivo do pipeline é oferecer um fluxo reproduzível e auditável para dados públicos estruturados.

ETL significa:

- **Extract:** coletar dados, metadados e parâmetros em APIs, bibliotecas e serviços públicos;
- **Transform:** limpar, converter, normalizar, enriquecer, agregar e validar os dados coletados;
- **Load:** salvar os resultados em formatos adequados para consulta, análise e integração.

As três camadas principais são:

```text
data/bronze
data/silver
data/gold
```

- A camada `bronze` preserva os retornos próximos ao formato original.
- A camada `silver` contém dados tratados e padronizados.
- A camada `gold` contém tabelas analíticas, indicadores, reconciliações e comparações entre fontes.

## Fontes integradas

### IBGE e PNAD Contínua

Os dados do IBGE e da PNAD Contínua são consultados por meio da API do SIDRA.

A configuração atual inclui indicadores relacionados a:

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

Os produtos anuais do IBGE utilizam, como regra geral, o intervalo de 2015 a 2026. A existência de uma linha para determinado exercício não significa que todos os indicadores estejam disponíveis. Valores ausentes são preservados como nulos.

Os status de disponibilidade usados são:

```text
completo
parcial
indisponivel
```

O pipeline não projeta nem cria valores artificiais para preencher períodos sem informação oficial.

### IPEAData

O IPEAData é usado para consultar séries macroeconômicas e séries do fluxo financeiro do Regime Geral de Previdência Social.

As séries atualmente cadastradas são:

| Dataset | Código da série | Descrição |
|---|---|---|
| `ipea_ipca_indice_mensal` | `PRECOS12_IPCA12` | Número-índice mensal do IPCA |
| `ipea_pib_real_trimestral` | `PAN4_PIBPMG4` | Variação real interanual do PIB trimestral |
| `ipea_rgps_arrecadacao_liquida_mensal` | `MPAS12_ARRLIQ12` | Arrecadação líquida mensal do RGPS |
| `ipea_rgps_beneficios_previdenciarios_mensal` | `MPAS12_BENPREV12` | Benefícios previdenciários mensais do RGPS |
| `ipea_rgps_resultado_primario_mensal` | `MPAS12_RESPRGPS12` | Resultado primário mensal do RGPS |

Na coleta validada em julho de 2026:

- o IPCA mensal possuía observações de dezembro de 1979 a junho de 2026;
- o PIB real trimestral possuía observações do primeiro trimestre de 1997 ao quarto trimestre de 2025;
- as três séries do RGPS possuíam 279 observações mensais, de fevereiro de 2003 a abril de 2026.

Esses períodos podem avançar em novas execuções, conforme a atualização da API.

A série `PAN4_PIBPMG4` não representa um valor monetário do PIB. Ela representa a variação percentual de cada trimestre em relação ao mesmo trimestre do ano anterior.

As séries previdenciárias usam unidade `R$` e multiplicador `mil`. O pipeline preserva o valor recebido na camada `silver` e aplica o fator de multiplicação na construção dos produtos `gold`, passando os valores para reais.

O resultado primário oficial é mantido separadamente do resultado recalculado:

```text
resultado primario calculado
=
arrecadacao liquida
-
beneficios previdenciarios
```

Quando a identidade não fecha exatamente, o pipeline preserva os dois resultados e registra a diferença observada. A diferença não é tratada automaticamente como erro da fonte.

### SIOP

O SIOP é usado para consultar a Lei Orçamentária Anual e a execução orçamentária por meio da biblioteca `orcamentobr`.

A configuração atual consulta os exercícios de 2015 a 2026. Cada exercício é coletado separadamente, preservando as dimensões configuradas da LOA na camada `bronze` e produzindo tabelas tratadas e consolidadas nas camadas seguintes.

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
│       ├── comparacoes/
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
│   ├── gerar_comparacao_previdencia.py
│   ├── inventariar_siop_previdencia_acoes.py
│   └── run_etl.py
├── src/
│   └── observatorio_etl/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── http_client.py
│       ├── ibge.py
│       ├── ipea_gold.py
│       ├── ipea_previdencia_gold.py
│       ├── ipeadata.py
│       ├── paths.py
│       ├── previdencia_comparacoes.py
│       ├── runner.py
│       ├── sidra.py
│       ├── siop.py
│       ├── siop_previdencia_gold.py
│       └── storage.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

Os arquivos efetivamente presentes podem variar conforme o estágio de desenvolvimento. Os diretórios `data`, `logs` e `outputs` armazenam artefatos de execução e não fazem parte do código-fonte principal.

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

A configuração permite acrescentar novas consultas sem reescrever toda a estrutura do pipeline.

## Camada Bronze

A camada `bronze` guarda os dados brutos ou próximos ao formato original recebido das fontes.

Ela permite:

- conferir o retorno da API ou biblioteca;
- preservar parâmetros e metadados de consulta;
- investigar problemas de coleta;
- auditar transformações;
- reaproveitar os dados em etapas futuras de reprocessamento.

Na execução atual, a transformação para `silver` ocorre a partir da resposta recebida em memória, depois de o conteúdo bruto ser registrado. A arquitetura já preserva a Bronze, mas ainda não possui um comando independente para reconstruir toda a Silver exclusivamente a partir dela.

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
data/bronze/ipea/previdencia_rgps/
├── ipea_rgps_arrecadacao_liquida_mensal_metadata.json
├── ipea_rgps_arrecadacao_liquida_mensal_values.json
├── ipea_rgps_arrecadacao_liquida_mensal_values.csv
├── ipea_rgps_beneficios_previdenciarios_mensal_metadata.json
├── ipea_rgps_beneficios_previdenciarios_mensal_values.json
├── ipea_rgps_beneficios_previdenciarios_mensal_values.csv
├── ipea_rgps_resultado_primario_mensal_metadata.json
├── ipea_rgps_resultado_primario_mensal_values.json
└── ipea_rgps_resultado_primario_mensal_values.csv
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

## Camada Silver

A camada `silver` contém os dados tratados e padronizados.

As transformações incluem:

- padronização de nomes de colunas;
- conversão de valores numéricos;
- interpretação de datas e períodos;
- derivação de exercício, mês e trimestre;
- identificação de fonte, tema e dataset;
- normalização de códigos territoriais e orçamentários;
- registro da data e hora da coleta;
- preservação do valor original quando aplicável;
- preservação de unidades e multiplicadores;
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
multiplicador_nome
fator_multiplicador
valor_original
valor
coletado_em
extra_json
```

Nem todas as fontes fornecem todos os campos. Quando a informação não existe na origem, ela permanece nula.

As colunas textuais da consolidação são harmonizadas antes da gravação em Parquet. Isso evita tipos mistos em campos como `valor_original`, que podem receber representações diferentes conforme a fonte.

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

## Camada Gold

A camada `gold` contém produtos analíticos, agregações, validações e comparações entre fontes.

### Catálogo de séries

O catálogo registra as fontes executadas:

```text
data/gold/catalogo_series.csv
```

Estrutura básica:

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

Esses arquivos possuem caráter técnico e servem como ponto de entrada para consultas gerais. Para análises específicas, devem ser preferidos os produtos temáticos das pastas `ibge`, `ipea`, `siop` e `comparacoes`.

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

O arquivo `nucleo_ibge_anual` facilita análises que combinam demografia, atividade econômica, inflação, mercado de trabalho, informalidade e contribuição previdenciária.

### Produtos Gold econômicos do IPEAData

Os produtos ficam em:

```text
data/gold/ipea/
```

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

Quando o ano possui 12 meses, o status é `completo`. Quando possui de 1 a 11 meses, o status é `parcial`.

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

### Produtos Gold previdenciários do IPEAData

O módulo `ipea_previdencia_gold.py` combina as três séries mensais do RGPS.

São produzidos:

```text
data/gold/ipea/rgps_fluxo_financeiro_por_mes.csv
data/gold/ipea/rgps_fluxo_financeiro_por_mes.parquet
data/gold/ipea/rgps_fluxo_financeiro_por_ano.csv
data/gold/ipea/rgps_fluxo_financeiro_por_ano.parquet
```

#### `rgps_fluxo_financeiro_por_mes`

Principais campos:

```text
periodo
exercicio
mes
arrecadacao_liquida
beneficios_previdenciarios
resultado_primario_oficial
resultado_primario_calculado
diferenca_resultado
diferenca_relativa_percentual
unidade
status_periodo
status_conciliacao
```

#### `rgps_fluxo_financeiro_por_ano`

Além dos totais anuais, registra:

```text
meses_arrecadacao_disponiveis
meses_beneficios_disponiveis
meses_resultado_disponiveis
meses_comuns_disponiveis
primeiro_mes_disponivel
ultimo_mes_disponivel
status_periodo
status_conciliacao
```

Os valores monetários desses produtos são expressos em reais.

### Produtos Gold do SIOP

Os produtos ficam em:

```text
data/gold/siop/
```

#### Consolidados anuais

```text
loa_total_por_ano.csv
loa_previdencia_publica_por_ano.csv
```

Os dois arquivos possuem a estrutura básica:

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

`loa_total_por_ano` representa a soma de todos os registros da LOA do exercício.

`loa_previdencia_publica_por_ano` representa a soma dos registros classificados na função `09 - Previdência Social`.

#### Detalhamento da Previdência Federal

Também são produzidos:

```text
previdencia_federal_por_subfuncao_ano.csv
previdencia_federal_por_subfuncao_ano.parquet
previdencia_federal_por_acao_ano.csv
previdencia_federal_por_acao_ano.parquet
previdencia_federal_componentes_por_ano.csv
previdencia_federal_componentes_por_ano.parquet
previdencia_federal_validacao_por_ano.csv
previdencia_federal_validacao_por_ano.parquet
```

`previdencia_federal_por_subfuncao_ano` agrega a função 09 por exercício e subfunção.

`previdencia_federal_por_acao_ano` agrega a função 09 por exercício, órgão, unidade orçamentária, subfunção, programa e ação.

`previdencia_federal_componentes_por_ano` organiza componentes previdenciários mapeados, incluindo:

- núcleo dos benefícios do RGPS;
- compensação previdenciária;
- ressarcimentos extraordinários mapeados;
- aposentadorias e pensões civis da União;
- pensões militares mapeadas;
- encargos previdenciários especiais;
- contribuição patronal da União ao RPPS;
- resíduos classificados como `outros_funcao_09`.

`previdencia_federal_validacao_por_ano` verifica se o total original da função 09 é reproduzido pelas agregações por subfunção e por ação.

Na validação de julho de 2026, os 12 exercícios de 2015 a 2026 apresentaram:

```text
status_validacao = validado
```

As diferenças entre o total da função 09 e as somas detalhadas ficaram em zero para valores empenhados, liquidados e pagos.

## Critério do recorte da função 09

O recorte de Previdência Pública considera todas as linhas da LOA classificadas na função:

```text
09 - Previdencia Social
```

O filtro não se limita às subfunções 271, 272, 273 e 274. Essas são subfunções diretamente associadas à Previdência, mas a função 09 também pode conter registros em outras subfunções administrativas, de controle, compensação ou encargos especiais.

Portanto, todas as linhas classificadas na função 09 são incluídas, independentemente do órgão, unidade orçamentária, programa, ação, plano orçamentário, natureza da despesa, fonte de recursos ou outra dimensão.

Não são incluídas linhas de outras funções apenas porque nomes de órgãos, programas ou ações contêm expressões como `INSS`, `previdência`, `aposentadoria` ou `pensão`.

Esse critério evita decisões baseadas somente em palavras e torna o recorte reproduzível entre exercícios.

A explicação metodológica complementar fica registrada em:

```text
docs/LEGENDA_PREVIDENCIA_PUBLICA.md
```

## Mapeamento das ações previdenciárias do SIOP

O mapeamento usa o código da ação e o exercício, evitando depender apenas da descrição textual.

### Núcleo dos benefícios do RGPS

| Período | Ações consideradas |
|---|---|
| 2015 a 2021 | `0E81` Benefícios Previdenciários Urbanos + `0E82` Benefícios Previdenciários Rurais |
| 2022 em diante | `00SJ` Benefícios Previdenciários |

### Outros componentes mapeados

| Código | Componente |
|---|---|
| `009W` | Compensação previdenciária |
| `00XK` | Ressarcimentos extraordinários mapeados |
| `0181` | Aposentadorias e pensões civis da União |
| `0179` | Pensões militares mapeadas |
| `09HB` | Contribuição patronal da União ao RPPS |

Também são agrupadas ações específicas relacionadas a encargos previdenciários especiais. O componente residual permanece identificado como `outros_funcao_09`, sem receber classificação automática indevida.

## Comparação entre IPEAData e SIOP

A comparação anual é gerada em:

```text
data/gold/comparacoes/
├── ipea_siop_previdencia_federal_por_ano.csv
└── ipea_siop_previdencia_federal_por_ano.parquet
```

O produto compara o fluxo financeiro do RGPS no IPEAData com a execução orçamentária previdenciária mapeada no SIOP.

A comparação principal utiliza:

```text
IPEAData:
beneficios previdenciarios do RGPS

SIOP:
beneficios do RGPS
+
compensacao previdenciaria
no estagio valor pago
```

O produto também mantém comparações auxiliares com valores empenhados, liquidados e pagos, além de recortes mais amplos da função 09.

Principais campos:

```text
ipea_arrecadacao_liquida
ipea_beneficios_previdenciarios
ipea_resultado_primario_oficial
ipea_resultado_primario_calculado
siop_rgps_beneficios_nucleo_pago
siop_rgps_compensacao_previdenciaria_pago
siop_rgps_beneficios_com_compensacao_pago
siop_rpps_uniao_civis_aposentadorias_pensoes_pago
siop_pensoes_militares_mapeadas_pago
siop_funcao_09_pago
siop_outros_funcao_09_pago
diferenca_siop_rgps_com_compensacao_pago_menos_ipea
cobertura_siop_rgps_com_compensacao_pago_percentual
status_comparabilidade
observacao_metodologica
```

Os status de comparabilidade são:

```text
dados_insuficientes
periodo_parcial
parcialmente_comparavel
```

A classificação `parcialmente_comparavel` é usada porque as fontes não representam exatamente o mesmo conceito:

- o IPEAData apresenta fluxo financeiro do RGPS;
- o SIOP apresenta execução orçamentária federal;
- os estágios de empenho, liquidação e pagamento possuem significados distintos;
- podem existir sentenças judiciais, compensações, ajustes de agentes pagadores e restos a pagar com reconhecimento diferente entre as fontes.

Na validação dos anos completos de 2015 a 2025, o recorte principal do SIOP correspondeu a aproximadamente 87,84% a 94,64% dos benefícios informados pelo IPEAData, com média aproximada de 91,38%.

Esses percentuais representam cobertura metodológica do recorte, não uma auditoria contábil nem uma medida automática de erro.

O exercício de 2026 deve ser tratado como parcial enquanto as fontes apresentarem datas de corte diferentes.

## Scripts auxiliares

### `scripts/gerar_comparacao_previdencia.py`

Reconstrói os produtos previdenciários do SIOP e a comparação com o IPEAData usando dados já existentes nas camadas `silver` e `gold`, sem depender de nova consulta às APIs.

Execução:

```bash
PYTHONPATH=src python scripts/gerar_comparacao_previdencia.py
```

### `scripts/inventariar_siop_previdencia_acoes.py`

Analisa o produto anual por ação e gera arquivos auxiliares em `outputs`:

```text
outputs/
├── siop_previdencia_acoes_inventario.csv
├── siop_previdencia_acoes_por_ano.csv
└── siop_previdencia_acoes_nomes_divergentes.csv
```

Execução:

```bash
PYTHONPATH=src python scripts/inventariar_siop_previdencia_acoes.py
```

Esses arquivos auxiliam a revisão do mapeamento das ações, mas não substituem os produtos permanentes da camada `gold`.

## Principais módulos do código

### `scripts/run_etl.py`

Ponto de entrada para execução do pipeline pelo terminal.

### `src/observatorio_etl/cli.py`

Define os comandos e argumentos da interface de linha de comando.

### `src/observatorio_etl/config.py`

Lê e valida o arquivo `config/sources.json`.

### `src/observatorio_etl/http_client.py`

Centraliza requisições HTTP e políticas de tentativa.

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
- multiplicador;
- fator multiplicador;
- valor original;
- valor numérico.

### `src/observatorio_etl/ipea_gold.py`

Constrói os produtos Gold econômicos do IPEAData:

- IPCA anual derivado do número-índice mensal;
- variação real interanual do PIB por trimestre.

### `src/observatorio_etl/ipea_previdencia_gold.py`

Constrói os produtos mensais e anuais do fluxo financeiro do RGPS.

### `src/observatorio_etl/siop.py`

Consulta, valida e transforma os dados do SIOP.

Entre suas responsabilidades estão:

1. validar os parâmetros da consulta;
2. consultar um exercício por vez;
3. repetir tentativas em falhas temporárias;
4. padronizar as colunas;
5. converter valores monetários;
6. preservar dimensões da LOA;
7. construir o total anual;
8. filtrar a função 09;
9. construir o recorte anual da Previdência Pública.

### `src/observatorio_etl/siop_previdencia_gold.py`

Constrói os detalhamentos por subfunção e ação, os componentes previdenciários mapeados e a validação interna da função 09.

### `src/observatorio_etl/previdencia_comparacoes.py`

Constrói a comparação anual entre o fluxo financeiro do RGPS no IPEAData e os componentes da execução orçamentária do SIOP.

### `src/observatorio_etl/runner.py`

Coordena a execução do pipeline.

O módulo:

1. lê as fontes cadastradas;
2. seleciona as fontes solicitadas;
3. chama o coletor correspondente;
4. salva os dados na camada `bronze`;
5. transforma e salva os dados na camada `silver`;
6. gera as séries consolidadas;
7. gera os produtos Gold do SIOP;
8. gera os produtos Gold do IBGE;
9. gera os produtos Gold do IPEAData;
10. gera a comparação previdenciária quando as fontes necessárias estão disponíveis;
11. atualiza o catálogo de séries.

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

Os exemplos abaixo consideram a execução a partir da raiz de `pipeline_estruturado`.

### Listar as fontes

```bash
PYTHONPATH=src python scripts/run_etl.py list-sources
```

### Executar todas as fontes

```bash
PYTHONPATH=src python scripts/run_etl.py run
```

A execução completa pode levar mais tempo por causa das consultas anuais do SIOP.

### Executar uma fonte específica

```bash
PYTHONPATH=src python scripts/run_etl.py run \
  --source ipea_ipca_indice_mensal
```

### Executar várias fontes específicas

O parâmetro `--source` pode ser repetido:

```bash
PYTHONPATH=src python scripts/run_etl.py run \
  --source ipea_rgps_arrecadacao_liquida_mensal \
  --source ipea_rgps_beneficios_previdenciarios_mensal \
  --source ipea_rgps_resultado_primario_mensal
```

Quando apenas algumas fontes são executadas, os produtos que dependem de outras fontes podem não ser reconstruídos. Para testar o pipeline de ponta a ponta, execute todas as fontes sem o parâmetro `--source`.

## Fluxo da execução completa

Quando o comando `run` é executado sem filtro, o pipeline:

1. lê `config/sources.json`;
2. seleciona todas as fontes cadastradas;
3. identifica o tipo de cada fonte;
4. realiza a coleta;
5. salva os dados próximos ao formato original na camada `bronze`;
6. padroniza, tipa e enriquece os dados;
7. salva CSV e Parquet na camada `silver`;
8. gera as séries consolidadas;
9. gera produtos Gold específicos do IBGE, IPEAData e SIOP;
10. gera a comparação previdenciária IPEAData × SIOP;
11. atualiza `catalogo_series.csv`.

Esse fluxo comprova as etapas de extração, transformação e carregamento. As transformações não se limitam à limpeza: incluem regras de negócio, conversão de unidades, agregação temporal, classificação de períodos, mapeamento orçamentário, validação e reconciliação entre fontes.

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

### Exemplo IPEAData econômico

```json
{
  "name": "ipea_ipca_indice_mensal",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "inflacao",
  "series_code": "PRECOS12_IPCA12"
}
```

### Exemplo IPEAData previdenciário

```json
{
  "name": "ipea_rgps_arrecadacao_liquida_mensal",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "previdencia_rgps",
  "series_code": "MPAS12_ARRLIQ12"
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
PYTHONPATH=src python scripts/run_etl.py list-sources
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
- preservação do resultado oficial do RGPS;
- cálculo independente do resultado previdenciário;
- registro da diferença entre resultado oficial e calculado;
- verificação do recorte funcional da Previdência no SIOP;
- reconciliação do total da função 09 com suas subfunções;
- reconciliação do total da função 09 com suas ações;
- classificação da comparabilidade entre IPEAData e SIOP;
- identificação de exercícios com período parcial.

As validações ajudam a identificar problemas técnicos e diferenças metodológicas, mas não substituem a documentação oficial de cada fonte.

## Teste de execução de ponta a ponta

Para comprovar que todas as camadas podem ser recriadas, remova apenas os artefatos gerados, preservando código, configuração e ambiente virtual.

Exemplo de limpeza:

```bash
for diretorio in data/bronze data/silver data/gold outputs; do
  if [ -d "$diretorio" ]; then
    find "$diretorio" \
      -type f \
      ! -name ".gitkeep" \
      -delete

    find "$diretorio" \
      -depth \
      -mindepth 1 \
      -type d \
      -empty \
      -delete
  fi
done

mkdir -p data/bronze data/silver data/gold outputs
```

Depois, execute:

```bash
mkdir -p logs
set -o pipefail

PYTHONPATH=src python scripts/run_etl.py run \
  2>&1 \
  | tee "logs/etl_completa_$(date +%Y%m%d_%H%M%S).log"
```

O teste é considerado aprovado quando:

- Bronze, Silver e Gold são recriadas;
- nenhum arquivo obrigatório fica vazio;
- `series_consolidadas.csv` e `series_consolidadas.parquet` são gravados;
- os produtos previdenciários do IPEAData são gerados;
- os produtos detalhados do SIOP são gerados;
- os 12 exercícios do SIOP aparecem como `validado`;
- a comparação IPEAData × SIOP é criada;
- o catálogo de séries é atualizado.

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
- composição da função 09 por subfunção e ação;
- arrecadação líquida do RGPS;
- benefícios previdenciários do RGPS;
- resultado previdenciário oficial e recalculado;
- aposentadorias e pensões civis da União;
- pensões militares mapeadas;
- compensação previdenciária;
- participação de componentes previdenciários na função 09;
- cobertura do IPEAData pelo recorte orçamentário do SIOP;
- valores orçamentários corrigidos pela inflação;
- benefícios e resultado previdenciário como proporção do PIB;
- relações entre emprego, contribuição, informalidade, demografia e orçamento público.

As comparações devem respeitar a granularidade, unidade, estágio contábil, cobertura institucional e período de cada indicador.

## Achados já reproduzidos pelo pipeline

Com base nos dados completos de 2015 a 2025, o pipeline permitiu observar que:

- a arrecadação líquida nominal do RGPS passou de aproximadamente R$ 350,3 bilhões para R$ 709,7 bilhões;
- os benefícios previdenciários nominais passaram de aproximadamente R$ 436,1 bilhões para R$ 1,033 trilhão;
- o resultado primário oficial passou de aproximadamente -R$ 85,8 bilhões para -R$ 317,2 bilhões;
- o recorte principal do SIOP cobriu, em média, aproximadamente 91,38% do fluxo anual de benefícios do IPEAData;
- a proximidade entre totais agregados não demonstra equivalência de conceitos, pois a função 09 contém componentes além do RGPS.

Esses valores são nominais e refletem a coleta validada em julho de 2026. Novas execuções podem alterar exercícios ainda sujeitos a revisão ou atualização.

## Situação atual

Nesta versão, o pipeline já permite:

- listar as fontes cadastradas;
- executar todas as fontes;
- executar uma ou várias fontes específicas;
- consultar o IBGE e a PNAD pelo SIDRA;
- consultar séries econômicas e previdenciárias do IPEAData;
- consultar a LOA completa do SIOP;
- preservar retornos e metadados próximos ao formato original;
- gerar arquivos tratados em CSV e Parquet;
- consolidar indicadores anuais do IBGE e da PNAD;
- gerar produtos econômicos mensais, trimestrais e anuais do IPEAData;
- gerar o fluxo financeiro mensal e anual do RGPS;
- gerar o total anual da LOA;
- gerar o recorte anual da função 09;
- detalhar a Previdência Federal por subfunção e ação;
- mapear componentes do RGPS, RPPS federal e encargos especiais;
- validar as agregações internas do SIOP;
- comparar IPEAData e SIOP com classificação metodológica;
- registrar status de disponibilidade e comparabilidade;
- manter um catálogo das séries executadas;
- produzir uma base adequada para análises e futura carga em banco de dados.

## Próximas etapas

Entre os próximos desenvolvimentos estão:

- separar comandos de extração, transformação e construção da Gold;
- permitir reconstruir Silver diretamente da Bronze;
- permitir reconstruir Gold diretamente da Silver sem nova coleta;
- criar um painel anual integrado;
- produzir gráficos e dashboards;
- calcular indicadores corrigidos pelo IPCA;
- relacionar Previdência, PIB, população e mercado de trabalho;
- ampliar o mapeamento e a documentação das ações previdenciárias;
- incorporar RPPS estaduais e municipais quando houver fonte adequada;
- adicionar aposentadorias, pensões e auxílios individualizados quando houver séries metodologicamente válidas;
- criar testes automatizados;
- ampliar os logs e relatórios de auditoria;
- incorporar a camada Gold em banco de dados;
- avaliar novas fontes públicas e microdados.

## Observações sobre os dados

### Exercício de 2026

O exercício de 2026 ainda está em andamento.

Por isso:

- valores do SIOP representam o acumulado disponível no momento da coleta;
- o IPEAData previdenciário pode possuir apenas parte dos meses do ano;
- algumas séries anuais permanecem parciais;
- indicadores com períodos futuros permanecem nulos;
- comparações entre fontes com datas de corte diferentes recebem status de período parcial.

### IPEAData e IBGE

Algumas séries disseminadas pelo IPEAData têm origem no próprio IBGE.

O IPEAData funciona, nesses casos, como plataforma de disseminação. Diferenças entre produtos podem resultar de:

- periodicidade;
- metodologia de agregação;
- momento da atualização;
- revisão da série;
- arredondamento;
- recorte temporal.

### IPEAData e SIOP

O IPEAData e o SIOP não devem ser comparados como se representassem a mesma contabilidade.

O IPEAData apresenta fluxo financeiro do RGPS. O SIOP apresenta execução orçamentária e diferencia empenho, liquidação e pagamento. A comparação produzida pelo pipeline é analítica e metodológica, não uma certificação contábil.

### Certificado do SIOP

A opção:

```json
"ignore_secure_certificate": true
```

foi usada porque o endpoint do SIOP apresentou falha de validação do certificado SSL durante os testes.

Essa configuração deve permanecer restrita à consulta do SIOP.

### Preservação da camada Bronze

Os dados da camada `bronze` devem ser preservados sempre que possível.

Alterações, filtros, padronizações e consolidações devem ocorrer nas camadas seguintes. Essa separação facilita auditoria, reprocessamento e rastreabilidade.

## Estado do projeto

O projeto continua em desenvolvimento.

A arquitetura atual já permite ampliar fontes e produtos analíticos sem misturar dados brutos, dados tratados e resultados consolidados. A implementação previdenciária acrescentou uma cadeia completa que vai da extração de séries e dados orçamentários até a validação, o mapeamento de componentes e a comparação metodológica entre fontes.