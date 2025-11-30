"""Workflow LangGraph para orquestração dos agentes."""

from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import GraphState
from agents import PartnerAgent, FinanceAgent, SetupAgent, OutputAgent, RouterAgent


# Instâncias globais dos agentes
partner_agent = PartnerAgent()
router_agent = RouterAgent()
finance_agent = FinanceAgent()
setup_agent = SetupAgent()
output_agent = OutputAgent()


def partner_node(state: GraphState) -> GraphState:
    """
    Nó do PartnerAgent: valida segurança + verifica setup em andamento.
    """
    partner_agent.log(f"Validando mensagem: '{state['message']}'")
    
    # Valida segurança
    result = partner_agent.process({"message": state["message"]})
    
    # Se inválido, termina
    if not result.get("valid"):
        partner_agent.log(f"Mensagem bloqueada: {result['error']}", "WARNING")
        return {
            **state,
            "intent": "invalid",
            "error": result["error"],
            "response": f"❌ {result['error']}"
        }
    
    # Verifica se usuário existe no banco
    from database import get_connection
    conn = get_connection()
    user = conn.execute(
        "SELECT user_name, setup_step FROM users WHERE user_phone = ?",
        (state["user_phone"],)
    ).fetchone()
    
    # Se usuário NÃO existe, é a primeira vez! Inicia setup automaticamente
    if not user:
        partner_agent.log("NOVO USUÁRIO! Iniciando apresentação + setup")
        
        # Cria o usuário no banco
        from tools import SQLTool
        SQLTool.get_or_create_user(state["user_phone"])
        
        # Define setup_step como "start" para começar o fluxo
        conn.execute(
            "UPDATE users SET setup_step = ? WHERE user_phone = ?",
            ("start", state["user_phone"])
        )
        conn.commit()
        
        return {
            **state,
            "message": result["cleaned_message"],
            "intent": "setup",
            "setup_step": "start",
            "action": "setup",
        }
    
    # Se usuário está em processo de setup - roteia direto
    if user and user["setup_step"]:
        partner_agent.log(f"Setup em andamento: {user['setup_step']}")
        return {
            **state,
            "message": result["cleaned_message"],
            "intent": "setup",
            "setup_step": user["setup_step"],
            "action": "setup",
        }
    
    # Mensagem válida - passa para RouterAgent
    partner_agent.log("Mensagem válida, encaminhando para RouterAgent")
    
    return {
        **state,
        "message": result["cleaned_message"],
        "intent": "process",
        "confidence": 1.0,
        "action": "route",
    }


def router_node(state: GraphState) -> GraphState:
    """
    Nó do RouterAgent: analisa mensagem e decide rota usando LLM.
    
    O RouterAgent identifica:
    - Intenção principal
    - Ambiguidades que precisam esclarecimento
    - Rota apropriada (finance, setup, clarification)
    """
    router_agent.log("Analisando mensagem e decidindo rota")
    
    # Roteia usando RouterAgent
    route_result = router_agent.route(state)
    
    # Atualiza estado com informações do roteamento
    # IMPORTANTE: Salva o campo "route" que o RouterAgent retorna
    updated_state = {
        **state,
        "route": route_result.get("route", "finance"),  # Rota decidida pelo RouterAgent
        "intent": route_result.get("intent"),
        "confidence": route_result.get("confidence"),
        "needs_clarification": route_result.get("needs_clarification", False),
        "clarification_context": route_result.get("clarification_context"),
    }
    
    # Se precisa esclarecimento, salva intenção pendente
    if route_result.get("needs_clarification"):
        updated_state["pending_intent"] = route_result.get("intent")
        router_agent.log(f"Ambiguidade detectada: {route_result.get('ambiguity_cases')}")
        # Se é uma nova ambiguidade (não é continuação), reseta contador
        # Se já havia tentativas, mantém o contador (será incrementado no clarification_node)
        if "clarification_attempts" not in state or state.get("clarification_attempts") is None:
            updated_state["clarification_attempts"] = 0
    else:
        # Se não precisa esclarecimento, reseta contador
        updated_state["clarification_attempts"] = 0
    
    router_agent.log(f"Rota decidida: {updated_state['route']} (intent: {updated_state['intent']})")
    
    return updated_state


