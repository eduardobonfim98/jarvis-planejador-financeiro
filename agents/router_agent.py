"""
RouterAgent - Agente central de roteamento usando LLM.

Este agente analisa mensagens e decide qual agente deve processar,
identificando ambiguidades e direcionando para o tratamento apropriado.

Responsabilidades:
- Analisar mensagem do usuário usando LLM
- Detectar intenção principal (registro, consulta, setup, etc)
- Identificar ambiguidades e casos que precisam esclarecimento
- Decidir rota apropriada (finance, setup, clarification)
- Retornar contexto de ambiguidade quando necessário

Fluxo:
1. Recebe mensagem do usuário
2. LLM analisa e detecta intenção + ambiguidades
3. Retorna rota + contexto para o workflow
"""

import json
import re
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from config import GEMINI_API_KEY, GEMINI_MODEL, GOOGLE_CLOUD_PROJECT
from llm_client import create_llm_client
from database import get_connection


class RouterAgent(BaseAgent):
    """
    RouterAgent - Agente central de roteamento inteligente.
    
    Usa LLM para analisar mensagens e decidir qual agente deve processar,
    identificando ambiguidades que precisam de esclarecimento.
    """
    
    def __init__(self):
        """
        Inicializa o RouterAgent com LLM Gemini.
        
        O LLM é essencial para este agente funcionar corretamente.
        """
        super().__init__("RouterAgent")
        
        # Configura LLM (Gemini API ou Vertex AI) para roteamento inteligente
        if GEMINI_API_KEY:
            try:
                self.llm_client = create_llm_client(
                    api_key=GEMINI_API_KEY,
                    model_name=GEMINI_MODEL,
                    project_id=GOOGLE_CLOUD_PROJECT
                )
                self.model = self.llm_client.model
                self.log(f"LLM configurado ({self.llm_client.client_type}, {GEMINI_MODEL}) para roteamento inteligente")
            except Exception as e:
                self.llm_client = None
                self.model = None
                self.log(f"Erro ao configurar LLM: {e}. Roteamento limitado", "ERROR")
        else:
            self.llm_client = None
            self.model = None
            self.log("LLM não configurado - roteamento limitado", "WARNING")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal de processamento do RouterAgent.
        
        Implementa a interface BaseAgent.process().
        Chama route() internamente para manter compatibilidade.
        
        Args:
            data: Dicionário com estado do grafo ou dados de roteamento
        
        Returns:
            Dicionário com resultado do roteamento
        """
        return self.route(data)
    
    def route(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa mensagem e decide rota usando LLM.
        
        Args:
            state: Estado do grafo contendo:
                - user_phone: ID do usuário
                - message: Mensagem do usuário
                - setup_step: Etapa do setup (se em andamento)
        
        Returns:
            Dicionário com:
                - route: "finance" | "setup" | "clarification"
                - intent: Intenção detectada
                - confidence: Confiança (0-1)
                - needs_clarification: Se precisa esclarecimento
                - clarification_context: Contexto do que precisa ser esclarecido
                - ambiguity_cases: Lista de ambiguidades detectadas
        """
        user_phone = state.get("user_phone")
        message = state.get("message", "")
        setup_step = state.get("setup_step")
        
        # Se está em setup, roteia direto para SetupAgent
        if setup_step:
            self.log(f"Setup em andamento ({setup_step}) - roteando para SetupAgent")
            return {
                "route": "setup",
                "intent": "setup",
                "confidence": 1.0,
                "needs_clarification": False,
                "clarification_context": None,
                "ambiguity_cases": []
            }
        
        # Se não tem LLM, usa roteamento básico
        if not self.llm_client or not self.llm_client.model:
            return self._route_basic(message)
        
        # Busca contexto do usuário
        user_context = self._get_user_context(user_phone)
        
        # Usa LLM para análise inteligente
        return self._route_with_llm(message, user_context)
    
    def _get_user_context(self, user_phone: str) -> Dict[str, Any]:
        """
        Busca contexto do usuário no banco de dados.
        
        Returns:
            Dicionário com informações do usuário
        """
        try:
            with get_connection() as conn:
                user = conn.execute(
                    "SELECT user_name, setup_step FROM users WHERE user_phone = ?",
                    (user_phone,)
                ).fetchone()
                
                if user:
                    return {
                        "exists": True,
                        "name": user["user_name"],
                        "setup_step": user["setup_step"],
                        "setup_complete": user["setup_step"] is None
                    }
                else:
                    return {
                        "exists": False,
                        "name": None,
                        "setup_step": None,
                        "setup_complete": False
                    }
        except Exception as e:
            self.log(f"Erro ao buscar contexto do usuário: {e}", "ERROR")
            return {
                "exists": False,
                "name": None,
                "setup_step": None,
                "setup_complete": False
            }
    
    def _route_basic(self, message: str) -> Dict[str, Any]:
        """
        Roteamento básico sem LLM (fallback).
        
        Usa heurísticas simples quando LLM não está disponível.
        """
        msg_lower = message.lower().strip()
        
        # Palavras-chave para setup
        setup_keywords = ["cadastrar", "configurar", "setup", "começar", "iniciar"]
        if any(keyword in msg_lower for keyword in setup_keywords):
            return {
                "route": "setup",
                "intent": "setup",
                "confidence": 0.7,
                "needs_clarification": False,
                "clarification_context": None,
                "ambiguity_cases": []
            }
        
        # Default: finance
        return {
            "route": "finance",
            "intent": "process",
            "confidence": 0.5,
            "needs_clarification": False,
            "clarification_context": None,
            "ambiguity_cases": []
        }
    
    def _route_with_llm(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteamento inteligente usando LLM.
        
        O LLM analisa a mensagem e identifica:
        - Intenção principal
        - Ambiguidades
        - Rota apropriada
        """
        # Se usuário não existe, é setup
        if not user_context.get("exists"):
            return {
                "route": "setup",
                "intent": "setup",
                "confidence": 1.0,
                "needs_clarification": False,
                "clarification_context": None,
                "ambiguity_cases": []
            }
        
        # Cria prompt para o LLM
        prompt = f"""Você é um roteador inteligente que analisa mensagens e decide qual agente deve processar.

**Mensagem do usuário:** "{message}"

**Contexto do usuário:**
- Nome: {user_context.get('name', 'Não informado')}
- Setup completo: {user_context.get('setup_complete', False)}

**Sua tarefa:**
1. Identifique a intenção principal:
   - REGISTRO: registrar gasto (ex: "gastei 50 reais", "paguei 30")
   - CONSULTA: ver gastos (ex: "quanto gastei?", "resumo")
   - CONSULTA_LIMITES: ver limites (ex: "meus limites", "limites")
   - LISTAR_CATEGORIAS: listar todas as categorias (ex: "me mostre minhas categorias", "quais são minhas categorias?", "listar categorias")
   - ADICIONAR_CATEGORIA: criar categoria (ex: "adicionar categoria Pets")
   - SETUP: configurar sistema (ex: "quero me cadastrar", "configurar")
   - AJUDA: ajuda/informação (ex: "oi", "como funciona?")
   - FORA_ESCOPO: não relacionado a finanças (ex: "qual o tamanho do brasil")

2. Identifique AMBIGUIDADES (seja flexível):
   - Apenas ambiguidades CRÍTICAS que realmente impedem processamento
   - Permita suposições razoáveis (ex: "50" = R$ 50,00, não R$ 0,50)
   - Use contexto para inferir informações faltantes quando possível
   - Só peça esclarecimento se realmente não conseguir processar

3. Decida a ROTA:
   - "setup": se intenção é SETUP ou usuário não completou setup
   - "finance": se intenção é REGISTRO, CONSULTA, CONSULTA_LIMITES, LISTAR_CATEGORIAS, ADICIONAR_CATEGORIA, AJUDA
   - "clarification": APENAS se houver ambiguidade CRÍTICA que realmente impede processamento

4. Se houver ambiguidade CRÍTICA, identifique:
   - O que está faltando ou ambíguo
   - Qual informação precisa ser esclarecida
   - Qual agente deve fazer o esclarecimento (finance ou setup)

**IMPORTANTE:**
- Seja FLEXÍVEL: permita suposições razoáveis baseadas em contexto
- Confie no LLM para inferir informações quando possível
- Só use route="clarification" para ambiguidades REALMENTE críticas
- Prefira processar com suposições razoáveis do que pedir esclarecimento
- Retorne JSON válido

**Formato de resposta:**
```json
{{
  "intent": "registro|consulta|consulta_limites|listar_categorias|adicionar_categoria|setup|ajuda|fora_escopo",
  "route": "finance|setup|clarification",
  "confidence": 0.0-1.0,
  "needs_clarification": true|false,
  "ambiguity_cases": ["descrição da ambiguidade 1", "descrição da ambiguidade 2"],
  "clarification_context": {{
    "missing_info": "o que está faltando",
    "ambiguous_field": "campo ambíguo",
    "target_agent": "finance|setup",
    "suggestion": "sugestão de pergunta para esclarecimento"
  }}
}}
```

**Exemplos:**

Mensagem: "gastei 50"
{{
  "intent": "registro",
  "route": "clarification",
  "confidence": 0.9,
  "needs_clarification": true,
  "ambiguity_cases": ["Categoria não especificada"],
  "clarification_context": {{
    "missing_info": "categoria",
    "ambiguous_field": "categoria",
    "target_agent": "finance",
    "suggestion": "Em qual categoria devo registrar? (ex: Alimentação, Transporte)"
  }}
}}

Mensagem: "gastei 50 reais no mercado"
{{
  "intent": "registro",
  "route": "finance",
  "confidence": 0.95,
  "needs_clarification": false,
  "ambiguity_cases": [],
  "clarification_context": null
}}

Mensagem: "quanto gastei?"
{{
  "intent": "consulta",
  "route": "finance",
  "confidence": 0.9,
  "needs_clarification": false,
  "ambiguity_cases": [],
  "clarification_context": null
}}

Mensagem: "paguei"
{{
  "intent": "registro",
  "route": "finance",
  "confidence": 0.7,
  "needs_clarification": false,
  "ambiguity_cases": [],
  "clarification_context": null
}}
Nota: Deixe o FinanceAgent lidar com a ambiguidade - ele pode pedir esclarecimento se necessário, mas tente processar primeiro.

JSON:"""
        
        try:
            # Chama LLM
            response = self.llm_client.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extrai JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response_text
            
            # Faz parse
            result = json.loads(json_text)
            
            self.log(f"Rota detectada: {result.get('route')} (intent: {result.get('intent')}, confidence: {result.get('confidence')})")
            
            if result.get("needs_clarification"):
                self.log(f"Ambiguidade detectada: {result.get('ambiguity_cases')}")
            
            return {
                "route": result.get("route", "finance"),
                "intent": result.get("intent", "process"),
                "confidence": float(result.get("confidence", 0.5)),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_context": result.get("clarification_context"),
                "ambiguity_cases": result.get("ambiguity_cases", [])
            }
        
        except json.JSONDecodeError as e:
            self.log(f"Erro ao fazer parse do JSON do LLM: {e}", "ERROR")
            self.log(f"Resposta do LLM: {response_text[:200]}", "ERROR")
            # Fallback para roteamento básico
            return self._route_basic(message)
        
        except Exception as e:
            self.log(f"Erro ao rotear com LLM: {e}", "ERROR")
            # Fallback para roteamento básico
            return self._route_basic(message)

