# Diagrama relacional da estrutura `previdencia_etl`

## Leitura geral

A pasta segue uma lógica de pipeline ETL:

- `data/bronze`: entrada bruta por fonte ou tema.
- `data/silver`: espaço reservado para dados tratados.
- `data/gold`: espaço reservado para dados consolidados/analíticos.
- `scripts`: tende a concentrar rotinas de coleta, transformação e consolidação.
- `outputs`: tende a receber produtos finais, relatórios, tabelas e visualizações.
- `logs`: tende a guardar registros de execução.
- `docs` e `notebooks`: apoio documental e análise exploratória.

No ZIP analisado, os arquivos encontrados estão concentrados em `data/bronze/siop`, principalmente PDFs de LOA, PLOA e anexos entre 2015 e 2026.

## Diagrama Mermaid

```mermaid
flowchart LR
    A[previdencia_etl] --> B[data]
    A --> C[docs]
    A --> D[logs]
    A --> E[notebooks]
    A --> F[outputs]
    A --> G[scripts]

    B --> H[bronze<br/>dados brutos]
    H --> I[silver<br/>dados tratados]
    I --> J[gold<br/>dados analíticos]
    J --> F

    G -->|coleta| H
    G -->|transformação| I
    G -->|consolidação| J
    G -->|registros de execução| D

    H --> BCB[BCB<br/>inpc, ipca, juros, selic]
    H --> Fiscal[Fiscal<br/>rgf, rreo, tesouro_nacional]
    H --> IBGE[IBGE<br/>envelhecimento, expectativa_vida,<br/>populacao, projecoes_populacionais]
    H --> IPEA[IPEA<br/>desemprego, indicadores_sociais,<br/>inflacao, pib]
    H --> Leg[Legislação<br/>emendas_constitucionais,<br/>leis_previdenciarias, reformas]
    H --> PNAD[PNAD<br/>informalidade, ocupacao,<br/>previdencia, rendimento]
    H --> Prev[Previdência<br/>aeps, arrecadacao, atuarial,<br/>beneficios, beps]
    H --> Transp[Transparência<br/>empenho, liquidado, pago]
    H --> SIOP[SIOP<br/>2015 a 2026]

    SIOP --> Ano[Ano orçamentário]
    Ano --> LDO[ldo]
    Ano --> LDOA[ldo_anexos]
    Ano --> LOA[loa]
    Ano --> LOAA[loa_anexos]
    Ano --> META[metadados]
    Ano --> PLOA[ploa]
    Ano --> PLOAA[ploa_anexos]
    Ano --> PPA[ppa]
    Ano --> PPAA[ppa_anexos]

```

## Árvore completa de pastas

```text
└── previdencia_etl/
    ├── data/
    │   ├── bronze/
    │   │   ├── bcb/
    │   │   │   ├── inpc/
    │   │   │   ├── ipca/
    │   │   │   ├── juros/
    │   │   │   └── selic/
    │   │   ├── fiscal/
    │   │   │   ├── rgf/
    │   │   │   ├── rreo/
    │   │   │   └── tesouro_nacional/
    │   │   ├── ibge/
    │   │   │   ├── envelhecimento/
    │   │   │   ├── expectativa_vida/
    │   │   │   ├── populacao/
    │   │   │   └── projecoes_populacionais/
    │   │   ├── ipea/
    │   │   │   ├── desemprego/
    │   │   │   ├── indicadores_sociais/
    │   │   │   ├── inflacao/
    │   │   │   └── pib/
    │   │   ├── legislacao/
    │   │   │   ├── emendas_constitucionais/
    │   │   │   ├── leis_previdenciarias/
    │   │   │   └── reformas/
    │   │   ├── pnad/
    │   │   │   ├── informalidade/
    │   │   │   ├── ocupacao/
    │   │   │   ├── previdencia/
    │   │   │   └── rendimento/
    │   │   ├── previdencia/
    │   │   │   ├── aeps/
    │   │   │   ├── arrecadacao/
    │   │   │   ├── atuarial/
    │   │   │   ├── beneficios/
    │   │   │   └── beps/
    │   │   ├── siop/
    │   │   │   ├── 2015/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2016/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2017/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2018/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2019/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2020/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2021/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2022/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2023/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2024/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   ├── 2025/
    │   │   │   │   ├── ldo/
    │   │   │   │   ├── ldo_anexos/
    │   │   │   │   ├── loa/
    │   │   │   │   ├── loa_anexos/
    │   │   │   │   ├── metadados/
    │   │   │   │   ├── ploa/
    │   │   │   │   ├── ploa_anexos/
    │   │   │   │   ├── ppa/
    │   │   │   │   └── ppa_anexos/
    │   │   │   └── 2026/
    │   │   │       ├── ldo/
    │   │   │       ├── ldo_anexos/
    │   │   │       ├── loa/
    │   │   │       ├── loa_anexos/
    │   │   │       ├── metadados/
    │   │   │       ├── ploa/
    │   │   │       ├── ploa_anexos/
    │   │   │       ├── ppa/
    │   │   │       └── ppa_anexos/
    │   │   └── transparencia/
    │   │       ├── empenho/
    │   │       ├── liquidado/
    │   │       └── pago/
    │   ├── gold/
    │   └── silver/
    ├── docs/
    ├── logs/
    ├── notebooks/
    ├── outputs/
    └── scripts/
```