def clarification_node(state: GraphState) -> GraphState:
    """
    Nó de esclarecimento: gera pergunta de esclarecimento e aguarda resposta.
    
    Quando RouterAgent detecta ambiguidade, este nó:
    1. Verifica se excedeu o limite de tentativas (máximo 3)
    2. Se excedeu, desiste e retorna mensagem padrão
    3. Caso contrário, gera pergunta de esclarecimento
    4. Incrementa contador de tentativas
    """
    # Limite máximo de tentativas de esclarecimento
    MAX_CLARIFICATION_ATTEMPTS = 3
    
    # Obtém número atual de tentativas
    attempts = state.get("clarification_attempts", 0)
    
    # Se excedeu o limite, deixa o LLM decidir como responder
    if attempts >= MAX_CLARIFICATION_ATTEMPTS:
        router_agent.log(f"Limite de esclarecimentos excedido ({attempts} tentativas) - deixando LLM decidir", "WARNING")
        # Em vez de mensagem fixa, roteia para FinanceAgent que vai usar LLM para responder
        return {
            **state,
            "needs_clarification": False,  # Reseta para evitar loop
            "route": "finance",  # Roteia para FinanceAgent
            "action": "process",
        }
    
    router_agent.log(f"Gerando pergunta de esclarecimento (tentativa {attempts + 1}/{MAX_CLARIFICATION_ATTEMPTS})")
    
    # Obtém contexto de esclarecimento (pode vir do RouterAgent ou do FinanceAgent)
    clarification_context = state.get("clarification_context")
    if not clarification_context:
        clarification_context = {}
    
    # Se já tem uma resposta do FinanceAgent, usa ela
    if state.get("response"):
        response = state.get("response")
    else:
        # Gera pergunta de esclarecimento baseada no contexto
        target_agent = clarification_context.get("target_agent", "finance")
        suggestion = clarification_context.get("suggestion", "Pode fornecer mais informações?")
        missing_info = clarification_context.get("missing_info", "informação")
        
        # Gera pergunta de esclarecimento
        response = f"❓ {suggestion}"
    
    return {
        **state,
        "response": response,
        "action": "clarification",
        "clarification_attempts": attempts + 1,  # Incrementa contador
        "error": None
    }


def finance_node(state: GraphState) -> GraphState:
    """
    Nó do FinanceAgent: usa LLM para TUDO.
    
    O LLM (Gemini) vai:
    - Detectar a intenção
    - Extrair informações necessárias
    - Executar ação apropriada
    - Gerar resposta natural
    - OU redirecionar para SetupAgent se detectar setup
    """
    finance_agent.log("Processando com LLM (Gemini)")
    
    # Verifica se é resposta de esclarecimento
    needs_clarification = state.get("needs_clarification", False)
    clarification_context = state.get("clarification_context")
    
    # Prepara dados - inclui contexto de esclarecimento se houver
    data = {
        "user_phone": state["user_phone"],
        "message": state["message"],
        "action": "clarification" if needs_clarification and clarification_context else "process",
        "clarification_context": clarification_context,
    }
    
    # Processa com LLM
    result = finance_agent.process(data)
    
    if result["success"]:
        # Verifica se precisa rotear para outro agente
        route_to = result.get("data", {}).get("route_to") or result.get("route_to")
        
        if route_to == "setup":
            # LLM detectou setup - redireciona
            finance_agent.log("Roteando para SetupAgent")
            return {
                **state,
                "intent": "setup",
                "action": "setup",
                "setup_step": "start",
                "error": None
            }
        
        finance_agent.log("Processamento concluído com sucesso")
        return {
            **state,
            "response": result["response"],
            "data": result.get("data"),
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_attempts": 0,  # Reseta contador ao processar com sucesso
            "error": None
        }
    else:
        # Verifica se precisa esclarecimento
        needs_clarification = result.get("needs_clarification", False)
        if needs_clarification:
            # Verifica limite de tentativas antes de pedir esclarecimento
            attempts = state.get("clarification_attempts", 0)
            MAX_ATTEMPTS = 3
            
            if attempts >= MAX_ATTEMPTS:
                finance_agent.log(f"Limite de esclarecimentos excedido ({attempts} tentativas) - deixando LLM decidir", "WARNING")
                # Em vez de mensagem fixa, usa a resposta do LLM que já detectou que não entendeu
                # O LLM já gerou uma resposta apropriada (fora_escopo ou ajuda)
                return {
                    **state,
                    "response": result.get("response", "Desculpe, não consegui entender. Como posso ajudar?"),
                    "needs_clarification": False,  # Reseta para evitar loop
                    "clarification_attempts": 0,  # Reseta contador
                    "error": None
                }
            
            finance_agent.log(f"Precisa esclarecimento (tentativa {attempts + 1}/{MAX_ATTEMPTS})")
            return {
                **state,
                "response": result["response"],
                "needs_clarification": True,
                "clarification_attempts": attempts + 1,  # Incrementa contador
                "error": None
            }
        
        # Se success=False mas há uma resposta válida, não é erro - é uma resposta informativa
        # (ex: "não é possível remover categoria com transações")
        if result.get("response") and not result.get("success", True):
            finance_agent.log(f"Resposta informativa (não é erro): {result['response'][:100]}")
            return {
                **state,
                "response": result["response"],
                "error": None  # Não é erro, é uma resposta válida
            }
        
        finance_agent.log(f"Erro no processamento: {result.get('response', 'Sem resposta')}", "ERROR")
        return {
            **state,
            "response": result.get("response", "Desculpe, tive um problema ao processar sua solicitação."),
            "error": "Erro ao processar mensagem"
        }


