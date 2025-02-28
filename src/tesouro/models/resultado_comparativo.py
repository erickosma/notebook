from typing import Dict, Any
from src.tesouro.models.titulo import Titulo


class ResultadoComparativo:
    def __init__(
        self,
        titulo_prefixado: Titulo,
        titulo_ipca: Titulo,
        inflacao_implicita: float,
        inflacao_diferencial: float
    ):
        self.titulo_prefixado = titulo_prefixado
        self.titulo_ipca = titulo_ipca
        self.inflacao_implicita = inflacao_implicita
        self.inflacao_diferencial = inflacao_diferencial

        # Determinar recomendação com base na inflação implícita
        if inflacao_implicita > 5:  # Limite conservador para considerar inflação alta
            self.recomendacao = f"Se você acredita que a inflação será MAIOR que {inflacao_implicita:.2f}%, escolha IPCA+. Caso contrário, escolha Prefixado."
        else:
            self.recomendacao = f"Se você acredita que a inflação será MENOR que {inflacao_implicita:.2f}%, escolha Prefixado. Caso contrário, escolha IPCA+."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Título Prefixado": self.titulo_prefixado.nome,
            "Vencimento Prefixado": self.titulo_prefixado.vencimento,
            "Taxa Prefixado (%)": self.titulo_prefixado.rentabilidade,
            "Título IPCA+": self.titulo_ipca.nome,
            "Vencimento IPCA+": self.titulo_ipca.vencimento,
            "Taxa IPCA+ (%)": self.titulo_ipca.rentabilidade,
            "Inflação Implícita (%)": round(self.inflacao_implicita, 2),
            "Taxa IPCA+  + Inflação Implícita": round(self.inflacao_diferencial, 2),
            "Recomendação": self.recomendacao
        }
