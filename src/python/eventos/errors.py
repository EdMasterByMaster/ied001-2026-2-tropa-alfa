class DomainError(ValueError):
    """Erro esperado nas regras do domínio."""


class EventNotFound(DomainError):
    def __init__(self, event_id: int):
        super().__init__(f"Evento {event_id} não encontrado.")


class RegistrationNotFound(DomainError):
    def __init__(self, registration_id: int):
        super().__init__(f"Inscrição {registration_id} não encontrada.")


class RegistrationNotCancelable(DomainError):
    def __init__(self, registration_id: int):
        super().__init__(f"Inscrição {registration_id} já está cancelada.")


class DatabaseError(RuntimeError):
    """Erro de configuração ou conexão com o banco de dados."""