def setup_node(state: GraphState) -> GraphState:
    """
    Nó do SetupAgent: configuração inicial do usuário.
    """
    setup_agent.log("Processando configuração")
    
    # Verifica se é resposta de esclarecimento
    needs_clarification = state.get("needs_clarification", False)
    clarification_context = state.get("clarification_context")
    setup_step = state.get("setup_step", "start")
    
    # Prepara dados para o SetupAgent
    data = {
        "user_phone": state["user_phone"],
        "message": state["message"],
        "setup_step": setup_step,
    }
    
    # Se precisa esclarecimento, usa handle_clarification
    if needs_clarification and clarification_context:
        result = setup_agent.handle_clarification(
            state["user_phone"],
            state["message"],
            clarification_context,
            setup_step
        )
    else:
        # Processa normalmente
        result = setup_agent.process(data)
    
    if result["success"]:
        setup_agent.log(f"Setup concluído: {result.get('setup_complete', False)}")
        return {
            **state,
            "response": result["response"],
            "setup_complete": result.get("setup_complete", False),
            "setup_step": result.get("next_step"),
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_attempts": 0,  # Reseta contador ao processar com sucesso
            "error": None
        }
    else:
        # Verifica se precisa esclarecimento
        needs_clarification = result.get("needs_clarification", False)
        if needs_clarification:
            # Verifica limite de tentativas antes de pedir esclarecimento
            attempts = state.get("clarification_attempts", 0)
            MAX_ATTEMPTS = 3
            
            if attempts >= MAX_ATTEMPTS:
                setup_agent.log(f"Limite de esclarecimentos excedido no setup ({attempts} tentativas) - deixando LLM decidir", "WARNING")
                # Em vez de mensagem fixa, usa a resposta do LLM que já detectou que não entendeu
                return {
                    **state,
                    "response": result.get("response", "Desculpe, não consegui entender. Vamos continuar?"),
                    "needs_clarification": False,  # Reseta para evitar loop
                    "clarification_attempts": 0,  # Reseta contador
                    "error": None
                }
            
            setup_agent.log(f"Precisa esclarecimento no setup (tentativa {attempts + 1}/{MAX_ATTEMPTS})")
            return {
                **state,
                "response": result["response"],
                "needs_clarification": True,
                "clarification_attempts": attempts + 1,  # Incrementa contador
                "error": None
            }
        
        setup_agent.log(f"Erro no setup: {result['response']}", "ERROR")
        return {
            **state,
            "response": result["response"],
            "error": "Setup falhou"
        }


