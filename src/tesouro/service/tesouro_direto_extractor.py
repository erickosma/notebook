import logging
from typing import Optional, Tuple, List, Dict
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

from src.tesouro.config.log import logger
from src.tesouro.models.tipo_titulo import TipoTitulo
from src.tesouro.models.titulo import Titulo



class TesouroDiretoExtractor:
    """Classe para extrair dados do Tesouro Direto utilizando vários métodos"""

    def __init__(self):
        self.tesouro_url = "https://www.tesourodireto.com.br/titulos/precos-e-taxas.htm"
        self.tesouro_api_url = "https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/service/api/treasurybondsinfo.json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.titulos_prefixados = []
        self.titulos_ipca = []

    def _fazer_requisicao(self, url: str) -> Optional[requests.Response]:
        """Faz uma requisição HTTP para a URL especificada"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar a URL {url}: {e}")
            return None

    def _extrair_titulos_do_json(self, script_content: str) -> None:
        """Extrai informações de títulos de um script contendo JSON"""
        try:
            json_match = re.search(r'window\.TD\.titulos\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
            if not json_match:
                return

            json_data = json.loads(json_match.group(1))

            for titulo_data in json_data:
                nome = titulo_data.get('nome', '')
                vencimento = titulo_data.get('vencimento', '')

                try:
                    rentabilidade = float(titulo_data.get('rentabilidade', '0').replace('%', '').replace(',', '.').strip())
                except (ValueError, AttributeError):
                    rentabilidade = 0

                if not vencimento:
                    continue

                try:
                    vencimento_data = datetime.strptime(vencimento, '%d/%m/%Y')
                except ValueError:
                    try:
                        vencimento_data = datetime(int(vencimento), 1, 1)
                    except ValueError:
                        continue

                titulo = Titulo(nome, vencimento, vencimento_data, rentabilidade)

                if TipoTitulo.PREFIXADO in nome:
                    self.titulos_prefixados.append(titulo)
                elif TipoTitulo.IPCA in nome:
                    self.titulos_ipca.append(titulo)

        except Exception as e:
            logger.error(f"Erro ao extrair dados do script: {e}")

    def _extrair_titulos_de_divs(self, soup: BeautifulSoup) -> None:
        """Extrai informações de títulos a partir das divs da página"""
        div_titulos = soup.find_all('div', class_=lambda c: c and ('card-title' in c or 'titulo' in c or 'tesouro' in c))

        for div in div_titulos:
            try:
                nome_titulo = div.get_text().strip()
                taxa_divs = div.find_next_siblings('div') or div.find_all('div')

                for taxa_div in taxa_divs:
                    taxa_text = taxa_div.get_text().strip()
                    taxa_match = re.search(r'(\d+[,.]\d+)\s*%', taxa_text)

                    if not taxa_match:
                        continue

                    rentabilidade = float(taxa_match.group(1).replace(',', '.'))
                    vencimento_match = re.search(r'(\d{2}/\d{2}/\d{4}|20\d{2})', nome_titulo)

                    if not vencimento_match:
                        continue

                    vencimento = vencimento_match.group(1)

                    try:
                        if len(vencimento) == 4:  # Apenas o ano
                            vencimento_data = datetime(int(vencimento), 1, 1)
                        else:
                            vencimento_data = datetime.strptime(vencimento, '%d/%m/%Y')
                    except ValueError:
                        continue

                    titulo = Titulo(nome_titulo, vencimento, vencimento_data, rentabilidade)

                    if TipoTitulo.PREFIXADO in nome_titulo:
                        self.titulos_prefixados.append(titulo)
                    elif TipoTitulo.IPCA in nome_titulo:
                        self.titulos_ipca.append(titulo)
                    break
            except Exception as e:
                logger.warning(f"Erro ao processar div: {e}")

    def _extrair_titulos_de_texto(self, soup: BeautifulSoup) -> None:
        """Extrai informações de títulos a partir do texto da página"""
        text = soup.get_text()

        # Padrões para extração de texto
        patterns = [
            (TipoTitulo.PREFIXADO, re.compile(r'(Tesouro\s+Prefixado\s+.*?20\d{2})[^\d]+([\d,]+%)')),
            (TipoTitulo.IPCA, re.compile(r'(Tesouro\s+IPCA\+\s+.*?20\d{2})[^\d]+([\d,]+%)'))
        ]

        for tipo, pattern in patterns:
            for match in pattern.finditer(text):
                nome = match.group(1).strip()
                taxa_str = match.group(2).strip().replace('%', '').replace(',', '.')

                try:
                    taxa = float(taxa_str)
                except ValueError:
                    continue

                vencimento_match = re.search(r'20\d{2}', nome)
                if not vencimento_match:
                    continue

                vencimento = vencimento_match.group(0)
                vencimento_data = datetime(int(vencimento), 1, 1)

                titulo = Titulo(nome, vencimento, vencimento_data, taxa)

                if tipo == TipoTitulo.PREFIXADO:
                    self.titulos_prefixados.append(titulo)
                elif tipo == TipoTitulo.IPCA:
                    self.titulos_ipca.append(titulo)

    def _extrair_titulos_da_api(self) -> None:
        """Extrai informações de títulos diretamente da API do Tesouro Direto"""
        response = self._fazer_requisicao(self.tesouro_api_url)
        if not response:
            return

        try:
            api_data = response.json()

            if 'response' not in api_data or 'TrsrBdTradgList' not in api_data['response']:
                return

            for item in api_data['response']['TrsrBdTradgList']:
                nome = item.get('TrsrBd', {}).get('nm', '')
                vencimento = item.get('TrsrBd', {}).get('mtrtyDt', '')
                taxa_str = item.get('TrsrBd', {}).get('anulInvstmtRate', '')
                if taxa_str or taxa_str == 0.0:
                    taxa_str = item.get('TrsrBd', {}).get('anulRedRate', '')

                if not nome or not vencimento or taxa_str <= 0.0:
                    continue

                try:
                    taxa = float(taxa_str)
                    vencimento_data = datetime.strptime(vencimento.split("T")[0], "%Y-%m-%d")
                    vencimento_str = vencimento_data.strftime('%d/%m/%Y')

                    titulo = Titulo(nome, vencimento_str, vencimento_data, taxa)

                    if TipoTitulo.PREFIXADO in nome:
                        self.titulos_prefixados.append(titulo)
                    elif TipoTitulo.IPCA in nome:
                        self.titulos_ipca.append(titulo)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar item da API: {e}")
                    continue
        except Exception as e:
            logger.error(f"Erro ao acessar API: {e}")

    def extrair_dados(self, usar_dados_exemplo: bool = False) -> Tuple[List[Dict], List[Dict]]:
        """
        Obtém dados do Tesouro Direto usando várias estratégias em cascata

        Args:
            usar_dados_exemplo: Se True, ignora extração da web e usa dados de exemplo

        Returns:
            Tupla com duas listas de dicionários: títulos prefixados e títulos IPCA+
        """
        # Limpar dados anteriores
        self.titulos_prefixados = []
        self.titulos_ipca = []

        logger.info("Iniciando extração de dados do Tesouro Direto")

        # Tenta fazer requisição para a página principal
        response = self._fazer_requisicao(self.tesouro_url)
        if not response:
            logger.error("Não foi possível acessar a página do Tesouro Direto")
            return self._obter_resultado()

        # Parsear o conteúdo HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Estratégia 1: Procurar script com dados JSON
        logger.info("Tentando extração via JSON embutido no script")
        script_tags = soup.find_all('script')
        for script in script_tags:
            if not script.string or "window.TD" not in script.string:
                continue
            self._extrair_titulos_do_json(script.string)
            break

        # Se a primeira estratégia não funcionar, tenta a segunda
        if not self.titulos_prefixados and not self.titulos_ipca:
            logger.info("Tentando extração via divs da página")
            self._extrair_titulos_de_divs(soup)

        # Se a segunda estratégia não funcionar, tenta a terceira
        if not self.titulos_prefixados and not self.titulos_ipca:
            logger.info("Tentando extração via texto completo da página")
            self._extrair_titulos_de_texto(soup)

        # Se nenhuma das estratégias anteriores funcionou, tenta a API
        if not self.titulos_prefixados and not self.titulos_ipca:
            logger.info("Tentando acesso direto à API")
            self._extrair_titulos_da_api()

        logger.info(f"Extração concluída: {len(self.titulos_prefixados)} títulos prefixados e {len(self.titulos_ipca)} títulos IPCA+")
        return self._obter_resultado()

    def _obter_resultado(self) -> Tuple[List[Dict], List[Dict]]:
        """Retorna os resultados como listas de dicionários"""
        return (
            [titulo.to_dict() for titulo in self.titulos_prefixados],
            [titulo.to_dict() for titulo in self.titulos_ipca]
        )
