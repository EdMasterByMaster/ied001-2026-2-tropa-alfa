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

    @property
    def vagas_disponiveis(self) -> int:
        return max(self.capacidade - self.vagas_ocupadas, 0)


@dataclass(frozen=True)
class Registration:
    id_inscricao: int
    id_evento: int
    status: str
    nome_participante: Optional[str] = None
    email_participante: Optional[str] = None
    criada_em: Optional[datetime] = None


@dataclass(frozen=True)
class CancellationResult:
    cancelada: Registration
    promovida: Optional[Registration]
