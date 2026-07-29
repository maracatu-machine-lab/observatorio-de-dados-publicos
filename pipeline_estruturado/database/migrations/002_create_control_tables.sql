CREATE TABLE IF NOT EXISTS controle.etl_execucao (
    execucao_id UUID PRIMARY KEY,

    tipo_execucao TEXT NOT NULL,
    comando TEXT,

    fontes_solicitadas JSONB NOT NULL
        DEFAULT '[]'::JSONB,

    iniciado_em TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    finalizado_em TIMESTAMPTZ,

    status TEXT NOT NULL,

    versao_codigo TEXT,
    mensagem_erro TEXT,

    detalhes JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    CONSTRAINT ck_etl_execucao_status
        CHECK (
            status IN (
                'iniciada',
                'concluida',
                'erro'
            )
        ),

    CONSTRAINT ck_etl_execucao_periodo
        CHECK (
            finalizado_em IS NULL
            OR finalizado_em >= iniciado_em
        )
);

CREATE INDEX IF NOT EXISTS idx_etl_execucao_iniciado_em
    ON controle.etl_execucao (
        iniciado_em DESC
    );

CREATE INDEX IF NOT EXISTS idx_etl_execucao_status
    ON controle.etl_execucao (
        status
    );

CREATE TABLE IF NOT EXISTS controle.etl_carga (
    carga_id UUID PRIMARY KEY,

    execucao_id UUID NOT NULL,

    camada TEXT NOT NULL,
    dataset TEXT NOT NULL,
    tabela_destino TEXT NOT NULL,

    arquivo_origem TEXT,
    hash_arquivo_sha256 TEXT,

    linhas_lidas BIGINT NOT NULL
        DEFAULT 0,

    linhas_carregadas BIGINT NOT NULL
        DEFAULT 0,

    linhas_rejeitadas BIGINT NOT NULL
        DEFAULT 0,

    iniciado_em TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    finalizado_em TIMESTAMPTZ,

    status TEXT NOT NULL,

    mensagem_erro TEXT,

    detalhes JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    CONSTRAINT fk_etl_carga_execucao
        FOREIGN KEY (execucao_id)
        REFERENCES controle.etl_execucao (
            execucao_id
        )
        ON DELETE CASCADE,

    CONSTRAINT ck_etl_carga_camada
        CHECK (
            camada IN (
                'bronze',
                'silver',
                'gold'
            )
        ),

    CONSTRAINT ck_etl_carga_status
        CHECK (
            status IN (
                'iniciada',
                'concluida',
                'erro'
            )
        ),

    CONSTRAINT ck_etl_carga_linhas
        CHECK (
            linhas_lidas >= 0
            AND linhas_carregadas >= 0
            AND linhas_rejeitadas >= 0
        ),

    CONSTRAINT ck_etl_carga_periodo
        CHECK (
            finalizado_em IS NULL
            OR finalizado_em >= iniciado_em
        ),

    CONSTRAINT uq_etl_carga_execucao_dataset
        UNIQUE (
            execucao_id,
            dataset,
            tabela_destino
        )
);

CREATE INDEX IF NOT EXISTS idx_etl_carga_dataset
    ON controle.etl_carga (
        dataset
    );

CREATE INDEX IF NOT EXISTS idx_etl_carga_status
    ON controle.etl_carga (
        status
    );

CREATE INDEX IF NOT EXISTS idx_etl_carga_execucao
    ON controle.etl_carga (
        execucao_id
    );

COMMENT ON TABLE controle.etl_execucao IS
    'Registra cada execução de ETL, migration ou carga realizada.';

COMMENT ON TABLE controle.etl_carga IS
    'Registra individualmente os datasets carregados durante uma execução.';