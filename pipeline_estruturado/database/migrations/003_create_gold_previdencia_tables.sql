-- Estrutura inicial das tabelas Gold previdenciárias.
-- Os percentuais são armazenados em pontos percentuais:
-- 92,752803% é persistido como NUMERIC 92.752803.

CREATE TABLE IF NOT EXISTS gold.rgps_fluxo_financeiro_ano (
    exercicio SMALLINT NOT NULL,
    arrecadacao_liquida NUMERIC(24, 2) NOT NULL,
    beneficios_previdenciarios NUMERIC(24, 2) NOT NULL,
    resultado_primario_oficial NUMERIC(24, 2) NOT NULL,
    resultado_primario_calculado NUMERIC(24, 2) NOT NULL,
    diferenca_resultado NUMERIC(24, 2) NOT NULL,
    diferenca_relativa_percentual NUMERIC(12, 6) NOT NULL,
    meses_arrecadacao_disponiveis SMALLINT NOT NULL,
    meses_beneficios_disponiveis SMALLINT NOT NULL,
    meses_resultado_disponiveis SMALLINT NOT NULL,
    meses_comuns_disponiveis SMALLINT NOT NULL,
    primeiro_mes_disponivel SMALLINT NOT NULL,
    ultimo_mes_disponivel SMALLINT NOT NULL,
    unidade TEXT NOT NULL,
    status_periodo TEXT NOT NULL,
    status_conciliacao TEXT NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_rgps_fluxo_financeiro_ano PRIMARY KEY (exercicio),
    CONSTRAINT ck_rgps_fluxo_financeiro_ano_exercicio CHECK (exercicio BETWEEN 1900 AND 2100),
    CONSTRAINT ck_rgps_fluxo_meses_arrecadacao_disponiveis CHECK (meses_arrecadacao_disponiveis BETWEEN 0 AND 12),
    CONSTRAINT ck_rgps_fluxo_meses_beneficios_disponiveis CHECK (meses_beneficios_disponiveis BETWEEN 0 AND 12),
    CONSTRAINT ck_rgps_fluxo_meses_resultado_disponiveis CHECK (meses_resultado_disponiveis BETWEEN 0 AND 12),
    CONSTRAINT ck_rgps_fluxo_meses_comuns_disponiveis CHECK (meses_comuns_disponiveis BETWEEN 0 AND 12),
    CONSTRAINT ck_rgps_fluxo_primeiro_mes CHECK (primeiro_mes_disponivel BETWEEN 1 AND 12),
    CONSTRAINT ck_rgps_fluxo_ultimo_mes CHECK (ultimo_mes_disponivel BETWEEN 1 AND 12),
    CONSTRAINT ck_rgps_fluxo_ordem_meses CHECK (primeiro_mes_disponivel <= ultimo_mes_disponivel),
    CONSTRAINT ck_rgps_fluxo_unidade CHECK (BTRIM(unidade) <> ''),
    CONSTRAINT ck_rgps_fluxo_status_periodo CHECK (status_periodo IN ('completo', 'parcial')),
    CONSTRAINT ck_rgps_fluxo_status_conciliacao CHECK (status_conciliacao IN ('identidade_exata', 'diferenca_observada')),
    CONSTRAINT fk_rgps_fluxo_financeiro_ano_carga FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.rgps_fluxo_financeiro_ano IS
    'Fluxo financeiro anual do RGPS consolidado a partir das séries do IPEAData.';

COMMENT ON COLUMN gold.rgps_fluxo_financeiro_ano.carga_id IS
    'Identificador da carga registrada em controle.etl_carga.';

COMMENT ON COLUMN gold.rgps_fluxo_financeiro_ano.carregado_em IS
    'Data e hora em que o registro foi carregado no PostgreSQL.';

CREATE TABLE IF NOT EXISTS staging.rgps_fluxo_financeiro_ano
    (LIKE gold.rgps_fluxo_financeiro_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.rgps_fluxo_financeiro_ano IS
    'Área de preparação da carga para gold.rgps_fluxo_financeiro_ano.';

CREATE TABLE IF NOT EXISTS gold.siop_previdencia_componentes_ano (
    exercicio SMALLINT NOT NULL,
    regra_rgps_beneficios_nucleo TEXT NOT NULL,
    status_mapeamento_rgps TEXT NOT NULL,
    funcao_09_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_nucleo_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rgps_compensacao_previdenciaria_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_com_compensacao_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rgps_ressarcimentos_extraordinarios_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_ampliados_valor_empenhado NUMERIC(24, 2) NOT NULL,
    rpps_uniao_civis_aposentadorias_pensoes_valor_empenhado NUMERIC(24, 2) NOT NULL,
    pensoes_militares_mapeadas_valor_empenhado NUMERIC(24, 2) NOT NULL,
    encargos_previdenciarios_especiais_valor_empenhado NUMERIC(24, 2) NOT NULL,
    contribuicao_patronal_rpps_uniao_valor_empenhado NUMERIC(24, 2) NOT NULL,
    componentes_beneficios_mapeados_valor_empenhado NUMERIC(24, 2) NOT NULL,
    componentes_totais_mapeados_valor_empenhado NUMERIC(24, 2) NOT NULL,
    outros_funcao_09_valor_empenhado NUMERIC(24, 2) NOT NULL,
    percentual_rgps_nucleo_sobre_funcao_09_empenhado NUMERIC(12, 6) NOT NULL,
    percentual_componentes_mapeados_sobre_funcao_09_empenhado NUMERIC(12, 6) NOT NULL,
    funcao_09_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_nucleo_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rgps_compensacao_previdenciaria_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_com_compensacao_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rgps_ressarcimentos_extraordinarios_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_ampliados_valor_liquidado NUMERIC(24, 2) NOT NULL,
    rpps_uniao_civis_aposentadorias_pensoes_valor_liquidado NUMERIC(24, 2) NOT NULL,
    pensoes_militares_mapeadas_valor_liquidado NUMERIC(24, 2) NOT NULL,
    encargos_previdenciarios_especiais_valor_liquidado NUMERIC(24, 2) NOT NULL,
    contribuicao_patronal_rpps_uniao_valor_liquidado NUMERIC(24, 2) NOT NULL,
    componentes_beneficios_mapeados_valor_liquidado NUMERIC(24, 2) NOT NULL,
    componentes_totais_mapeados_valor_liquidado NUMERIC(24, 2) NOT NULL,
    outros_funcao_09_valor_liquidado NUMERIC(24, 2) NOT NULL,
    percentual_rgps_nucleo_sobre_funcao_09_liquidado NUMERIC(12, 6) NOT NULL,
    percentual_componentes_mapeados_sobre_funcao_09_liquidado NUMERIC(12, 6) NOT NULL,
    funcao_09_valor_pago NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_nucleo_valor_pago NUMERIC(24, 2) NOT NULL,
    rgps_compensacao_previdenciaria_valor_pago NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_com_compensacao_valor_pago NUMERIC(24, 2) NOT NULL,
    rgps_ressarcimentos_extraordinarios_valor_pago NUMERIC(24, 2) NOT NULL,
    rgps_beneficios_ampliados_valor_pago NUMERIC(24, 2) NOT NULL,
    rpps_uniao_civis_aposentadorias_pensoes_valor_pago NUMERIC(24, 2) NOT NULL,
    pensoes_militares_mapeadas_valor_pago NUMERIC(24, 2) NOT NULL,
    encargos_previdenciarios_especiais_valor_pago NUMERIC(24, 2) NOT NULL,
    contribuicao_patronal_rpps_uniao_valor_pago NUMERIC(24, 2) NOT NULL,
    componentes_beneficios_mapeados_valor_pago NUMERIC(24, 2) NOT NULL,
    componentes_totais_mapeados_valor_pago NUMERIC(24, 2) NOT NULL,
    outros_funcao_09_valor_pago NUMERIC(24, 2) NOT NULL,
    percentual_rgps_nucleo_sobre_funcao_09_pago NUMERIC(12, 6) NOT NULL,
    percentual_componentes_mapeados_sobre_funcao_09_pago NUMERIC(12, 6) NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_siop_previdencia_componentes_ano PRIMARY KEY (exercicio),
    CONSTRAINT ck_siop_previdencia_componentes_ano_exercicio CHECK (exercicio BETWEEN 1900 AND 2100),
    CONSTRAINT ck_siop_componentes_regra CHECK (BTRIM(regra_rgps_beneficios_nucleo) <> ''),
    CONSTRAINT ck_siop_componentes_status CHECK (BTRIM(status_mapeamento_rgps) <> ''),
    CONSTRAINT fk_siop_previdencia_componentes_ano_carga FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.siop_previdencia_componentes_ano IS
    'Decomposição anual dos componentes previdenciários da função 09 no SIOP.';

COMMENT ON COLUMN gold.siop_previdencia_componentes_ano.carga_id IS
    'Identificador da carga registrada em controle.etl_carga.';

COMMENT ON COLUMN gold.siop_previdencia_componentes_ano.carregado_em IS
    'Data e hora em que o registro foi carregado no PostgreSQL.';

CREATE TABLE IF NOT EXISTS staging.siop_previdencia_componentes_ano
    (LIKE gold.siop_previdencia_componentes_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.siop_previdencia_componentes_ano IS
    'Área de preparação da carga para gold.siop_previdencia_componentes_ano.';

CREATE TABLE IF NOT EXISTS gold.siop_previdencia_validacao_ano (
    exercicio SMALLINT NOT NULL,
    funcao_09_valor_empenhado NUMERIC(24, 2) NOT NULL,
    subfuncoes_valor_empenhado NUMERIC(24, 2) NOT NULL,
    acoes_valor_empenhado NUMERIC(24, 2) NOT NULL,
    diferenca_subfuncoes_empenhado NUMERIC(24, 2) NOT NULL,
    diferenca_acoes_empenhado NUMERIC(24, 2) NOT NULL,
    funcao_09_valor_liquidado NUMERIC(24, 2) NOT NULL,
    subfuncoes_valor_liquidado NUMERIC(24, 2) NOT NULL,
    acoes_valor_liquidado NUMERIC(24, 2) NOT NULL,
    diferenca_subfuncoes_liquidado NUMERIC(24, 2) NOT NULL,
    diferenca_acoes_liquidado NUMERIC(24, 2) NOT NULL,
    funcao_09_valor_pago NUMERIC(24, 2) NOT NULL,
    subfuncoes_valor_pago NUMERIC(24, 2) NOT NULL,
    acoes_valor_pago NUMERIC(24, 2) NOT NULL,
    diferenca_subfuncoes_pago NUMERIC(24, 2) NOT NULL,
    diferenca_acoes_pago NUMERIC(24, 2) NOT NULL,
    status_validacao TEXT NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_siop_previdencia_validacao_ano PRIMARY KEY (exercicio),
    CONSTRAINT ck_siop_previdencia_validacao_ano_exercicio CHECK (exercicio BETWEEN 1900 AND 2100),
    CONSTRAINT ck_siop_validacao_status CHECK (BTRIM(status_validacao) <> ''),
    CONSTRAINT fk_siop_previdencia_validacao_ano_carga FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.siop_previdencia_validacao_ano IS
    'Validação anual entre o total da função 09 e as somas por subfunção e ação.';

COMMENT ON COLUMN gold.siop_previdencia_validacao_ano.carga_id IS
    'Identificador da carga registrada em controle.etl_carga.';

COMMENT ON COLUMN gold.siop_previdencia_validacao_ano.carregado_em IS
    'Data e hora em que o registro foi carregado no PostgreSQL.';

CREATE TABLE IF NOT EXISTS staging.siop_previdencia_validacao_ano
    (LIKE gold.siop_previdencia_validacao_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.siop_previdencia_validacao_ano IS
    'Área de preparação da carga para gold.siop_previdencia_validacao_ano.';

CREATE TABLE IF NOT EXISTS gold.comparacao_ipea_siop_previdencia_ano (
    exercicio SMALLINT NOT NULL,
    ipea_arrecadacao_liquida NUMERIC(24, 2) NOT NULL,
    ipea_beneficios_previdenciarios NUMERIC(24, 2) NOT NULL,
    ipea_resultado_primario_oficial NUMERIC(24, 2) NOT NULL,
    ipea_resultado_primario_calculado NUMERIC(24, 2) NOT NULL,
    ipea_diferenca_resultado NUMERIC(24, 2) NOT NULL,
    ipea_status_periodo TEXT NOT NULL,
    siop_rgps_beneficios_nucleo_empenhado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_nucleo_liquidado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_nucleo_pago NUMERIC(24, 2) NOT NULL,
    siop_rgps_compensacao_previdenciaria_empenhado NUMERIC(24, 2) NOT NULL,
    siop_rgps_compensacao_previdenciaria_liquidado NUMERIC(24, 2) NOT NULL,
    siop_rgps_compensacao_previdenciaria_pago NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_com_compensacao_empenhado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_com_compensacao_liquidado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_com_compensacao_pago NUMERIC(24, 2) NOT NULL,
    siop_rgps_ressarcimentos_extraordinarios_empenhado NUMERIC(24, 2) NOT NULL,
    siop_rgps_ressarcimentos_extraordinarios_liquidado NUMERIC(24, 2) NOT NULL,
    siop_rgps_ressarcimentos_extraordinarios_pago NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_ampliados_empenhado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_ampliados_liquidado NUMERIC(24, 2) NOT NULL,
    siop_rgps_beneficios_ampliados_pago NUMERIC(24, 2) NOT NULL,
    siop_rpps_uniao_civis_aposentadorias_pensoes_pago NUMERIC(24, 2) NOT NULL,
    siop_pensoes_militares_mapeadas_pago NUMERIC(24, 2) NOT NULL,
    siop_encargos_previdenciarios_especiais_pago NUMERIC(24, 2) NOT NULL,
    siop_funcao_09_pago NUMERIC(24, 2) NOT NULL,
    siop_outros_funcao_09_pago NUMERIC(24, 2) NOT NULL,
    diferenca_siop_rgps_nucleo_pago_menos_ipea NUMERIC(24, 2) NOT NULL,
    cobertura_siop_rgps_nucleo_pago_percentual NUMERIC(12, 6) NOT NULL,
    diferenca_siop_rgps_com_compensacao_pago_menos_ipea NUMERIC(24, 2) NOT NULL,
    cobertura_siop_rgps_com_compensacao_pago_percentual NUMERIC(12, 6) NOT NULL,
    diferenca_siop_rgps_ampliado_pago_menos_ipea NUMERIC(24, 2) NOT NULL,
    cobertura_siop_rgps_ampliado_pago_percentual NUMERIC(12, 6) NOT NULL,
    diferenca_siop_rgps_com_compensacao_liquidado_menos_ipea NUMERIC(24, 2) NOT NULL,
    cobertura_siop_rgps_com_compensacao_liquidado_percentual NUMERIC(12, 6) NOT NULL,
    diferenca_siop_rgps_com_compensacao_empenhado_menos_ipea NUMERIC(24, 2) NOT NULL,
    cobertura_siop_rgps_com_compensacao_empenhado_percentual NUMERIC(12, 6) NOT NULL,
    diferenca_funcao_09_pago_menos_ipea NUMERIC(24, 2) NOT NULL,
    relacao_funcao_09_pago_sobre_ipea_percentual NUMERIC(12, 6) NOT NULL,
    estagio_comparacao_principal TEXT NOT NULL,
    escopo_siop_comparacao_principal TEXT NOT NULL,
    status_comparabilidade TEXT NOT NULL,
    observacao_metodologica TEXT NOT NULL,
    carga_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_comparacao_ipea_siop_previdencia_ano PRIMARY KEY (exercicio),
    CONSTRAINT ck_comparacao_ipea_siop_previdencia_ano_exercicio CHECK (exercicio BETWEEN 1900 AND 2100),
    CONSTRAINT ck_comparacao_status_periodo CHECK (ipea_status_periodo IN ('completo', 'parcial')),
    CONSTRAINT ck_comparacao_estagio CHECK (BTRIM(estagio_comparacao_principal) <> ''),
    CONSTRAINT ck_comparacao_escopo CHECK (BTRIM(escopo_siop_comparacao_principal) <> ''),
    CONSTRAINT ck_comparacao_status CHECK (BTRIM(status_comparabilidade) <> ''),
    CONSTRAINT ck_comparacao_observacao CHECK (BTRIM(observacao_metodologica) <> ''),
    CONSTRAINT fk_comparacao_ipea_siop_previdencia_ano_carga FOREIGN KEY (carga_id)
        REFERENCES controle.etl_carga (carga_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE gold.comparacao_ipea_siop_previdencia_ano IS
    'Comparação anual entre o fluxo financeiro do RGPS no IPEAData e a execução orçamentária previdenciária no SIOP.';

COMMENT ON COLUMN gold.comparacao_ipea_siop_previdencia_ano.carga_id IS
    'Identificador da carga registrada em controle.etl_carga.';

COMMENT ON COLUMN gold.comparacao_ipea_siop_previdencia_ano.carregado_em IS
    'Data e hora em que o registro foi carregado no PostgreSQL.';

CREATE TABLE IF NOT EXISTS staging.comparacao_ipea_siop_previdencia_ano
    (LIKE gold.comparacao_ipea_siop_previdencia_ano INCLUDING DEFAULTS);

COMMENT ON TABLE staging.comparacao_ipea_siop_previdencia_ano IS
    'Área de preparação da carga para gold.comparacao_ipea_siop_previdencia_ano.';