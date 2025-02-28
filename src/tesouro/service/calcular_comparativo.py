# Funções de cálculo e análise
from typing import List, Dict

from src.tesouro.config.log import logger
from src.tesouro.models.resultado_comparativo import ResultadoComparativo
from src.tesouro.models.titulo import Titulo


def calcular_comparativo(titulos_prefixados: List[Dict], titulos_ipca: List[Dict]) -> List[Dict]:
    """Calcula o comparativo entre títulos prefixados e IPCA+"""
    logger.info("Calculando comparativos entre títulos")

    resultados = []

    if not titulos_prefixados or not titulos_ipca:
        logger.warning("Não há dados suficientes para calcular o comparativo")
        return resultados

    # Ordenar títulos por data de vencimento
    titulos_prefixados.sort(key=lambda x: x["vencimento_data"])
    titulos_ipca.sort(key=lambda x: x["vencimento_data"])

    # Para cada título prefixado, encontrar o IPCA+ mais próximo em termos de vencimento
    for prefixado in titulos_prefixados:
        # Encontrar o IPCA+ mais próximo
        ipca_mais_proximo = None
        diferenca_minima = float('inf')

        for ipca in titulos_ipca:
            diferenca = abs((prefixado["vencimento_data"] - ipca["vencimento_data"]).days)
            if diferenca < diferenca_minima:
                diferenca_minima = diferenca
                ipca_mais_proximo = ipca

        if ipca_mais_proximo:
            # Calcular a inflação implícita
            prefixado_valor = 1 + (prefixado["rentabilidade"] / 100)
            ipca_valor = 1 + (ipca_mais_proximo["rentabilidade"] / 100)
            resultado = (prefixado_valor / ipca_valor) - 1
            resultado_percentual = resultado * 100
            resultados_ipca_inflacao_implicita = ipca_mais_proximo["rentabilidade"] + resultado_percentual

            # Criar objeto de resultado e converter para dicionário
            titulo_prefixado = Titulo(
                prefixado["nome"],
                prefixado["vencimento"],
                prefixado["vencimento_data"],
                prefixado["rentabilidade"]
            )

            titulo_ipca = Titulo(
                ipca_mais_proximo["nome"],
                ipca_mais_proximo["vencimento"],
                ipca_mais_proximo["vencimento_data"],
                ipca_mais_proximo["rentabilidade"]
            )

            comparativo = ResultadoComparativo(
                titulo_prefixado,
                titulo_ipca,
                resultado_percentual,
                resultados_ipca_inflacao_implicita
            )

            resultados.append(comparativo.to_dict())

    return resultados