def help_node(state: GraphState) -> GraphState:
    """
    Nó para responder mensagens de ajuda.
    """
    partner_agent.log("Gerando mensagem de ajuda")
    
    help_response = partner_agent.get_help_response()
    
    return {
        **state,
        "response": help_response,
        "error": None
    }


def output_node(state: GraphState) -> GraphState:
    """
    Nó do OutputAgent: valida e modera resposta usando LLM.
    
    Combina validação e moderação em um único agente inteligente.
    Também salva a conversa no histórico.
    """
    output_agent.log("Validando e moderando resposta com LLM")
    
    # Se já houver erro, retorna com mensagem padrão
    if state.get("error"):
        output_agent.log("Erro detectado, retornando mensagem padrão")
        response = "Desculpe, tive um problema ao processar sua solicitação. Tente novamente!"
    else:
        # Prepara dados para o OutputAgent
        data = {
            "response": state.get("response", ""),
            "intent": state.get("intent"),
            "user_phone": state["user_phone"]
        }
    
        # Processa com LLM (valida + modera)
        result = output_agent.process(data)
        
        if result.get("valid"):
            output_agent.log("Resposta validada e moderada com sucesso")
            response = result["response"]  # Resposta melhorada pelo LLM
        else:
            output_agent.log(f"Erro na validação: {result.get('error')}", "ERROR")
            response = "Desculpe, não consegui processar sua solicitação corretamente."
    
    # Salva conversa no histórico
    try:
        from tools import SQLTool
        SQLTool.save_conversation(
            state["user_phone"],
            state["message"],
            response
        )
        output_agent.log("Conversa salva no histórico")
    except Exception as e:
        output_agent.log(f"Erro ao salvar histórico: {e}", "WARNING")
    
    return {
        **state,
        "response": response
    }


def route_after_partner(state: GraphState) -> Literal["router", "setup", "end"]:
    """
    Roteador: decide qual nó executar após o PartnerAgent.
    
    - invalid → END
    - setup (em andamento) → SetupAgent
    - process → RouterAgent (analisa e decide rota)
    """
    intent = state.get("intent")
    
    if intent == "invalid":
        # Mensagem bloqueada por segurança
        return "end"
    elif intent == "setup":
        # Usuário está em processo de setup
        return "setup"
    else:
        # Vai para RouterAgent para análise inteligente
        return "router"


def route_after_router(state: GraphState) -> Literal["finance", "setup", "clarification", "end"]:
    """
    Roteador: decide qual nó executar após o RouterAgent.
    
    Usa o campo "route" retornado pelo RouterAgent para decidir o próximo nó.
    O RouterAgent já fez a análise inteligente e decidiu a rota apropriada.
    
    - clarification → Nó de esclarecimento
    - setup → SetupAgent
    - finance → FinanceAgent
    - invalid → END
    """
    # Usa o campo "route" que o RouterAgent retornou
    route = state.get("route", "finance")
    needs_clarification = state.get("needs_clarification", False)
    intent = state.get("intent")
    
    # Se precisa esclarecimento, sempre vai para clarification
    if needs_clarification or route == "clarification":
        return "clarification"
    # Usa a rota decidida pelo RouterAgent
    elif route == "setup":
        return "setup"
    elif route == "finance":
        return "finance"
    elif intent == "invalid":
        # Mensagem inválida
        return "end"
    else:
        # Fallback: FinanceAgent (default)
        return "finance"


def route_after_finance(state: GraphState) -> Literal["setup", "output", "clarification"]:
    """
    Roteador: decide qual nó executar após o FinanceAgent.
    
    Se LLM detectou setup → SetupAgent (fluxo guiado)
    Se precisa esclarecimento → Clarification
    Caso contrário → Output (valida e modera com LLM)
    """
    intent = state.get("intent")
    needs_clarification = state.get("needs_clarification", False)
    
    if needs_clarification:
        # Precisa esclarecimento
        return "clarification"
    elif intent == "setup":
        # LLM detectou que usuário quer configurar
        return "setup"
    else:
        # Resposta normal - valida e modera com LLM
        return "output"


