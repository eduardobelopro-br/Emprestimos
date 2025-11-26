import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacenAPI:
    """
    Cliente para a API do Banco Central do Brasil (BACEN)
    Sistema Gerenciador de Séries Temporais (SGS)
    """
    
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    CODIGO_SELIC = 432   # Meta da Taxa Selic (% a.a.)
    CODIGO_CDI = 4389    # CDI acumulado no ano anualizado (% a.a.)
    TIMEOUT = 10         # Timeout em segundos
    
    @staticmethod
    def buscar_taxa(codigo_serie: int, nome_taxa: str = "Taxa") -> Optional[float]:
        """
        Busca uma taxa específica na API do BACEN
        
        Args:
            codigo_serie: Código da série temporal no SGS
            nome_taxa: Nome da taxa para logging
            
        Returns:
            float: Valor da taxa em % a.a. ou None em caso de erro
        """
        try:
            # Define período de busca (últimos 90 dias para garantir dados)
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=90)
            
            # Formata datas no padrão brasileiro (dd/mm/yyyy)
            data_inicio_str = data_inicio.strftime("%d/%m/%Y")
            data_fim_str = data_fim.strftime("%d/%m/%Y")
            
            # Monta URL da requisição
            url = f"{BacenAPI.BASE_URL}.{codigo_serie}/dados"
            params = {
                "formato": "json",
                "dataInicial": data_inicio_str,
                "dataFinal": data_fim_str
            }
            
            logger.info(f"Buscando {nome_taxa} (série {codigo_serie}) no BACEN...")
            
            # Faz a requisição
            response = requests.get(url, params=params, timeout=BacenAPI.TIMEOUT)
            response.raise_for_status()  # Levanta exceção se status não for 200
            
            # Processa resposta JSON
            dados = response.json()
            
            if not dados:
                logger.warning(f"API do BACEN retornou lista vazia para {nome_taxa}")
                return None
            
            # Pega o valor mais recente (último item da lista)
            ultima_entrada = dados[-1]
            data_referencia = ultima_entrada.get('data')
            valor_str = ultima_entrada.get('valor')
            
            # Converte valor (BACEN usa vírgula como separador decimal)
            valor = float(valor_str.replace(',', '.'))
            
            logger.info(f"✅ {nome_taxa}: {valor}% a.a. (ref: {data_referencia})")
            return valor
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout ao buscar {nome_taxa} no BACEN")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de rede ao buscar {nome_taxa}: {e}")
            return None
        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"❌ Erro ao processar dados do {nome_taxa}: {e}")
            return None
    
    @staticmethod
    def buscar_selic() -> Optional[float]:
        """
        Busca a taxa SELIC atual (Meta definida pelo COPOM)
        
        Returns:
            float: Taxa SELIC em % a.a. ou None em caso de erro
        """
        return BacenAPI.buscar_taxa(BacenAPI.CODIGO_SELIC, "SELIC")
    
    @staticmethod
    def buscar_cdi() -> Optional[float]:
        """
        Busca a taxa CDI anualizada (acumulado no ano)
        
        Returns:
            float: Taxa CDI em % a.a. ou None em caso de erro
        """
        return BacenAPI.buscar_taxa(BacenAPI.CODIGO_CDI, "CDI")
    
    @staticmethod
    def buscar_taxas_atuais() -> Dict[str, Optional[float]]:
        """
        Busca SELIC e CDI de uma só vez
        
        Returns:
            dict: {"selic": float, "cdi": float, "data_atualizacao": str}
        """
        logger.info("Iniciando busca de taxas no BACEN...")
        
        selic = BacenAPI.buscar_selic()
        cdi = BacenAPI.buscar_cdi()
        
        return {
            "selic": selic,
            "cdi": cdi,
            "data_atualizacao": datetime.now().isoformat()
        }


# Para testes diretos do módulo
if __name__ == "__main__":
    print("=" * 50)
    print("Testando API do BACEN")
    print("=" * 50)
    
    taxas = BacenAPI.buscar_taxas_atuais()
    
    print("\n📊 Resultados:")
    print(f"SELIC: {taxas['selic']}% a.a." if taxas['selic'] else "SELIC: Erro ao buscar")
    print(f"CDI: {taxas['cdi']}% a.a." if taxas['cdi'] else "CDI: Erro ao buscar")
    print(f"Atualização: {taxas['data_atualizacao']}")
