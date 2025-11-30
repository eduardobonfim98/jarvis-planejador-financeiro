"""Estado compartilhado do grafo LangGraph."""

from typing import TypedDict, Optional, Any, Dict


class GraphState(TypedDict):
    """
    Estado compartilhado entre todos os nós do grafo.
    
    Campos:
    - user_phone: Telefone/ID do usuário
    - message: Mensagem original do usuário
    - intent: Intenção detectada (setup, registro, consulta, etc)
    - route: Rota decidida pelo RouterAgent (finance, setup, clarification)
    - confidence: Confiança na detecção (0-1)
    - action: Ação a ser executada
    - response: Resposta final para o usuário
    - data: Dados adicionais (transações, totais, etc.)
    - error: Mensagem de erro, se houver
    - setup_step: Etapa atual do setup (start, categories, limits)
    - setup_complete: Se a configuração foi concluída
    - needs_clarification: Se precisa esclarecimento antes de processar
    - clarification_context: Contexto do que precisa ser esclarecido
    - pending_intent: Intenção pendente após esclarecimento
    - clarification_attempts: Número de tentativas de esclarecimento (para evitar loops infinitos)
    """
    user_phone: str
    message: str
    intent: Optional[str]
    route: Optional[str]  # Rota decidida pelo RouterAgent: "finance" | "setup" | "clarification"
    confidence: Optional[float]
    action: Optional[str]
    response: Optional[str]
    data: Optional[Any]
    error: Optional[str]
    setup_step: Optional[str]
    setup_complete: Optional[bool]
    needs_clarification: Optional[bool]
    clarification_context: Optional[Dict[str, Any]]
    pending_intent: Optional[str]
    clarification_attempts: Optional[int]  # Contador de tentativas de esclarecimento

