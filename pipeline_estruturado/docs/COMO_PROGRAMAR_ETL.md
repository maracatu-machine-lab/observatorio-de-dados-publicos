# ETL de dados públicos brasileiros

Este projeto usa três camadas de dados.

`data/bronze` guarda o dado bruto recebido da fonte.

`data/silver` guarda o dado tratado em formato tabular padronizado.

`data/gold` guarda a base consolidada para análise, visualização e modelagem.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ver fontes configuradas

```bash
python scripts/run_etl.py list-sources
```

## Executar o ETL

```bash
python scripts/run_etl.py run
```

## Saídas esperadas

Os arquivos brutos ficam em `data/bronze`.

Os arquivos tratados ficam em `data/silver`.

A base final fica em `data/gold/series_consolidadas.csv` e `data/gold/series_consolidadas.parquet`.

O catálogo fica em `data/gold/catalogo_series.csv`.

## Adicionar nova série SIDRA

Inclua uma entrada em `config/sources.json` com `type` igual a `sidra`.

Campos necessários:

```json
{
  "name": "nome_da_base",
  "type": "sidra",
  "source": "ibge",
  "theme": "tema",
  "table": "6579",
  "variable": "9324",
  "period": "all",
  "territorial_level": "1",
  "localities": "all",
  "decimals": "0"
}
```

## Adicionar nova série IPEAData

Inclua uma entrada em `config/sources.json` com `type` igual a `ipeadata`.

Campos necessários:

```json
{
  "name": "nome_da_serie",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "tema",
  "series_code": "CODIGO_DA_SERIE"
}
```
