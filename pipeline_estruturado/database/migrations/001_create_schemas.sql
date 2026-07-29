CREATE SCHEMA IF NOT EXISTS controle;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

COMMENT ON SCHEMA controle IS
    'Metadados de execução, migrations, cargas e validações do pipeline.';

COMMENT ON SCHEMA staging IS
    'Tabelas temporárias utilizadas durante as cargas no PostgreSQL.';

COMMENT ON SCHEMA bronze IS
    'Dados brutos ou próximos ao formato original das fontes.';

COMMENT ON SCHEMA silver IS
    'Dados tratados, tipados e padronizados pelo pipeline.';

COMMENT ON SCHEMA gold IS
    'Produtos analíticos, consolidações, indicadores e comparações.';