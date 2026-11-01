from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class Event:
    id_evento: int
    nome: str
    data: date
    local: str
    capacidade: int
    vagas_ocupadas: int = 0
    tamanho_fila: int = 0

    @property
    def status(self) -> str:
        return "Esgotado" if self.vagas_ocupadas >= self.capacidade else "Disponível"


@dataclass(frozen=True)
class Registration:
    id_inscricao: int
    id_evento: int
    status: str
    nome_participante: str
    email_participante: str
    criada_em: Optional[datetime] = None


@dataclass(frozen=True)
class CancellationResult:
    cancelada: Registration
    promovida: Optional[Registration]
