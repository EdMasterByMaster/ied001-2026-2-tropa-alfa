import argparse
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from eventos.errors import DatabaseError, DomainError
from eventos.mysql_repository import MySQLRepository
from eventos.service import EventService


def _service() -> EventService:
    load_dotenv()
    required = ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise DatabaseError("Configure as variáveis: " + ", ".join(missing) + " (consulte .env.example).")
    try:
        port = int(os.getenv("MYSQL_PORT", "3306"))
    except ValueError as exc:
        raise DatabaseError("MYSQL_PORT deve ser um número inteiro.") from exc
    config = {
        "host": os.environ["MYSQL_HOST"],
        "port": port,
        "user": os.environ["MYSQL_USER"],
        "password": os.environ["MYSQL_PASSWORD"],
        "database": os.environ["MYSQL_DATABASE"],
        "charset": "utf8mb4",
    }
    return EventService(MySQLRepository(config))


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a data no formato AAAA-MM-DD.") from exc


def _show_event(event) -> None:
    print(
        f"Evento #{event.id_evento}: {event.nome} | {event.data.isoformat()} | {event.local} | "
        f"{event.status} | vagas: {event.vagas_ocupadas}/{event.capacidade} | fila: {event.tamanho_fila}"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MVP de eventos e inscrições com persistência MySQL.",
        epilog='Exemplo: python src/python/main.py inscrever 1 "Ana Silva" ana@example.com',
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db", help="Cria as tabelas do MVP no banco configurado.")

    create = commands.add_parser("cadastrar-evento", help="Cadastra um evento.")
    create.add_argument("nome")
    create.add_argument("data", type=_date, help="Data no formato AAAA-MM-DD.")
    create.add_argument("local")
    create.add_argument("capacidade", type=int)

    catalog = commands.add_parser("eventos", help="Lista eventos, com filtros opcionais.")
    catalog.add_argument("--nome")
    catalog.add_argument("--data", type=_date)
    catalog.add_argument("--local")

    register = commands.add_parser("inscrever", help="Inscreve no evento ou coloca na fila de espera.")
    register.add_argument("evento_id", type=int)
    register.add_argument("nome")
    register.add_argument("email")

    lookup = commands.add_parser("inscricao", help="Consulta uma inscrição pelo ID.")
    lookup.add_argument("inscricao_id", type=int)

    cancel = commands.add_parser("cancelar", help="Cancela a inscrição e promove o próximo da fila.")
    cancel.add_argument("inscricao_id", type=int)

    summary = commands.add_parser("resumo", help="Mostra lotação e tamanho da fila de um evento.")
    summary.add_argument("evento_id", type=int)
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    try:
        if args.command == "init-db":
            repository = MySQLRepository(_service().repository.config)
            repository.initialize_schema(str(Path(__file__).with_name("schema.sql")))
            print("Tabelas criadas/atualizadas com sucesso.")
            return 0

        service = _service()
        if args.command == "cadastrar-evento":
            event = service.create_event(args.nome, args.data, args.local, args.capacidade)
            _show_event(event)
        elif args.command == "eventos":
            events = service.list_events(name=args.nome, event_date=args.data, location=args.local)
            for event in events:
                _show_event(event)
            if not events:
                print("Nenhum evento encontrado.")
        elif args.command == "inscrever":
            registration = service.register(args.evento_id, args.nome, args.email)
            print(
                f"Inscrição #{registration.id_inscricao} para {registration.nome_participante} "
                f"({registration.email_participante}): {registration.status}."
            )
        elif args.command == "inscricao":
            registration = service.get_registration(args.inscricao_id)
            print(
                f"Inscrição #{registration.id_inscricao} | evento #{registration.id_evento} | "
                f"{registration.nome_participante} ({registration.email_participante}) | {registration.status}"
            )
        elif args.command == "cancelar":
            result = service.cancel_registration(args.inscricao_id)
            print(f"Inscrição #{result.cancelada.id_inscricao} cancelada.")
            if result.promovida:
                print(f"Inscrição #{result.promovida.id_inscricao} promovida da fila para confirmada.")
        elif args.command == "resumo":
            _show_event(service.get_summary(args.evento_id))
    except (DatabaseError, DomainError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
