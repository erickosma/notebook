from datetime import datetime
from typing import Dict, Any


class Titulo:
    def __init__(self, nome: str, vencimento: str, vencimento_data: datetime, rentabilidade: float):
        self.nome = nome
        self.vencimento = vencimento
        self.vencimento_data = vencimento_data
        self.rentabilidade = rentabilidade

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nome": self.nome,
            "vencimento": self.vencimento,
            "vencimento_data": self.vencimento_data,
            "rentabilidade": self.rentabilidade
        }