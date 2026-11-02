CREATE TABLE IF NOT EXISTS eventos (
    id_evento BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    data_evento DATE NOT NULL,
    `local` VARCHAR(200) NOT NULL,
    capacidade INT UNSIGNED NOT NULL,
    PRIMARY KEY (id_evento),
    CONSTRAINT chk_eventos_capacidade CHECK (capacidade > 0),
    INDEX idx_eventos_data_nome (data_evento, nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS participantes (
    id_participante BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    PRIMARY KEY (id_participante),
    UNIQUE KEY uq_participantes_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inscricoes (
    id_inscricao BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_evento BIGINT UNSIGNED NOT NULL,
    id_participante BIGINT UNSIGNED NOT NULL,
    status ENUM('confirmada', 'lista_espera', 'cancelada') NOT NULL,
    criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_inscricao),
    CONSTRAINT fk_inscricoes_evento FOREIGN KEY (id_evento)
        REFERENCES eventos (id_evento) ON DELETE RESTRICT,
    CONSTRAINT fk_inscricoes_participante FOREIGN KEY (id_participante)
        REFERENCES participantes (id_participante) ON DELETE RESTRICT,
    INDEX idx_inscricoes_evento_status_id (id_evento, status, id_inscricao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
