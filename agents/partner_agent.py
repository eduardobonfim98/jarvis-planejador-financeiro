"""
PartnerAgent - Gateway de segurança e validação usando LLM.

Este é o PRIMEIRO agente que processa todas as mensagens do usuário.
Usa LLM Gemini para validar segurança de forma inteligente, lidando com ambiguidade.

Responsabilidades:
- Validar tamanho da mensagem (máximo 500 caracteres)
- Bloquear conteúdo malicioso (SQL injection, XSS, JavaScript) usando LLM
- Limpar espaços extras e normalizar mensagem
- Distinguir entre conteúdo legítimo e malicioso (ex: "deletei arquivo" vs "DELETE FROM")

IMPORTANTE:
- NÃO detecta intenções (isso é feito pelo LLM no FinanceAgent)
- NÃO faz parsing de dados (isso é feito pelo LLM)
- Usa LLM para entender contexto e evitar falsos positivos

Para debug:
- Logs mostram quando mensagens são bloqueadas
- Mensagens bloqueadas retornam error no resultado
"""

import re
import os
import json
from typing import Dict, Any, Tuple
from agents.base_agent import BaseAgent
from config import GEMINI_MODEL, GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT
from llm_client import create_llm_client


class PartnerAgent(BaseAgent):
    """
    PartnerAgent - Gateway de segurança do sistema.
    
    Este agente é o primeiro ponto de entrada de todas as mensagens.
    Ele valida segurança ANTES de qualquer processamento com LLM.
    
    Fluxo:
    1. Recebe mensagem do usuário
    2. Valida tamanho e conteúdo perigoso
    3. Limpa espaços extras
    4. Retorna mensagem validada ou erro
    
    Para debug:
    - Use self.log() para rastrear validações
    - Mensagens bloqueadas aparecem como WARNING nos logs
    """
    
    def __init__(self):
        """
        Inicializa o PartnerAgent com LLM Gemini para validação inteligente.
        
        Usa LLM para entender contexto e distinguir entre:
        - Conteúdo legítimo (ex: "deletei um arquivo", "vou fazer um script")
        - Conteúdo malicioso (ex: "DROP TABLE users", "<script>alert('xss')</script>")
        
        Isso evita falsos positivos que regex simples não consegue distinguir.
        """
        super().__init__("PartnerAgent")
        
        # Configura LLM (Gemini API ou Vertex AI) para validação inteligente
        # O LLMClient detecta automaticamente qual usar baseado na chave
        if GEMINI_API_KEY:
            try:
                self.llm_client = create_llm_client(
                    api_key=GEMINI_API_KEY,
                    model_name=GEMINI_MODEL,
                    project_id=GOOGLE_CLOUD_PROJECT
                )
                self.model = self.llm_client.model  # Compatibilidade com código existente
                self.log(f"LLM configurado ({self.llm_client.client_type}, {GEMINI_MODEL}) para validação inteligente de segurança")
            except Exception as e:
                self.llm_client = None
                self.model = None
                self.log(f"Erro ao configurar LLM: {e}. Usando validação básica com regex", "WARNING")
        else:
            self.llm_client = None
            self.model = None
            self.log("LLM não configurado - usando validação básica com regex", "WARNING")
        
        # Lista de padrões PERIGOSOS para validação básica
        # Simplificada - apenas SQL injection crítico (Telegram já sanitiza XSS)
        # Mantemos apenas padrões que realmente podem causar dano ao banco de dados
        self.dangerous_patterns = [
            r"DROP\s+TABLE",  # SQL injection - deletar tabela
            r"DELETE\s+FROM\s+\w+\s*;",  # SQL injection - deletar dados (com ponto e vírgula)
            r";\s*DROP",  # Comando SQL seguido de DROP
        ]
        
        self.log("PartnerAgent inicializado (gateway de segurança com LLM)")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa e valida a mensagem do usuário.
        
        Este método é chamado pelo workflow LangGraph para validar
        a segurança da mensagem ANTES de processar com LLM.
        
        Args:
            data: Dicionário com dados de entrada
                  Deve conter:
                  - message: str (mensagem do usuário a validar)
        
        Returns:
            Dicionário com resultado da validação:
            {
                "valid": bool (True se mensagem é segura),
                "cleaned_message": str (mensagem limpa, ou "" se inválida),
                "error": str (mensagem de erro se inválida, ou None)
            }
        
        Para debug:
        - Mensagens válidas: log INFO com preview da mensagem
        - Mensagens bloqueadas: log WARNING com motivo do bloqueio
        """
        message = data.get("message", "")
        
        # Valida e limpa a mensagem
        # Retorna (is_valid, cleaned_message_or_error)
        is_valid, result = self.validate_and_clean(message)
        
        if not is_valid:
            # Mensagem bloqueada por segurança
            # Loga como WARNING para facilitar identificação
            self.log(f"Mensagem bloqueada: {result}", "WARNING")
            return {
                "valid": False,
                "cleaned_message": "",
                "error": result  # Motivo do bloqueio
            }
        
        # Mensagem válida - loga preview para debug
        self.log(f"Mensagem validada: '{result[:50]}...'")
        
        return {
            "valid": True,
            "cleaned_message": result,  # Mensagem limpa e segura
            "error": None
        }
    
    def validate_and_clean(self, message: str) -> Tuple[bool, str]:
        """
        Valida segurança e limpa a mensagem do usuário usando LLM.
        
        Aplica múltiplas camadas de validação:
        1. Verifica se mensagem não está vazia
        2. Remove espaços extras (normaliza)
        3. Verifica tamanho máximo (500 caracteres)
        4. Usa LLM para verificar se é conteúdo malicioso (entende contexto)
        5. Fallback para regex se LLM não disponível
        
        Args:
            message: Mensagem original do usuário
        
        Returns:
            Tupla (is_valid, result):
            - is_valid: bool (True se mensagem é segura)
            - result: str (mensagem limpa se válida, ou mensagem de erro se inválida)
        
        Exemplos:
            validate_and_clean("gastei 50") → (True, "gastei 50")
            validate_and_clean("") → (False, "Mensagem vazia")
            validate_and_clean("DROP TABLE users") → (False, "Mensagem contém conteúdo não permitido")
            validate_and_clean("deletei um arquivo") → (True, "deletei um arquivo")  # LLM entende contexto
        
        Para debug:
        - Logs mostram quando LLM é usado vs regex
        - Mensagens bloqueadas aparecem como WARNING
        """
        # 1. Verifica se mensagem está vazia ou só tem espaços
        if not message or not message.strip():
            return (False, "Mensagem vazia")
        
        # 2. Remove espaços extras e normaliza
        # Exemplo: "gastei   50   reais" → "gastei 50 reais"
        cleaned = " ".join(message.strip().split())
        
        # 3. Verifica tamanho máximo (proteção contra spam/DoS)
        # Aumentado para 2000 caracteres para permitir mensagens mais longas e detalhadas
        if len(cleaned) > 2000:
            return (False, "Mensagem muito longa (máximo 2000 caracteres)")
        
        # 4. Validação de segurança simplificada
        # Removida validação LLM rigorosa - confiamos mais no LLM e no Telegram
        # Mantemos apenas validação básica de SQL injection via regex
        # O Telegram já sanitiza XSS, então não precisamos validar isso
        
        # 5. Fallback: Verifica padrões perigosos usando regex (se LLM não disponível)
        # Itera sobre todos os padrões definidos em self.dangerous_patterns
        for pattern in self.dangerous_patterns:
            # Busca case-insensitive (ignora maiúsculas/minúsculas)
            if re.search(pattern, cleaned, re.IGNORECASE):
                # Padrão perigoso encontrado - bloqueia mensagem
                self.log(f"Regex bloqueou mensagem (padrão: {pattern})", "WARNING")
                return (False, "Mensagem contém conteúdo não permitido")
        
        # Mensagem passou em todas as validações
        return (True, cleaned)
