CREATE TABLE IF NOT EXISTS pedidos (
    id        SERIAL PRIMARY KEY,
    item      VARCHAR(100) NOT NULL,
    quantidade INTEGER      NOT NULL CHECK (quantidade > 0),
    status    VARCHAR(50)  NOT NULL DEFAULT 'Em preparo',
    criado_em TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO pedidos (id, item, quantidade, status) VALUES
    (1, 'Pizza',       2, 'Em preparo'),
    (2, 'Hambúrguer',  1, 'Pronto'),
    (3, 'Salada',      3, 'Em preparo');

SELECT setval('pedidos_id_seq', (SELECT MAX(id) FROM pedidos));
