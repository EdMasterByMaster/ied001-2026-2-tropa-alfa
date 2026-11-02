# MVP de Eventos e Inscrições

Sistema para publicar eventos e administrar inscrições com confirmação, lista de espera e acompanhamento de vagas. O projeto foi desenvolvido em Python, com persistência MySQL, interface web e uma CLI para operações pelo terminal.

## Funcionalidades

- Cadastro de eventos com nome, data, local e capacidade.
- Catálogo com busca por nome e filtros por data e local.
- Inscrição de participantes com nome e e-mail e geração de um ID de ingresso.
- Confirmação de inscrições até o limite de vagas e entrada automática na fila quando o evento está lotado.
- Fila de espera FIFO independente para cada evento.
- Consulta de ingresso por ID, mostrando o evento e o status sem expor os dados pessoais do participante.
- Resumo de capacidade, vagas ocupadas, vagas disponíveis e tamanho da fila.
- Cancelamento de inscrição confirmada com promoção imediata da primeira pessoa da fila.

O MVP não processa pagamentos.

## Requisitos

- Python 3.10 ou superior
- MySQL 8.0.16 ou superior com InnoDB
- Navegador web moderno para usar a interface

## Configuração

Abra um terminal na pasta principal do projeto, onde estão `README.md`, `src` e `tests`. No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r src/python/requirements.txt
Copy-Item .env.example .env
```

Crie o banco e o usuário de aplicação no MySQL. Troque a senha de exemplo por uma senha local:

```sql
CREATE DATABASE eventos_mvp CHARACTER SET utf8mb4;
CREATE USER 'eventos_app'@'127.0.0.1' IDENTIFIED BY 'defina-uma-senha';
GRANT ALL PRIVILEGES ON eventos_mvp.* TO 'eventos_app'@'127.0.0.1';
```

Configure as mesmas credenciais no arquivo `.env`, localizado na pasta principal do projeto:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=eventos_app
MYSQL_PASSWORD=sua-senha-local
MYSQL_DATABASE=eventos_mvp
```

O `.env` contém credenciais locais, está ignorado pelo Git e não deve ser compartilhado ou commitado. Com o serviço MySQL iniciado e o ambiente virtual ativo, crie as tabelas:

```powershell
python src/python/main.py init-db
```

## Executar a interface web

Na pasta principal do projeto, com o ambiente virtual ativo e o MySQL configurado:

```powershell
python src/python/webapp.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000) no navegador. A interface permite explorar e filtrar eventos, publicar um evento, inscrever participantes, consultar ingressos e cancelar inscrições. Para encerrar o servidor local, pressione `Ctrl+C` no terminal.

## Executar pela CLI

A CLI também pode ser usada para as mesmas operações. Os comandos são executados na pasta principal do projeto:

```powershell
python src/python/main.py cadastrar-evento "Feira de Ciências" 2026-12-01 "Auditório Central" 100
python src/python/main.py eventos
python src/python/main.py eventos --nome feira --data 2026-12-01 --local Auditório
python src/python/main.py inscrever 1 "Ana Silva" ana@example.com
python src/python/main.py inscricao 1
python src/python/main.py resumo 1
python src/python/main.py cancelar 1
```

Substitua os IDs de exemplo pelos IDs retornados durante a execução. Dados criados são persistidos no MySQL.

## Cards do backlog

Os cards descrevem os requisitos funcionais e se relacionam às áreas correspondentes do sistema:

| Card | Funcionalidade | Implementação |
|---|---|---|
| [US-01 — Cadastrar eventos](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/1) | Criar eventos com data, local e capacidade | `EventService.create_event`, `MySQLRepository.create_event` |
| [US-02 — Inscrever participante](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/2) | Associar participante e evento e gerar ID de ingresso | `EventService.register`, `MySQLRepository.register` |
| [US-03 — Buscar eventos](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/3) | Consultar catálogo por nome, data e local | `EventService.list_events`, `MySQLRepository.list_events` |
| [US-04 — Lista de espera FIFO](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/4) | Enfileirar inscrições quando as vagas se esgotam | `MySQLRepository.register`, índice FIFO do schema |
| [US-05 — Consultar ingresso](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/5) | Consultar evento e status pelo ID | `EventService.get_registration`, `MySQLRepository.get_registration` |
| [US-06 — Acompanhar lotação](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/6) | Exibir ocupação, vagas disponíveis e tamanho da fila | `EventService.get_summary`, `MySQLRepository.get_event` |
| [US-07 — Cancelar e promover](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/7) | Cancelar inscrição e promover a próxima da fila | `MySQLRepository.cancel_registration` |
| [UI-01 — Interface web](https://github.com/EdMasterByMaster/ied001-2026-2-tropa-alfa/issues/9) | Usar as funcionalidades do sistema pelo navegador | `src/python/web/`, `src/python/webapp.py` |

O schema MySQL está em `src/python/schema.sql`; as regras de domínio ficam em `src/python/eventos/service.py`; a interface utiliza essas mesmas regras pela API em `src/python/webapp.py`.

## Testes

Execute os testes automatizados na pasta principal:

```powershell
python -m unittest discover -s tests/python -v
```

Os testes cobrem as regras de domínio e os endpoints e arquivos da interface. Para validar a integração com MySQL, configure um banco de teste no `.env`, inicialize o schema e execute as operações pela interface ou CLI.
