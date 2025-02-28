from typing import List, Dict, Optional
import pandas as pd
from tabulate import tabulate
from src.tesouro.config.log import logger


def exibir_resultados(resultados: List[Dict]) -> Optional[pd.DataFrame]:
    """Exibe os resultados da análise de inflação implícita"""
    if not resultados:
        logger.warning("Não foi possível calcular os resultados devido à falta de dados")
        return None

    # Converter para DataFrame
    df = pd.DataFrame(resultados)

    # Exibir cabeçalho
    print("\n=== ANÁLISE DE INFLAÇÃO IMPLÍCITA NO TESOURO DIRETO ===\n")

    # Criar uma versão simplificada para exibição
    df_display = df[["Título Prefixado", "Taxa Prefixado (%)",
                     "Título IPCA+", "Taxa IPCA+ (%)",
                     "Inflação Implícita (%)",
                     "Taxa IPCA+  + Inflação Implícita"]]

    print(tabulate(df_display, headers='keys', tablefmt='grid', showindex=False))

    # Exibir explicação e recomendação para cada par de títulos
    print("\n=== INTERPRETAÇÃO E RECOMENDAÇÃO ===\n")

    for i, row in enumerate(resultados):
        print(f"Par {i+1}: {row['Título Prefixado']} vs {row['Título IPCA+']}")
        print(f"Inflação Implícita: {row['Inflação Implícita (%)']:.2f}%")
        print("O que significa: Este é o valor médio anual do IPCA até o vencimento")
        print("que o mercado está prevendo implicitamente.")
        print(f"Recomendação: {row['Recomendação']}")
        print("-" * 80)

    # Explicação adicional
    print("\nEXPLICAÇÃO DETALHADA:")
    print("""
A inflação implícita representa quanto o mercado acha que será o IPCA médio anual até o vencimento do título.

ESTRATÉGIA DE INVESTIMENTO:
- Se você acredita que a inflação média anual será MAIOR que a inflação implícita,
  o melhor negócio é investir no título indexado ao IPCA.
- Se você acredita que a inflação média anual será MENOR que a inflação implícita,
  o título prefixado é a escolha mais rentável.

Esta estratégia vale para qualquer título de renda fixa, desde que tenham o mesmo prazo e emissor.
Isso garante que você está comparando ativos com níveis de risco similares.
    """)

    # Retornar também o DataFrame para possível uso posterior
    return df