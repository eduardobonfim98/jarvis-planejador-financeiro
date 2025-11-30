"""OutputAgent - Valida e modera respostas usando LLM."""

from typing import Dict, Any
import os
from agents.base_agent import BaseAgent
from config import GEMINI_MODEL, GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT
from llm_client import create_llm_client


class OutputAgent(BaseAgent):
    """
    Agente responsável por validar e moderar respostas finais usando LLM.
    
    Combina as funcionalidades de ValidadorAgent e ModeratorAgent em um único agente inteligente.
    """
    
    def __init__(self):
        super().__init__("OutputAgent")
        
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
                self.log(f"LLM configurado ({self.llm_client.client_type}, {GEMINI_MODEL}) para validação inteligente")
            except Exception as e:
                self.llm_client = None
                self.model = None
                self.log(f"Erro ao configurar LLM: {e}. Usando fallback", "WARNING")
        else:
            self.llm_client = None
            self.model = None
            self.log("LLM não configurado - usando fallback", "WARNING")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e modera resposta usando LLM Gemini.
        
        O LLM verifica:
        - Resposta está completa e coerente?
        - Tom é amigável e profissional?
        - Tem informações necessárias?
        - Precisa adicionar/ajustar emojis?
        - Formatação Markdown está correta?
        
        Args:
            data: {
                "response": str (resposta a validar),
                "intent": str (intenção detectada),
                "user_phone": str (opcional)
            }
            
        Returns:
            {
                "response": str (resposta melhorada),
                "valid": bool,
                "error": str (se houver)
            }
        """
        response = data.get("response", "")
        intent = data.get("intent", "")
        
        # Validação básica de segurança (não usa LLM - rápido)
        if not response or len(response.strip()) == 0:
            self.log("Resposta vazia detectada", "ERROR")
            return {
                **data,
                "response": "Desculpe, não consegui gerar uma resposta.",
                "valid": False,
                "error": "Resposta vazia"
            }
        
        # Trunca se muito longo (aumentado para permitir respostas mais detalhadas)
        if len(response) > 8000:
            response = response[:8000]
            self.log("Resposta truncada para 8000 caracteres", "WARNING")
        
        # Se não tem LLM, retorna com validação básica
        if not self.llm_client or not self.llm_client.model:
            self.log("Usando fallback sem LLM")
            return {
                **data,
                "response": response,
                "valid": True,
                "error": None
            }
        
        # Usa LLM para validar e melhorar APENAS se necessário
        # Verifica se a resposta já está bem formatada antes de modificar
        try:
            # Verifica se resposta já tem formatação adequada
            has_emojis = any(emoji in response for emoji in ["✅", "❌", "⚠️", "💰", "📊", "🎉", "📝", "📋", "🔴", "🟡", "🟢"])
            has_markdown = "*" in response or "_" in response or "`" in response
            is_well_formatted = has_emojis and has_markdown and len(response) > 20
            
            # Se já está bem formatada, retorna sem modificar
            if is_well_formatted:
                self.log("Resposta já bem formatada, retornando sem modificação")
                return {
                    **data,
                    "response": response,
                    "valid": True,
                    "error": None
                }
            
            # Só modifica se realmente necessário
            prompt = f"""Você é um validador e moderador de respostas de chatbot financeiro.

**Contexto:** {intent}

**Resposta a validar:**
"{response}"

**Sua tarefa:**
1. Se a resposta já está boa e formatada, retorne ela EXATAMENTE como está, sem mudanças
2. Se precisa melhorar, faça APENAS ajustes mínimos:
   - Adicione emojis apropriados se não tiver (✅ ❌ ⚠️ 💰 📊 🎉 📝)
   - Corrija erros de formatação Markdown APENAS se houver problemas
3. NUNCA altere números, valores ou informações importantes
4. Mantenha o português brasileiro natural

**IMPORTANTE:**
- Se a resposta já está perfeita, retorne ela EXATAMENTE como está
- Não invente informações novas
- Mantenha números e valores exatos
- Faça mudanças MÍNIMAS apenas se necessário
- Retorne APENAS a resposta melhorada, SEM explicações ou comentários

**Resposta melhorada:**"""
            
            # Usa LLMClient que funciona com ambas as APIs
            result = self.llm_client.generate_content(prompt)
            improved_response = result.text.strip()
            
            # Se a resposta melhorada estiver vazia, usa a original
            if not improved_response:
                self.log("LLM retornou resposta vazia, usando original", "WARNING")
                improved_response = response
            
            self.log("Resposta validada e melhorada com LLM (apenas se necessário)")
            
            return {
                **data,
                "response": improved_response,
                "valid": True,
                "error": None
            }
        
        except Exception as e:
            self.log(f"Erro no LLM de validação: {e}", "ERROR")
            # Fallback: retorna original sem modificação
            # Isso garante que o usuário sempre recebe uma resposta
            return {
                **data,
                "response": response if response else "Desculpe, não consegui processar sua solicitação.",
                "valid": True,
                "error": f"Erro no LLM: {str(e)}"
            }

