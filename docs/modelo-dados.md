# Modelo de dados do MVP

O schema executável está em `src/python/schema.sql`. A persistência usa três tabelas InnoDB:

## `eventos`

- `id_evento`: chave primária numérica, gerada pelo banco.
- `nome`, `data_evento`, `local`: dados usados no catálogo e nos filtros.
- `capacidade`: total de vagas, obrigatório e maior que zero.

## `participantes`

- `id_participante`: chave primária numérica, gerada pelo banco.
- `nome`: nome obrigatório, com até 150 caracteres.
- `email`: e-mail obrigatório e único, normalizado para minúsculas.

Um participante pode ter inscrições em eventos diferentes; a unicidade do e-mail evita duplicar o cadastro.

## `inscricoes`

- `id_inscricao`: chave primária numérica que o usuário usa para consultar/cancelar a inscrição.
- `id_evento`: chave estrangeira para o evento.
- `id_participante`: chave estrangeira para o participante.
- `status`: `confirmada`, `lista_espera` ou `cancelada`.
- `criada_em`: data/hora de criação para auditoria.

A ocupação e o tamanho da fila são calculados a partir das inscrições ativas; não são armazenados como contadores que possam divergir. Vagas disponíveis são `max(capacidade - vagas ocupadas, 0)`. Um evento está `Esgotado` quando o total de inscrições confirmadas atinge a capacidade. Inscrições canceladas não ocupam vaga. A consulta pelo ID da inscrição retorna evento e status, sem revelar nome ou e-mail.

## Regras e concorrência

1. A inscrição bloqueia a linha do evento (`SELECT ... FOR UPDATE`) e decide entre confirmação e fila dentro de uma transação.
2. O cancelamento bloqueia o evento, cancela a inscrição e promove o menor `id_inscricao` em espera na mesma transação.
3. O índice `(id_evento, status, id_inscricao)` atende à consulta da fila FIFO.
4. As chaves estrangeiras impedem inscrições para eventos ou participantes inexistentes. O banco também rejeita capacidade zero.

O sistema usa IDs sequenciais como identificadores de inscrição e não processa pagamentos. O e-mail é informação pessoal; use dados fictícios nos testes e não compartilhe cópias do banco.