def route_after_clarification(state: GraphState) -> Literal["finance", "setup", "end"]:
    """
    Roteador: decide qual nó executar após esclarecimento.
    
    Após esclarecimento, roteia para o agente apropriado baseado na intenção pendente.
    """
    pending_intent = state.get("pending_intent")
    clarification_context = state.get("clarification_context", {})
    target_agent = clarification_context.get("target_agent", "finance")
    
    if target_agent == "setup":
        return "setup"
    elif pending_intent == "setup":
        return "setup"
    else:
        # Default: FinanceAgent processa com a nova informação
        return "finance"


def create_workflow() -> StateGraph:
    """
    Cria o workflow SIMPLIFICADO + SETUP do Jarvis.
    
    Fluxo:
    1. START → partner_node (valida segurança)
    2. partner_node → [finance_node | END]
    3. finance_node (LLM decide) → [setup_node | validator_node]
       - Se LLM detecta setup → setup_node (fluxo guiado)
       - Caso contrário → validator_node
    4. setup_node → validator_node
    5. validator_node → moderator_node
    6. moderator_node → END
    
    O FinanceAgent usa o LLM (Gemini) para:
    - Detectar intenção (registro, consulta, ajuda, setup)
    - Extrair informações
    - Gerar resposta apropriada
    
    Returns:
        StateGraph compilado pronto para execução
    """
    # Cria grafo
    workflow = StateGraph(GraphState)
    
    # Adiciona nós
    workflow.add_node("partner", partner_node)      # Valida segurança
    workflow.add_node("router", router_node)        # Analisa e decide rota
    workflow.add_node("clarification", clarification_node)  # Gera pergunta de esclarecimento
    workflow.add_node("finance", finance_node)      # Processa operações financeiras
    workflow.add_node("setup", setup_node)          # Fluxo guiado de setup
    workflow.add_node("output", output_node)        # Valida + modera com LLM
    
    # Define ponto de entrada
    workflow.set_entry_point("partner")
    
    # Roteamento após partner
    workflow.add_conditional_edges(
        "partner",
        route_after_partner,
        {
            "router": "router",   # Normal → RouterAgent (analisa)
            "setup": "setup",     # Setup em andamento → SetupAgent
            "end": END            # Inválido → END
        }
    )
    
    # Roteamento após router
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "clarification": "clarification",  # Precisa esclarecimento
            "setup": "setup",                  # Roteia para SetupAgent
            "finance": "finance",              # Roteia para FinanceAgent
            "end": END                         # Inválido → END
        }
    )
    
    # Roteamento após clarification
    workflow.add_conditional_edges(
        "clarification",
        route_after_clarification,
        {
            "finance": "finance",  # Após esclarecimento → FinanceAgent
            "setup": "setup",      # Após esclarecimento → SetupAgent
            "end": END             # Inválido → END
        }
    )
    
    # Roteamento após finance
    workflow.add_conditional_edges(
        "finance",
        route_after_finance,
        {
            "setup": "setup",          # LLM detectou setup → SetupAgent
            "clarification": "clarification",  # Precisa esclarecimento
            "output": "output"         # Normal → Output (valida + modera)
        }
    )
    
    # Setup também vai para output
    workflow.add_edge("setup", "output")
    
    # Output vai direto para END
    workflow.add_edge("output", END)
    
    # Compila grafo
    return workflow.compile()


# Cria instância global do workflow
app = create_workflow()


def run_workflow(user_phone: str, message: str) -> dict:
    """
    Executa o workflow completo para uma mensagem.
    
    Args:
        user_phone: Telefone/ID do usuário
        message: Mensagem do usuário
        
    Returns:
        Estado final com resposta
    """
    # Estado inicial
    initial_state: GraphState = {
        "user_phone": user_phone,
        "message": message,
        "intent": None,
        "route": None,  # Será definido pelo RouterAgent
        "confidence": None,
        "action": None,
        "response": None,
        "data": None,
        "error": None,
        "setup_step": None,
        "setup_complete": None,
        "needs_clarification": None,
        "clarification_context": None,
        "pending_intent": None,
        "clarification_attempts": 0,  # Inicializa contador de tentativas
        "validation_errors": None,
        "moderation_applied": None,
        "tone_adjustments": None,
    }
    
    # Executa workflow
    final_state = app.invoke(initial_state)
    
    return final_state

