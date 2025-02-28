from src.tesouro.config.log import logger
from src.tesouro.service.calcular_comparativo import calcular_comparativo
from src.tesouro.service.exibir_resultados import exibir_resultados
from src.tesouro.service.tesouro_direto_extractor import TesouroDiretoExtractor


def main() -> None:
    """Função principal do programa"""
    extractor = TesouroDiretoExtractor()


    try:
        # Obter dados do Tesouro Direto
        titulos_prefixados, titulos_ipca = extractor.extrair_dados()

        # Se não conseguiu obter dados, usar dados de exemplo
        if not titulos_prefixados or not titulos_ipca:
            logger.warning("Não foi possível obter dados reais. Usando dados de exemplo.")

        # Calcular o comparativo
        resultados = calcular_comparativo(titulos_prefixados, titulos_ipca)

        # Exibir resultados
        df_resultados = exibir_resultados(resultados)

    except Exception as e:
        logger.error(f"Erro inesperado na execução do programa: {e}")

if __name__ == "__main__":
    main()