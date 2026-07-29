CREATE TABLE IF NOT EXISTS gold.ibge_populacao_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    populacao BIGINT,
    unidade_original TEXT NOT NULL,
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ibge_populacao_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_ibge_populacao_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_ibge_populacao_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
            AND BTRIM(unidade_original) <> ''
        ),

    CONSTRAINT ck_ibge_populacao_ano_populacao
        CHECK (populacao IS NULL OR populacao >= 0),

    CONSTRAINT ck_ibge_populacao_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_ibge_populacao_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.ibge_populacao_ano IS
    'População estimada do Brasil por exercício, produzida a partir de dados do IBGE.';

COMMENT ON COLUMN gold.ibge_populacao_ano.coletado_em IS
    'Data e hora da coleta na fonte de dados.';

COMMENT ON COLUMN gold.ibge_populacao_ano.carregado_em IS
    'Data e hora da carga no PostgreSQL.';

CREATE TABLE IF NOT EXISTS staging.ibge_populacao_ano
    (LIKE gold.ibge_populacao_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.ibge_populacao_ano IS
    'Área de preparação da carga para gold.ibge_populacao_ano.';


CREATE TABLE IF NOT EXISTS gold.ibge_pib_nominal_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    pib_nominal NUMERIC(24, 2),
    valor_original NUMERIC(24, 6),
    unidade_original TEXT NOT NULL,
    multiplicador_para_reais NUMERIC(24, 6),
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ibge_pib_nominal_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_ibge_pib_nominal_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_ibge_pib_nominal_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
            AND BTRIM(unidade_original) <> ''
        ),

    CONSTRAINT ck_ibge_pib_nominal_ano_valores
        CHECK (
            (pib_nominal IS NULL OR pib_nominal >= 0)
            AND (
                multiplicador_para_reais IS NULL
                OR multiplicador_para_reais > 0
            )
        ),

    CONSTRAINT ck_ibge_pib_nominal_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_ibge_pib_nominal_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.ibge_pib_nominal_ano IS
    'Produto Interno Bruto nominal do Brasil por exercício, convertido para reais.';

CREATE TABLE IF NOT EXISTS staging.ibge_pib_nominal_ano
    (LIKE gold.ibge_pib_nominal_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.ibge_pib_nominal_ano IS
    'Área de preparação da carga para gold.ibge_pib_nominal_ano.';


CREATE TABLE IF NOT EXISTS gold.ibge_ipca_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    ipca_numero_indice_medio NUMERIC(18, 6),
    ipca_numero_indice_fim_periodo NUMERIC(18, 6),
    ipca_variacao_acumulada_ano NUMERIC(12, 6),
    meses_disponiveis SMALLINT,
    ultimo_mes_disponivel SMALLINT,
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ibge_ipca_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_ibge_ipca_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_ibge_ipca_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
        ),

    CONSTRAINT ck_ibge_ipca_ano_meses
        CHECK (
            (
                meses_disponiveis IS NULL
                OR meses_disponiveis BETWEEN 0 AND 12
            )
            AND (
                ultimo_mes_disponivel IS NULL
                OR ultimo_mes_disponivel BETWEEN 1 AND 12
            )
        ),

    CONSTRAINT ck_ibge_ipca_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_ibge_ipca_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.ibge_ipca_ano IS
    'Indicadores anuais do IPCA, incluindo índice médio, fim do período e variação acumulada.';

CREATE TABLE IF NOT EXISTS staging.ibge_ipca_ano
    (LIKE gold.ibge_ipca_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.ibge_ipca_ano IS
    'Área de preparação da carga para gold.ibge_ipca_ano.';


CREATE TABLE IF NOT EXISTS gold.pnad_estrutura_etaria_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    populacao_pnad BIGINT,
    populacao_60_mais BIGINT,
    percentual_60_mais NUMERIC(12, 6),
    unidade_original TEXT NOT NULL,
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_pnad_estrutura_etaria_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_pnad_estrutura_etaria_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_pnad_estrutura_etaria_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
            AND BTRIM(unidade_original) <> ''
        ),

    CONSTRAINT ck_pnad_estrutura_etaria_ano_valores
        CHECK (
            (populacao_pnad IS NULL OR populacao_pnad >= 0)
            AND (
                populacao_60_mais IS NULL
                OR populacao_60_mais >= 0
            )
            AND (
                percentual_60_mais IS NULL
                OR percentual_60_mais BETWEEN 0 AND 100
            )
        ),

    CONSTRAINT ck_pnad_estrutura_etaria_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_pnad_estrutura_etaria_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.pnad_estrutura_etaria_ano IS
    'Estrutura etária anual da população brasileira, com destaque para pessoas de 60 anos ou mais.';

