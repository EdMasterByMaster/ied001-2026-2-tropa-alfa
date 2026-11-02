from contextlib import contextmanager
from datetime import date
from typing import Iterator, Optional, Sequence

from .errors import (
    DatabaseError,
    EventNotFound,
    RegistrationNotCancelable,
    RegistrationNotFound,
)
from .models import CancellationResult, Event, Registration


class MySQLRepository:
    def __init__(self, config: dict):
        self.config = config

    def _connect(self):
        try:
            import mysql.connector
        except ImportError as exc:
            raise DatabaseError("Driver MySQL ausente. Execute: python -m pip install -r src/python/requirements.txt") from exc
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as exc:
            raise DatabaseError(f"Não foi possível conectar ao MySQL: {exc}") from exc

    @contextmanager
    def _connection(self) -> Iterator[object]:
        connection = self._connect()
        try:
            yield connection
        except Exception as exc:
            import mysql.connector

            if isinstance(exc, mysql.connector.Error):
                raise DatabaseError(f"Falha ao executar operação no MySQL: {exc}") from exc
            raise
        finally:
            connection.close()

    def _transaction(self, operation):
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                result = operation(cursor)
                connection.commit()
                return result
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    @staticmethod
    def _event(row: dict) -> Event:
        return Event(
            id_evento=row["id_evento"],
            nome=row["nome"],
            data=row["data_evento"],
            local=row["local"],
            capacidade=row["capacidade"],
            vagas_ocupadas=row["vagas_ocupadas"],
            tamanho_fila=row["tamanho_fila"],
        )

    @staticmethod
    def _registration(row: dict) -> Registration:
        return Registration(
            id_inscricao=row["id_inscricao"],
            id_evento=row["id_evento"],
            status=row["status"],
            nome_participante=row["nome_participante"],
            email_participante=row["email_participante"],
            criada_em=row.get("criada_em"),
        )

    @staticmethod
    def _event_select() -> str:
        return """
            SELECT e.id_evento, e.nome, e.data_evento, e.`local`, e.capacidade,
                (SELECT COUNT(*) FROM inscricoes i
                 WHERE i.id_evento = e.id_evento AND i.status = 'confirmada') AS vagas_ocupadas,
                (SELECT COUNT(*) FROM inscricoes i
                 WHERE i.id_evento = e.id_evento AND i.status = 'lista_espera') AS tamanho_fila
            FROM eventos e
        """

    def initialize_schema(self, schema_path: str) -> None:
        with open(schema_path, encoding="utf-8") as schema_file:
            statements = [statement.strip() for statement in schema_file.read().split(";") if statement.strip()]
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                for statement in statements:
                    cursor.execute(statement)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def create_event(self, name: str, event_date: date, location: str, capacity: int) -> Event:
        def insert(cursor):
            cursor.execute(
                "INSERT INTO eventos (nome, data_evento, `local`, capacidade) VALUES (%s, %s, %s, %s)",
                (name, event_date, location, capacity),
            )
            return self._event(
                {
                    "id_evento": cursor.lastrowid,
                    "nome": name,
                    "data_evento": event_date,
                    "local": location,
                    "capacidade": capacity,
                    "vagas_ocupadas": 0,
                    "tamanho_fila": 0,
                }
            )

        return self._transaction(insert)

    def get_event(self, event_id: int) -> Optional[Event]:
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(self._event_select() + " WHERE e.id_evento = %s", (event_id,))
                row = cursor.fetchone()
                return self._event(row) if row else None
            finally:
                cursor.close()

    def list_events(
        self, name: Optional[str] = None, event_date: Optional[date] = None, location: Optional[str] = None
    ) -> Sequence[Event]:
        conditions = []
        parameters = []
        if name:
            conditions.append("e.nome LIKE %s")
            parameters.append(f"%{name}%")
        if event_date:
            conditions.append("e.data_evento = %s")
            parameters.append(event_date)
        if location:
            conditions.append("e.`local` LIKE %s")
            parameters.append(f"%{location}%")
        query = self._event_select()
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY e.data_evento, e.id_evento"
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(query, tuple(parameters))
                return [self._event(row) for row in cursor.fetchall()]
            finally:
                cursor.close()

    def register(self, event_id: int, participant_name: str, participant_email: str) -> Registration:
        def insert(cursor):
            cursor.execute("SELECT id_evento, capacidade FROM eventos WHERE id_evento = %s FOR UPDATE", (event_id,))
            event = cursor.fetchone()
            if event is None:
                raise EventNotFound(event_id)
            cursor.execute(
                "INSERT IGNORE INTO participantes (nome, email) VALUES (%s, %s)",
                (participant_name, participant_email),
            )
            cursor.execute(
                "SELECT id_participante, nome, email FROM participantes WHERE email = %s",
                (participant_email,),
            )
            participant = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) AS total FROM inscricoes "
                "WHERE id_evento = %s AND status = 'confirmada'",
                (event_id,),
            )
            status = "confirmada" if cursor.fetchone()["total"] < event["capacidade"] else "lista_espera"
            cursor.execute(
                "INSERT INTO inscricoes (id_evento, id_participante, status) VALUES (%s, %s, %s)",
                (event_id, participant["id_participante"], status),
            )
            return Registration(cursor.lastrowid, event_id, status, participant["nome"], participant["email"])

        return self._transaction(insert)

    def get_registration(self, registration_id: int) -> Optional[Registration]:
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id_inscricao, id_evento, status, criada_em "
                    "FROM inscricoes WHERE id_inscricao = %s",
                    (registration_id,),
                )
                row = cursor.fetchone()
                return self._registration(row) if row else None
            finally:
                cursor.close()

    def cancel_registration(self, registration_id: int) -> CancellationResult:
        def cancel(cursor):
            cursor.execute("SELECT id_evento FROM inscricoes WHERE id_inscricao = %s", (registration_id,))
            initial = cursor.fetchone()
            if initial is None:
                raise RegistrationNotFound(registration_id)
            event_id = initial["id_evento"]
            cursor.execute("SELECT id_evento FROM eventos WHERE id_evento = %s FOR UPDATE", (event_id,))
            cursor.execute(
                "SELECT id_inscricao, id_evento, status, criada_em "
                "FROM inscricoes WHERE id_inscricao = %s FOR UPDATE",
                (registration_id,),
            )
            row = cursor.fetchone()
            if row["status"] == "cancelada":
                raise RegistrationNotCancelable(registration_id)
            cancelled = Registration(
                row["id_inscricao"],
                row["id_evento"],
                "cancelada",
                row.get("criada_em"),
            )
            cursor.execute("UPDATE inscricoes SET status = 'cancelada' WHERE id_inscricao = %s", (registration_id,))
            promoted = None
            if row["status"] == "confirmada":
                cursor.execute(
                    "SELECT id_inscricao, id_evento, status, criada_em "
                    "FROM inscricoes WHERE id_evento = %s AND status = 'lista_espera' "
                    "ORDER BY id_inscricao ASC LIMIT 1 FOR UPDATE",
                    (event_id,),
                )
                waiting = cursor.fetchone()
                if waiting:
                    cursor.execute(
                        "UPDATE inscricoes SET status = 'confirmada' WHERE id_inscricao = %s",
                        (waiting["id_inscricao"],),
                    )
                    promoted = Registration(
                        waiting["id_inscricao"],
                        waiting["id_evento"],
                        "confirmada",
                        waiting.get("criada_em"),
                    )
            return CancellationResult(cancelled, promoted)

        return self._transaction(cancel)
