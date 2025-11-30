"""
Classe base para todos os agentes do Jarvis.

Todos os agentes (PartnerAgent, FinanceAgent, SetupAgent, OutputAgent)
herdam desta classe base, que fornece funcionalidades comuns:
- Sistema de logging padronizado
- Estrutura comum para processamento

Para criar um novo agente:
1. Herde de BaseAgent
2. Implemente o método process() (obrigatório)
3. Use self.log() para logging
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAgent(ABC):
    """
    Classe abstrata base para todos os agentes do sistema.
    
    Todos os agentes devem herdar desta classe e implementar o método process().
    Esta classe fornece funcionalidades comuns como logging padronizado.
    
    Exemplo de uso:
        class MeuAgent(BaseAgent):
            def __init__(self):
                super().__init__("MeuAgent")
            
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                self.log("Processando dados...")
                return {"success": True, "response": "OK"}
    """
    
    def __init__(self, name: str):
        """
        Inicializa o agente com um nome e timestamp de criação.
        
        Args:
            name: Nome do agente (ex: "FinanceAgent", "SetupAgent")
                  Usado nos logs para identificar qual agente está executando
        """
        self.name = name
        self.created_at = datetime.now()  # Timestamp de quando o agente foi criado
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método abstrato que DEVE ser implementado por todos os agentes.
        
        Este método recebe dados de entrada e retorna um resultado processado.
        Cada agente implementa sua própria lógica de processamento aqui.
        
        Args:
            data: Dicionário com dados de entrada
                  Estrutura varia por agente, mas geralmente contém:
                  - user_phone: ID do usuário
                  - message: Mensagem do usuário
                  - intent: Intenção detectada (opcional)
                  - response: Resposta anterior (opcional)
        
        Returns:
            Dicionário com resultado do processamento
            Geralmente contém:
            - success: bool (se processamento foi bem-sucedido)
            - response: str (mensagem de resposta)
            - data: dict (dados adicionais)
            - error: str (mensagem de erro, se houver)
        
        Raises:
            NotImplementedError: Se o método não for implementado
        """
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """
        Sistema de logging padronizado para todos os agentes.
        
        Logs aparecem no console no formato:
        [HH:MM:SS] [NomeDoAgente] LEVEL: mensagem
        
        Use este método para debug e rastreamento do fluxo:
        - self.log("Iniciando processamento")  # INFO (padrão)
        - self.log("Aviso importante", "WARNING")
        - self.log("Erro ocorreu", "ERROR")
        
        Args:
            message: Mensagem a ser logada
            level: Nível do log
                   - INFO: Informações normais (padrão)
                   - WARNING: Avisos (algo pode estar errado)
                   - ERROR: Erros (algo falhou)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {level}: {message}")
    
    def __repr__(self) -> str:
        """
        Representação string do agente (útil para debug).
        
        Returns:
            String no formato: NomeDoAgente(created_at=timestamp)
        """
        return f"{self.name}(created_at={self.created_at})"

