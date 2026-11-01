# MVP de Eventos e Inscrições

Projeto avaliativo da disciplina Estrutura de Dados. O MVP em Python usa MySQL e cobre cadastro de eventos, catálogo e busca, inscrição com ID, fila de espera FIFO, consulta de inscrição, resumo de lotação e cancelamento com promoção imediata.

## Requisitos

- Python 3.10 ou superior
- MySQL 8.0.16 ou superior (InnoDB)

## Configuração rápida

No PowerShell, na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r src/python/requirements.txt
Copy-Item .env.example .env
```

Crie o banco e um usuário MySQL para a aplicação (substitua a senha de exemplo; execute em um cliente MySQL):

```sql
CREATE DATABASE eventos_mvp CHARACTER SET utf8mb4;
CREATE USER 'eventos_app'@'127.0.0.1' IDENTIFIED BY 'defina-uma-senha';
GRANT ALL PRIVILEGES ON eventos_mvp.* TO 'eventos_app'@'127.0.0.1';
```

Atualize `.env` com usuário, senha, host, porta e nome do banco. O arquivo `.env` é ignorado pelo Git e não deve conter credenciais em commits. Crie as tabelas com:

```powershell
python src/python/main.py init-db
```

## Uso

Os comandos abaixo são executados na raiz do repositório:

```powershell
python src/python/main.py cadastrar-evento "Feira de Ciências" 2026-12-01 "Auditório Central" 100
python src/python/main.py eventos
python src/python/main.py eventos --nome feira --data 2026-12-01 --local auditório
python src/python/main.py inscrever 1 "Ana Silva" ana@example.com
python src/python/main.py inscricao 1
python src/python/main.py resumo 1
python src/python/main.py cancelar 1
```

Cada inscrição exige nome e e-mail do participante e devolve um ID numérico. Participantes são associados pelo e-mail e podem se inscrever em vários eventos. Quando não houver vaga, a inscrição recebe o status `lista_espera`; ao cancelar uma inscrição confirmada, a primeira inscrição pendente (menor ID no mesmo evento) é confirmada na mesma transação. A consulta pelo ID mostra os dados do participante e o status.

## Testes

Os testes unitários exercitam as histórias sem precisar de MySQL:

```powershell
python -m unittest discover -s tests/python -v
```

Para validar a integração ponta a ponta, configure um banco de teste em `.env`, execute `init-db` e siga os comandos de uso. Os comandos persistem dados; use IDs e eventos de teste.

## Histórias do backlog e pontos de entrada

As issues existentes são os cards de trabalho. O código abaixo já pode ser usado como referência para implementar/refinar cada história e dividir commits:

| História | Issue | Código de referência |
|---|---|---|
| US-01 — cadastrar evento | [#1](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/1) | `EventService.create_event`, `MySQLRepository.create_event`, `schema.sql` |
| US-02 — inscrição de participante e ID | [#2](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/2) | `EventService.register`, `MySQLRepository.register`, tabelas `participantes` e `inscricoes` |
| US-03 — catálogo e busca | [#3](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/3) | `EventService.list_events`, `MySQLRepository.list_events` |
| US-04 — fila FIFO | [#4](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/4) | `MySQLRepository.register`, índice `idx_inscricoes_evento_status_id` |
| US-05 — consultar inscrição | [#5](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/5) | `EventService.get_registration`, `MySQLRepository.get_registration` |
| US-06 — lotação e fila | [#6](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/6) | `EventService.get_summary`, `MySQLRepository.get_event` |
| US-07 — cancelar e promover | [#7](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/7) | `MySQLRepository.cancel_registration` |

Cada integrante pode assumir uma issue, ler o teste correspondente em `tests/python/test_events.py`, executar a suíte e commitar sua alteração na branch combinada pelo grupo. Os comentários nas issues também apontam para esses pontos de entrada; este README mantém o mapa completo junto ao código.

## Limites do MVP

Não há pagamento. Nome e e-mail são armazenados para identificar o participante associado à inscrição; cada inscrição também gera um identificador consultável. As conexões e transações MySQL serializam operações por evento para não exceder a capacidade nem alterar a ordem da fila.
