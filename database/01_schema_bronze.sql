-- Criação da base de fontes de dados
CREATE TABLE IF NOT EXISTS fontes_dados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orgao VARCHAR(100) NOT NULL,
    url_origem VARCHAR(255),
    frequencia_atualizacao VARCHAR(50),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Registro de cada ingestão (o histórico de arquivos brutos)
CREATE TABLE IF NOT EXISTS cargas_ingestao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fonte_id INT,
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(10) NOT NULL,
    hash_arquivo VARCHAR(64) UNIQUE,
    data_ingestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caminho_storage VARCHAR(512) NOT NULL,
    FOREIGN KEY (fonte_id) REFERENCES fontes_dados(id)
);