CREATE TABLE IF NOT EXISTS staging.pnad_estrutura_etaria_ano
    (LIKE gold.pnad_estrutura_etaria_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.pnad_estrutura_etaria_ano IS
    'Área de preparação da carga para gold.pnad_estrutura_etaria_ano.';


CREATE TABLE IF NOT EXISTS gold.pnad_mercado_trabalho_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    populacao_14_mais BIGINT,
    forca_de_trabalho BIGINT,
    populacao_ocupada BIGINT,
    populacao_desocupada BIGINT,
    taxa_desocupacao NUMERIC(12, 6),
    pessoas_informais BIGINT,
    taxa_informalidade NUMERIC(12, 6),
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_pnad_mercado_trabalho_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_pnad_mercado_trabalho_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_pnad_mercado_trabalho_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
        ),

    CONSTRAINT ck_pnad_mercado_trabalho_ano_contagens
        CHECK (
            (populacao_14_mais IS NULL OR populacao_14_mais >= 0)
            AND (forca_de_trabalho IS NULL OR forca_de_trabalho >= 0)
            AND (populacao_ocupada IS NULL OR populacao_ocupada >= 0)
            AND (
                populacao_desocupada IS NULL
                OR populacao_desocupada >= 0
            )
            AND (pessoas_informais IS NULL OR pessoas_informais >= 0)
        ),

    CONSTRAINT ck_pnad_mercado_trabalho_ano_taxas
        CHECK (
            (
                taxa_desocupacao IS NULL
                OR taxa_desocupacao BETWEEN 0 AND 100
            )
            AND (
                taxa_informalidade IS NULL
                OR taxa_informalidade BETWEEN 0 AND 100
            )
        ),

    CONSTRAINT ck_pnad_mercado_trabalho_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_pnad_mercado_trabalho_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.pnad_mercado_trabalho_ano IS
    'Indicadores anuais do mercado de trabalho brasileiro produzidos a partir da PNAD Contínua.';

