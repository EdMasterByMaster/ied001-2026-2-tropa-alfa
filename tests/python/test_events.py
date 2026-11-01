import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "python"))

from eventos.errors import DomainError, EventNotFound, RegistrationNotCancelable, RegistrationNotFound
from eventos.models import CancellationResult, Event, Registration
from eventos.service import EventService


class MemoryRepository:
    def __init__(self):
        self.events = {}
        self.registrations = {}
        self.participants = {}
        self.next_event_id = 1
        self.next_registration_id = 1

    def _event(self, event_id):
        event = self.events[event_id]
        registrations = [item for item in self.registrations.values() if item.id_evento == event_id]
        confirmed = sum(item.status == "confirmada" for item in registrations)
        waiting = sum(item.status == "lista_espera" for item in registrations)
        return Event(
            event.id_evento,
            event.nome,
            event.data,
            event.local,
            event.capacidade,
            confirmed,
            waiting,
        )

    def create_event(self, name, event_date, location, capacity):
        event = Event(self.next_event_id, name, event_date, location, capacity)
        self.events[event.id_evento] = event
        self.next_event_id += 1
        return self._event(event.id_evento)

    def get_event(self, event_id):
        return self._event(event_id) if event_id in self.events else None

    def list_events(self, name=None, event_date=None, location=None):
        result = []
        for event_id in self.events:
            event = self._event(event_id)
            if name and name.casefold() not in event.nome.casefold():
                continue
            if event_date and event.data != event_date:
                continue
            if location and location.casefold() not in event.local.casefold():
                continue
            result.append(event)
        return result

    def register(self, event_id, participant_name, participant_email):
        event = self.get_event(event_id)
        if event is None:
            raise EventNotFound(event_id)
        status = "confirmada" if event.vagas_ocupadas < event.capacidade else "lista_espera"
        participant = self.participants.setdefault(participant_email, (participant_name, participant_email))
        registration = Registration(
            self.next_registration_id,
            event_id,
            status,
            participant[0],
            participant[1],
        )
        self.registrations[registration.id_inscricao] = registration
        self.next_registration_id += 1
        return registration

    def get_registration(self, registration_id):
        return self.registrations.get(registration_id)

    def cancel_registration(self, registration_id):
        registration = self.get_registration(registration_id)
        if registration is None:
            raise RegistrationNotFound(registration_id)
        if registration.status == "cancelada":
            raise RegistrationNotCancelable(registration_id)
        cancelled = Registration(
            registration.id_inscricao,
            registration.id_evento,
            "cancelada",
            registration.nome_participante,
            registration.email_participante,
        )
        self.registrations[registration_id] = cancelled
        promoted = None
        if registration.status == "confirmada":
            waiting = sorted(
                (
                    item
                    for item in self.registrations.values()
                    if item.id_evento == registration.id_evento and item.status == "lista_espera"
                ),
                key=lambda item: item.id_inscricao,
            )
            if waiting:
                next_item = waiting[0]
                promoted = Registration(
                    next_item.id_inscricao,
                    next_item.id_evento,
                    "confirmada",
                    next_item.nome_participante,
                    next_item.email_participante,
                )
                self.registrations[next_item.id_inscricao] = promoted
        return CancellationResult(cancelled, promoted)


class EventServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MemoryRepository()
        self.service = EventService(self.repository)

    def test_create_event_and_validate_required_fields(self):
        event = self.service.create_event(" Feira de Ciências ", date(2026, 12, 1), " Auditório ", 2)

        self.assertEqual(event.nome, "Feira de Ciências")
        self.assertEqual(event.local, "Auditório")
        self.assertEqual(event.capacidade, 2)
        with self.assertRaises(DomainError):
            self.service.create_event("", date(2026, 12, 1), "Auditório", 2)
        with self.assertRaises(DomainError):
            self.service.create_event("Feira", date(2026, 12, 1), "Auditório", 0)

    def test_catalog_searches_by_name_date_and_location(self):
        self.service.create_event("Feira de Ciências", date(2026, 12, 1), "Auditório Central", 20)
        self.service.create_event("Encontro de Robótica", date(2026, 12, 2), "Auditório Central", 10)

        found = self.service.list_events(name="ciências", event_date=date(2026, 12, 1), location="central")

        self.assertEqual([event.nome for event in found], ["Feira de Ciências"])

    def test_registration_confirms_until_capacity_then_adds_to_fifo_waitlist(self):
        event = self.service.create_event("Palestra", date(2026, 12, 1), "Sala 1", 1)

        first = self.service.register(event.id_evento, "Ana", "ana@example.com")
        second = self.service.register(event.id_evento, "Bruno", "bruno@example.com")
        third = self.service.register(event.id_evento, "Caio", "caio@example.com")

        self.assertEqual(first.status, "confirmada")
        self.assertEqual(second.status, "lista_espera")
        self.assertEqual(third.status, "lista_espera")
        self.assertEqual(second.nome_participante, "Bruno")
        self.assertEqual(second.email_participante, "bruno@example.com")
        self.assertEqual([second.id_inscricao, third.id_inscricao], sorted([second.id_inscricao, third.id_inscricao]))

    def test_registration_requires_valid_participant_name_and_email(self):
        event = self.service.create_event("Palestra", date(2026, 12, 1), "Sala 1", 1)

        with self.assertRaises(DomainError):
            self.service.register(event.id_evento, "", "ana@example.com")
        with self.assertRaises(DomainError):
            self.service.register(event.id_evento, "Ana", "invalid-email")
        with self.assertRaises(DomainError):
            self.service.register(event.id_evento, "A" * 151, "ana@example.com")

        registration = self.service.register(event.id_evento, " Ana Silva ", " ANA@EXAMPLE.COM ")
        self.assertEqual(registration.nome_participante, "Ana Silva")
        self.assertEqual(registration.email_participante, "ana@example.com")

    def test_participant_email_reuses_the_existing_participant_record(self):
        first_event = self.service.create_event("Palestra 1", date(2026, 12, 1), "Sala 1", 2)
        second_event = self.service.create_event("Palestra 2", date(2026, 12, 2), "Sala 2", 2)

        first = self.service.register(first_event.id_evento, "Ana Silva", "ana@example.com")
        second = self.service.register(second_event.id_evento, "Outro Nome", "ANA@example.com")

        self.assertEqual(first.nome_participante, "Ana Silva")
        self.assertEqual(second.nome_participante, "Ana Silva")
        self.assertEqual(second.email_participante, "ana@example.com")

    def test_lookup_and_event_summary_report_status_capacity_and_queue(self):
        event = self.service.create_event("Show", date(2026, 12, 1), "Arena", 1)
        confirmed = self.service.register(event.id_evento, "Ana", "ana@example.com")
        waiting = self.service.register(event.id_evento, "Bruno", "bruno@example.com")

        self.assertEqual(self.service.get_registration(waiting.id_inscricao).status, "lista_espera")
        self.assertEqual(self.service.get_registration(waiting.id_inscricao).nome_participante, "Bruno")
        summary = self.service.get_summary(event.id_evento)
        self.assertEqual(summary.status, "Esgotado")
        self.assertEqual(summary.vagas_ocupadas, 1)
        self.assertEqual(summary.tamanho_fila, 1)
        with self.assertRaises(RegistrationNotFound):
            self.service.get_registration(999)

    def test_cancelation_promotes_waiting_registrations_in_fifo_order(self):
        event = self.service.create_event("Show", date(2026, 12, 1), "Arena", 1)
        confirmed = self.service.register(event.id_evento, "Ana", "ana@example.com")
        first_waiting = self.service.register(event.id_evento, "Bruno", "bruno@example.com")
        second_waiting = self.service.register(event.id_evento, "Caio", "caio@example.com")

        first_result = self.service.cancel_registration(confirmed.id_inscricao)
        self.assertEqual(first_result.cancelada.status, "cancelada")
        self.assertEqual(first_result.promovida.id_inscricao, first_waiting.id_inscricao)
        self.assertEqual(first_result.promovida.nome_participante, "Bruno")

        second_result = self.service.cancel_registration(first_waiting.id_inscricao)
        self.assertEqual(second_result.promovida.id_inscricao, second_waiting.id_inscricao)
        self.assertEqual(self.service.get_registration(second_waiting.id_inscricao).status, "confirmada")
        summary = self.service.get_summary(event.id_evento)
        self.assertEqual(summary.vagas_ocupadas, 1)
        self.assertEqual(summary.tamanho_fila, 0)

    def test_unknown_event_and_repeated_cancelation_are_rejected(self):
        with self.assertRaises(EventNotFound):
            self.service.register(999, "Ana", "ana@example.com")

        event = self.service.create_event("Show", date(2026, 12, 1), "Arena", 1)
        registration = self.service.register(event.id_evento, "Ana", "ana@example.com")
        self.service.cancel_registration(registration.id_inscricao)
        with self.assertRaises(RegistrationNotCancelable):
            self.service.cancel_registration(registration.id_inscricao)


if __name__ == "__main__":
    unittest.main()
