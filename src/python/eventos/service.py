import re
from datetime import date
from typing import Optional, Protocol, Sequence

from .errors import DomainError, EventNotFound, RegistrationNotFound
from .models import CancellationResult, Event, Registration


class EventRepository(Protocol):
    def create_event(self, name: str, event_date: date, location: str, capacity: int) -> Event: ...

    def get_event(self, event_id: int) -> Optional[Event]: ...

    def list_events(
        self, name: Optional[str] = None, event_date: Optional[date] = None, location: Optional[str] = None
    ) -> Sequence[Event]: ...

    def register(self, event_id: int, participant_name: str, participant_email: str) -> Registration: ...

    def get_registration(self, registration_id: int) -> Optional[Registration]: ...

    def cancel_registration(self, registration_id: int) -> CancellationResult: ...


class EventService:
    def __init__(self, repository: EventRepository):
        self.repository = repository

    def create_event(self, name: str, event_date: date, location: str, capacity: int) -> Event:
        if not isinstance(name, str) or not name.strip():
            raise DomainError("O nome do evento é obrigatório.")
        if not isinstance(location, str) or not location.strip():
            raise DomainError("O local do evento é obrigatório.")
        if type(event_date) is not date:
            raise DomainError("Informe uma data válida para o evento.")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise DomainError("A capacidade deve ser um número inteiro maior que zero.")
        return self.repository.create_event(name.strip(), event_date, location.strip(), capacity)

    def get_event(self, event_id: int) -> Event:
        event = self.repository.get_event(event_id)
        if event is None:
            raise EventNotFound(event_id)
        return event

    def list_events(
        self, name: Optional[str] = None, event_date: Optional[date] = None, location: Optional[str] = None
    ) -> Sequence[Event]:
        return self.repository.list_events(name=name, event_date=event_date, location=location)

    def register(self, event_id: int, participant_name: str, participant_email: str) -> Registration:
        if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id <= 0:
            raise DomainError("Informe um ID de evento válido.")
        if not isinstance(participant_name, str) or not participant_name.strip():
            raise DomainError("O nome do participante é obrigatório.")
        name = participant_name.strip()
        if len(name) > 150:
            raise DomainError("O nome do participante deve ter até 150 caracteres.")
        if not isinstance(participant_email, str):
            raise DomainError("Informe um e-mail válido.")
        email = participant_email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise DomainError("Informe um e-mail válido.")
        return self.repository.register(event_id, name, email)

    def get_registration(self, registration_id: int) -> Registration:
        if isinstance(registration_id, bool) or not isinstance(registration_id, int) or registration_id <= 0:
            raise DomainError("Informe um ID de inscrição válido.")
        registration = self.repository.get_registration(registration_id)
        if registration is None:
            raise RegistrationNotFound(registration_id)
        return registration

    def cancel_registration(self, registration_id: int) -> CancellationResult:
        if isinstance(registration_id, bool) or not isinstance(registration_id, int) or registration_id <= 0:
            raise DomainError("Informe um ID de inscrição válido.")
        return self.repository.cancel_registration(registration_id)

    def get_summary(self, event_id: int) -> Event:
        return self.get_event(event_id)