CREATE TABLE IF NOT EXISTS staging.pnad_mercado_trabalho_ano
    (LIKE gold.pnad_mercado_trabalho_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.pnad_mercado_trabalho_ano IS
    'Área de preparação da carga para gold.pnad_mercado_trabalho_ano.';


CREATE TABLE IF NOT EXISTS gold.pnad_contribuicao_previdenciaria_ano (
    fonte TEXT NOT NULL,
    tema TEXT NOT NULL,
    dataset TEXT NOT NULL,
    exercicio SMALLINT NOT NULL,
    pessoas_ocupadas_contribuintes_previdencia BIGINT,
    percentual_ocupados_contribuintes_previdencia NUMERIC(12, 6),
    status_periodo TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_pnad_contribuicao_previdenciaria_ano
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_pnad_contribuicao_previdenciaria_ano_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_pnad_contribuicao_previdenciaria_ano_textos
        CHECK (
            BTRIM(fonte) <> ''
            AND BTRIM(tema) <> ''
            AND BTRIM(dataset) <> ''
        ),

    CONSTRAINT ck_pnad_contribuicao_previdenciaria_ano_valores
        CHECK (
            (
                pessoas_ocupadas_contribuintes_previdencia IS NULL
                OR pessoas_ocupadas_contribuintes_previdencia >= 0
            )
            AND (
                percentual_ocupados_contribuintes_previdencia IS NULL
                OR percentual_ocupados_contribuintes_previdencia
                    BETWEEN 0 AND 100
            )
        ),

    CONSTRAINT ck_pnad_contribuicao_previdenciaria_ano_status
        CHECK (
            status_periodo IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_pnad_contribuicao_previdenciaria_ano_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.pnad_contribuicao_previdenciaria_ano IS
    'Quantidade e percentual anual de pessoas ocupadas que contribuem para a Previdência.';

CREATE TABLE IF NOT EXISTS staging.pnad_contribuicao_previdenciaria_ano
    (LIKE gold.pnad_contribuicao_previdenciaria_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.pnad_contribuicao_previdenciaria_ano IS
    'Área de preparação da carga para gold.pnad_contribuicao_previdenciaria_ano.';


CREATE TABLE IF NOT EXISTS gold.ibge_nucleo_anual (
    exercicio SMALLINT NOT NULL,

    populacao BIGINT,
    pib_nominal NUMERIC(24, 2),

    ipca_numero_indice_medio NUMERIC(18, 6),
    ipca_numero_indice_fim_periodo NUMERIC(18, 6),
    ipca_variacao_acumulada_ano NUMERIC(12, 6),
    meses_disponiveis SMALLINT,
    ultimo_mes_disponivel SMALLINT,

    populacao_pnad BIGINT,
    populacao_60_mais BIGINT,
    percentual_60_mais NUMERIC(12, 6),

    populacao_14_mais BIGINT,
    forca_de_trabalho BIGINT,
    populacao_ocupada BIGINT,
    populacao_desocupada BIGINT,
    taxa_desocupacao NUMERIC(12, 6),
    pessoas_informais BIGINT,
    taxa_informalidade NUMERIC(12, 6),

    pessoas_ocupadas_contribuintes_previdencia BIGINT,
    percentual_ocupados_contribuintes_previdencia NUMERIC(12, 6),

    status_populacao TEXT NOT NULL,
    status_pib TEXT NOT NULL,
    status_ipca TEXT NOT NULL,
    status_estrutura_etaria TEXT NOT NULL,
    status_mercado_trabalho TEXT NOT NULL,
    status_contribuicao_previdenciaria TEXT NOT NULL,

    coletado_em TIMESTAMPTZ NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ibge_nucleo_anual
        PRIMARY KEY (exercicio),

    CONSTRAINT ck_ibge_nucleo_anual_exercicio
        CHECK (exercicio BETWEEN 1900 AND 2100),

    CONSTRAINT ck_ibge_nucleo_anual_contagens
        CHECK (
            (populacao IS NULL OR populacao >= 0)
            AND (populacao_pnad IS NULL OR populacao_pnad >= 0)
            AND (populacao_60_mais IS NULL OR populacao_60_mais >= 0)
            AND (populacao_14_mais IS NULL OR populacao_14_mais >= 0)
            AND (forca_de_trabalho IS NULL OR forca_de_trabalho >= 0)
            AND (populacao_ocupada IS NULL OR populacao_ocupada >= 0)
            AND (
                populacao_desocupada IS NULL
                OR populacao_desocupada >= 0
            )
            AND (pessoas_informais IS NULL OR pessoas_informais >= 0)
            AND (
                pessoas_ocupadas_contribuintes_previdencia IS NULL
                OR pessoas_ocupadas_contribuintes_previdencia >= 0
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_taxas
        CHECK (
            (
                percentual_60_mais IS NULL
                OR percentual_60_mais BETWEEN 0 AND 100
            )
            AND (
                taxa_desocupacao IS NULL
                OR taxa_desocupacao BETWEEN 0 AND 100
            )
            AND (
                taxa_informalidade IS NULL
                OR taxa_informalidade BETWEEN 0 AND 100
            )
            AND (
                percentual_ocupados_contribuintes_previdencia IS NULL
                OR percentual_ocupados_contribuintes_previdencia
                    BETWEEN 0 AND 100
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_meses
        CHECK (
            (
                meses_disponiveis IS NULL
                OR meses_disponiveis BETWEEN 0 AND 12
            )
            AND (
                ultimo_mes_disponivel IS NULL
                OR ultimo_mes_disponivel BETWEEN 1 AND 12
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_populacao
        CHECK (
            status_populacao IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_pib
        CHECK (
            status_pib IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_ipca
        CHECK (
            status_ipca IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_estrutura
        CHECK (
            status_estrutura_etaria IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_mercado
        CHECK (
            status_mercado_trabalho IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT ck_ibge_nucleo_anual_status_contribuicao
        CHECK (
            status_contribuicao_previdenciaria IN (
                'completo',
                'parcial',
                'indisponivel'
            )
        ),

    CONSTRAINT fk_ibge_nucleo_anual_carga
        FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.ibge_nucleo_anual IS
    'Núcleo anual consolidado de indicadores demográficos, econômicos, trabalhistas e previdenciários do IBGE e da PNAD.';

COMMENT ON COLUMN gold.ibge_nucleo_anual.coletado_em IS
    'Data e hora mais recente entre as coletas que contribuíram para a linha anual.';

CREATE TABLE IF NOT EXISTS staging.ibge_nucleo_anual
    (LIKE gold.ibge_nucleo_anual INCLUDING DEFAULTS);

COMMENT ON TABLE staging.ibge_nucleo_anual IS
    'Área de preparação da carga para gold.ibge_nucleo_anual.';