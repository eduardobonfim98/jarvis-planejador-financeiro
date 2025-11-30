"""SetupAgent - Agente responsável por configuração inicial usando LLM."""

from typing import Dict, Any, Optional
import os
import json
from agents.base_agent import BaseAgent
from tools import SQLTool
from database import get_connection
from config import GEMINI_MODEL, GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT
from llm_client import create_llm_client


class SetupAgent(BaseAgent):
    """
    Agente responsável por configuração inicial do usuário.
    
    Usa LLM Gemini para interpretar TODAS as respostas do usuário de forma flexível.
    Fluxo simplificado:
    1. Boas-vindas + pede nome
    2. Cria categorias padrão + pergunta se quer adicionar mais
    3. Define limites (opcional)
    4. Conclui setup
    """
    
    def __init__(self):
        super().__init__("SetupAgent")
        
        # Configura LLM (Gemini API ou Vertex AI)
        # O LLMClient detecta automaticamente qual usar baseado na chave
        if GEMINI_API_KEY:
            try:
                self.llm_client = create_llm_client(
                    api_key=GEMINI_API_KEY,
                    model_name=GEMINI_MODEL,
                    project_id=GOOGLE_CLOUD_PROJECT
                )
                self.model = self.llm_client.model  # Compatibilidade com código existente
                self.log(f"LLM configurado ({self.llm_client.client_type}, {GEMINI_MODEL})")
            except Exception as e:
                self.llm_client = None
                self.model = None
                self.log(f"Erro ao configurar LLM: {e}. Usando fallback", "WARNING")
        else:
            self.llm_client = None
            self.model = None
            self.log("LLM não configurado - usando fallback", "WARNING")
        
        # Categorias padrão
        self.default_categories = [
            {"name": "Alimentação", "description": "Mercado, supermercado"},
            {"name": "Delivery", "description": "iFood, Rappi, pedidos"},
            {"name": "Transporte", "description": "Uber, combustível, ônibus"},
            {"name": "Moradia", "description": "Aluguel, condomínio, contas"},
            {"name": "Lazer", "description": "Cinema, festas, diversão"},
            {"name": "Farmácia", "description": "Remédios, medicamentos"},
            {"name": "Assinaturas", "description": "Netflix, Spotify, streaming"},
            {"name": "Investimento", "description": "Poupança, ações, aplicações"},
            {"name": "Viagem", "description": "Passagens, hospedagem, turismo"},
        ]
        
        self.log("SetupAgent inicializado")
    
    def handle_clarification(self, user_phone: str, message: str, clarification_context: Dict[str, Any], setup_step: str) -> Dict[str, Any]:
        """
        Processa resposta de esclarecimento do usuário durante o setup.
        
        Args:
            user_phone: ID do usuário
            message: Resposta do usuário ao esclarecimento
            clarification_context: Contexto do esclarecimento
            setup_step: Etapa atual do setup
        
        Returns:
            Dicionário com resultado do processamento
        """
        self.log(f"Processando esclarecimento no setup - etapa: {setup_step}")
        
        # Roteia para a etapa apropriada com a mensagem de esclarecimento
        if setup_step == "get_name":
            return self.get_user_name(user_phone, message)
        elif setup_step == "categories":
            return self.handle_categories(user_phone, message)
        elif setup_step == "limits":
            return self.handle_limits(user_phone, message)
        else:
            # Fallback: processa normalmente
            return self.process({
                "user_phone": user_phone,
                "message": message,
                "setup_step": setup_step
            })
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa configuração usando LLM para interpretar tudo.
        
        Args:
            data: {
                "user_phone": str,
                "message": str,
                "setup_step": str (opcional)
            }
        """
        user_phone = data["user_phone"]
        message = data.get("message", "")
        setup_step = data.get("setup_step", "start")
        
        # Garante que usuário existe
        SQLTool.get_or_create_user(user_phone)
        
        self.log(f"Processando setup - etapa: {setup_step}")
        
        # Roteia para etapa apropriada
        if setup_step == "start":
            return self.start_setup(user_phone)
        elif setup_step == "get_name":
            return self.get_user_name(user_phone, message)
        elif setup_step == "categories":
            return self.handle_categories(user_phone, message)
        elif setup_step == "limits":
            return self.handle_limits(user_phone, message)
        else:
            return self.start_setup(user_phone)
    
    def start_setup(self, user_phone: str) -> Dict[str, Any]:
        """Inicia processo de configuração."""
        self.log("Iniciando configuração")
        
        response = """
🎉 *Olá! Eu sou o Jarvis!*

Seu assistente financeiro pessoal inteligente.

*Como eu funciono:*
📝 Você me conta seus gastos em linguagem natural
💰 Eu organizo tudo automaticamente em categorias
📊 Você consulta quanto gastou a qualquer momento

*Vamos começar o seu cadastro!*

*Primeiro, me diga: qual é o seu nome?*

(Isso me ajuda a personalizar as mensagens para você 😊)
        """.strip()
        
        self._save_setup_step(user_phone, "get_name")
        
        return {
            "success": True,
            "response": response,
            "setup_complete": False,
            "next_step": "get_name"
        }
    
    def get_user_name(self, user_phone: str, message: str) -> Dict[str, Any]:
        """
        Recebe e salva o nome do usuário com validação de ambiguidade.
        
        Valida:
        - Nome vazio ou muito curto
        - Nome apenas com números
        - Nome apenas com caracteres especiais
        - Nome ambíguo (ex: "sim", "não")
        """
        user_name = message.strip()
        
        # Validação: nome vazio ou muito curto
        if not user_name or len(user_name) < 2:
            return {
                "success": False,
                "response": "❓ Nome muito curto ou vazio. Por favor, me diga seu nome completo:",
                "setup_complete": False,
                "next_step": "get_name",
                "needs_clarification": True
            }
        
        # Validação: apenas números
        if user_name.isdigit():
            return {
                "success": False,
                "response": "❓ Isso parece ser um número. Por favor, me diga seu nome (ex: João, Maria, Pedro):",
                "setup_complete": False,
                "next_step": "get_name",
                "needs_clarification": True
            }
        
        # Validação: palavras ambíguas
        ambiguous_words = ["sim", "não", "ok", "pronto", "continuar", "n"]
        if user_name.lower() in ambiguous_words:
            return {
                "success": False,
                "response": "❓ Isso parece ser uma resposta de confirmação. Por favor, me diga seu nome real (ex: João, Maria, Pedro):",
                "setup_complete": False,
                "next_step": "get_name",
                "needs_clarification": True
            }
        
        # Validação: apenas caracteres especiais
        if not any(c.isalnum() for c in user_name):
            return {
                "success": False,
                "response": "❓ Não consegui identificar um nome válido. Por favor, me diga seu nome (ex: João, Maria, Pedro):",
                "setup_complete": False,
                "next_step": "get_name",
                "needs_clarification": True
            }
        
        # Normaliza nome (primeira letra maiúscula)
        user_name = user_name.title()
        
        # Salva nome
        conn = get_connection()
        conn.execute("UPDATE users SET user_name = ? WHERE user_phone = ?", (user_name, user_phone))
        conn.commit()
        
        self.log(f"Nome salvo: {user_name}")
        
        # Cria categorias padrão automaticamente
        created = []
        for cat in self.default_categories:
            try:
                SQLTool.create_category(user_phone, cat["name"], cat["description"])
                created.append(cat["name"])
            except:
                pass
        
        response = f"""
Prazer em te conhecer, *{user_name}*! 👋

✅ *Criei {len(created)} categorias padrão para você:*
{chr(10).join(f"• {name}" for name in created)}

📝 *Quer adicionar alguma categoria personalizada?*

Exemplos: Pets, Academia, Roupas, Educação, Reforma

⚠️ *Importante:* Se eu não conseguir identificar a categoria de um gasto, ele vai para "Geral" automaticamente! 😊

Envie o nome da categoria ou digite *"não"* para continuar.
        """.strip()
        
        self._save_setup_step(user_phone, "categories")
        
        return {
            "success": True,
            "response": response,
            "setup_complete": False,
            "next_step": "categories"
        }
    
    def handle_categories(self, user_phone: str, message: str) -> Dict[str, Any]:
        """
        Processa resposta sobre categorias usando LLM.
        
        O LLM interpreta:
        - Se quer adicionar categoria (extrai nome)
        - Se disse "não" ou "pronto" (continua)
        - Qualquer outra coisa (responde apropriadamente)
        """
        if not self.model:
            # Fallback simples sem LLM
            msg_lower = message.lower().strip()
            if "n" in msg_lower[:3] or "pronto" in msg_lower:
                return self._finish_categories(user_phone)
            else:
                # Tenta criar categoria
                category_name = message.strip().title()
                try:
                    SQLTool.create_category(user_phone, category_name, f"Categoria: {category_name}")
                    return {
                        "success": True,
                        "response": f"✅ Categoria *{category_name}* criada!\n\nQuer adicionar mais? Envie o nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"❌ Erro ao criar categoria. Tente outro nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
        
        # Usa LLM para interpretar
        if not self.llm_client or not self.llm_client.model:
            # Fallback simples sem LLM
            msg_lower = message.lower().strip()
            if "n" in msg_lower[:3] or "pronto" in msg_lower:
                return self._finish_categories(user_phone)
            else:
                # Tenta criar categoria
                category_name = message.strip().title()
                try:
                    SQLTool.create_category(user_phone, category_name, f"Categoria: {category_name}")
                    return {
                        "success": True,
                        "response": f"✅ Categoria *{category_name}* criada!\n\nQuer adicionar mais? Envie o nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"❌ Erro ao criar categoria. Tente outro nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
        
        try:
            prompt = f"""Você é um assistente que interpreta respostas sobre categorias financeiras.

Mensagem do usuário: "{message}"

Contexto: O usuário acabou de receber as categorias padrão e foi perguntado se quer adicionar categorias personalizadas.

**Sua tarefa:** Interprete a intenção e retorne JSON:

{{
  "action": "add_category" | "finish" | "other",
  "category_name": "NomeDaCategoria" (apenas se action="add_category"),
  "response": "resposta ao usuário" (apenas se action="other")
}}

Exemplos:
- "Pets" → {{"action": "add_category", "category_name": "Pets"}}
- "Quero adicionar Academia" → {{"action": "add_category", "category_name": "Academia"}}
- "não" ou "pronto" ou "continuar" → {{"action": "finish"}}
- "o que são categorias?" → {{"action": "other", "response": "Categorias são grupos onde seus gastos são organizados. Ex: Alimentação, Transporte, etc."}}

**IMPORTANTE - Tratamento de Ambiguidade:**
- Se o nome da categoria não estiver claro (ex: "sim" pode ser nome ou confirmação), use action="other" e pergunte
- Se a resposta estiver ambígua (ex: "talvez"), use action="other" e pergunte se quer adicionar ou não
- Se TUDO estiver claro, use action="add_category" ou action="finish"
- Retorne APENAS JSON válido
- category_name com primeira letra maiúscula
- Se for pergunta ou dúvida, use action="other" e responda de forma amigável

JSON:"""
            
            # Usa LLMClient que funciona com ambas as APIs (Gemini API ou Vertex AI)
            response_llm = self.llm_client.generate_content(prompt)
            result_text = response_llm.text.strip()
            
            # Remove markdown se houver
            if "```" in result_text:
                result_text = result_text.split("```")[1].replace("json", "").strip()
            
            result = json.loads(result_text)
            action = result.get("action")
            
            self.log(f"LLM interpretou: action={action}")
            
            if action == "add_category":
                category_name = result.get("category_name", message.strip().title())
                
                # Validação de nome da categoria
                if not category_name or len(category_name) < 2:
                    return {
                        "success": False,
                        "response": "❓ Nome da categoria muito curto. Pode informar o nome completo?",
                        "setup_complete": False,
                        "next_step": "categories",
                        "needs_clarification": True
                    }
                
                # Validação de nome ambíguo
                ambiguous_words = ["sim", "não", "ok", "pronto", "continuar", "n", "talvez"]
                if category_name.lower() in ambiguous_words:
                    return {
                        "success": False,
                        "response": "❓ Isso parece ser uma resposta de confirmação. Qual o nome real da categoria que você quer adicionar?",
                        "setup_complete": False,
                        "next_step": "categories",
                        "needs_clarification": True
                    }
                
                try:
                    SQLTool.create_category(user_phone, category_name, f"Categoria: {category_name}")
                    self.log(f"Categoria criada: {category_name}")
                    return {
                        "success": True,
                        "response": f"✅ Categoria *{category_name}* criada!\n\nQuer adicionar mais? Envie o nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"❌ Erro ao criar categoria. Tente outro nome ou digite *não* para continuar.",
                        "setup_complete": False,
                        "next_step": "categories"
                    }
            
            elif action == "finish":
                return self._finish_categories(user_phone)
            
            else:
                # Outra resposta - usa a resposta do LLM
                llm_response = result.get("response", "Entendi! Quer adicionar alguma categoria ou digite *não* para continuar.")
                return {
                    "success": True,
                    "response": llm_response,
                    "setup_complete": False,
                    "next_step": "categories"
                }
        
        except Exception as e:
            self.log(f"Erro no LLM: {e}", "ERROR")
            # Sem fallback hardcoded - retorna erro e pede para tentar novamente
            return {
                "success": False,
                "response": "❌ Não consegui processar sua mensagem. Por favor, tente novamente ou digite *não* para continuar.",
                "setup_complete": False,
                "next_step": "categories"
            }
    
    def _finish_categories(self, user_phone: str) -> Dict[str, Any]:
        """Finaliza etapa de categorias e pergunta sobre limites."""
        self.log("Categorias finalizadas - perguntando sobre limites")
        
        response = """
✅ *Categorias configuradas!*

💰 *Definir limites de gasto?* (opcional)

Limites ajudam a controlar gastos por categoria.
Exemplo: "Alimentação 2000" (R$ 2000 por mês)

Responda: *sim* (definir limites) ou *não* (pular)
        """.strip()
        
        self._save_setup_step(user_phone, "limits")
        
        return {
            "success": True,
            "response": response,
            "setup_complete": False,
            "next_step": "limits"
        }
    
    def handle_limits(self, user_phone: str, message: str) -> Dict[str, Any]:
        """
        Processa limites usando LLM.
        
        O LLM interpreta TUDO:
        - Se quer definir limite (extrai categoria e valor)
        - Se disse "não" (finaliza setup)
        - Qualquer outra coisa (responde apropriadamente)
        
        IMPORTANTE: Sem fallback hardcoded - confia 100% no LLM.
        """
        if not self.model:
            # Sem LLM, não pode processar - retorna erro
            return {
                "success": False,
                "response": "⚠️ Sistema de IA não disponível. Por favor, tente novamente mais tarde.",
                "setup_complete": False,
                "next_step": "limits"
            }
        
        # Usa LLM para interpretar TUDO
        if not self.llm_client or not self.llm_client.model:
            # Sem LLM, não pode processar - retorna erro
            return {
                "success": False,
                "response": "⚠️ Sistema de IA não disponível. Por favor, tente novamente mais tarde.",
                "setup_complete": False,
                "next_step": "limits"
            }
        
        try:
            prompt = f"""Você é um assistente que interpreta respostas sobre limites de gasto.

Mensagem do usuário: "{message}"

Contexto: O usuário foi perguntado se quer definir limites de gasto por categoria.

**Sua tarefa:** Interprete a intenção e retorne JSON:

{{
  "action": "add_limit" | "finish" | "other",
  "category_name": "NomeDaCategoria" (apenas se action="add_limit"),
  "limit_value": número (apenas se action="add_limit"),
  "response": "resposta ao usuário" (apenas se action="other")
}}

Exemplos:
- "Alimentação 2000" → {{"action": "add_limit", "category_name": "Alimentação", "limit_value": 2000}}
- "Transporte 500" → {{"action": "add_limit", "category_name": "Transporte", "limit_value": 500}}
- "não" ou "pular" → {{"action": "finish"}}
- "o que são limites?" → {{"action": "other", "response": "Limites são valores máximos que você quer gastar por categoria no mês. Ex: Alimentação 2000 = máximo R$ 2000/mês em alimentação."}}

**IMPORTANTE - Tratamento de Ambiguidade:**
- Se o valor estiver ausente ou ambíguo (ex: "Alimentação" sem valor), use action="other" e pergunte o valor
- Se a categoria estiver ausente ou ambígua (ex: "2000" sem categoria), use action="other" e pergunte a categoria
- Se o valor estiver ambíguo (ex: "50" pode ser R$ 50 ou R$ 0,50), use action="other" e pergunte
- Se TUDO estiver claro, use action="add_limit"
- Retorne APENAS JSON válido
- category_name com primeira letra maiúscula
- limit_value deve ser um número
- Se for pergunta, use action="other" e responda

JSON:"""
            
            # Usa LLMClient que funciona com ambas as APIs (Gemini API ou Vertex AI)
            response_llm = self.llm_client.generate_content(prompt)
            result_text = response_llm.text.strip()
            
            # Extrai JSON da resposta
            if "```" in result_text:
                # Procura por bloco de código JSON
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1).strip()
                else:
                    # Tenta qualquer bloco de código
                    result_text = result_text.split("```")[1].replace("json", "").strip()
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                self.log(f"Erro ao fazer parse do JSON do LLM: {e}", "ERROR")
                self.log(f"Resposta do LLM: {result_text[:200]}", "ERROR")
                return {
                    "success": False,
                    "response": "❌ Não consegui processar sua mensagem. Por favor, tente novamente ou digite *não* para continuar.",
                    "setup_complete": False,
                    "next_step": "limits"
                }
            
            action = result.get("action")
            
            self.log(f"LLM interpretou: action={action}")
            
            if action == "add_limit":
                category_name = result.get("category_name")
                limit_value_str = result.get("limit_value")
                
                # Validação de categoria
                if not category_name or not category_name.strip():
                    return {
                        "success": False,
                        "response": "❓ Não consegui identificar a categoria. Pode informar? (ex: 'Alimentação 2000')",
                        "setup_complete": False,
                        "next_step": "limits",
                        "needs_clarification": True
                    }
                
                # Validação de valor
                if limit_value_str is None:
                    return {
                        "success": False,
                        "response": f"❓ Identifiquei a categoria '{category_name}', mas não consegui identificar o valor. Quanto é o limite? (ex: 'Alimentação 2000')",
                        "setup_complete": False,
                        "next_step": "limits",
                        "needs_clarification": True
                    }
                
                try:
                    # Converte para float (pode ser int, float ou string)
                    if isinstance(limit_value_str, (int, float)):
                        limit_value = float(limit_value_str)
                    else:
                        limit_value = float(limit_value_str)
                    
                    if limit_value <= 0:
                        return {
                            "success": False,
                            "response": "❓ O valor do limite precisa ser maior que zero. Pode informar o valor correto?",
                            "setup_complete": False,
                            "next_step": "limits",
                            "needs_clarification": True
                        }
                except (ValueError, TypeError) as e:
                    self.log(f"Erro ao converter valor: {e}", "ERROR")
                    return {
                        "success": False,
                        "response": f"❓ Não consegui entender o valor '{limit_value_str}'. Pode informar em números? (ex: 'Alimentação 2000')",
                        "setup_complete": False,
                        "next_step": "limits",
                        "needs_clarification": True
                    }
                
                # Usa LLM para encontrar a categoria mais próxima (matching inteligente)
                try:
                    category = self._find_category_with_llm(user_phone, category_name)
                    if not category:
                        return {
                            "success": False,
                            "response": f"❓ Categoria '{category_name}' não encontrada.\n\nVerifique o nome ou digite *não* para pular.",
                            "setup_complete": False,
                            "next_step": "limits",
                            "needs_clarification": True
                        }
                except Exception as e:
                    self.log(f"Erro ao buscar categoria: {e}", "ERROR")
                    import traceback
                    self.log(traceback.format_exc(), "ERROR")
                    return {
                        "success": False,
                        "response": f"❌ Erro ao buscar categoria. Tente novamente ou digite *não* para pular.",
                        "setup_complete": False,
                        "next_step": "limits"
                    }
                
                try:
                    SQLTool.create_limit_rule(user_phone, category["category_id"], "mensal", limit_value)
                    # Usa o nome correto da categoria encontrada pelo LLM
                    correct_name = category["category_name"]
                    self.log(f"Limite criado: {correct_name} = R$ {limit_value}")
                    return {
                        "success": True,
                        "response": f"✅ Limite registrado: *{correct_name}* = R$ {limit_value:,.2f}/mês\n\nQuer definir mais limites? Ou digite *não* para finalizar.",
                        "setup_complete": False,
                        "next_step": "limits"
                    }
                except Exception as e:
                    self.log(f"Erro ao criar limite: {e}", "ERROR")
                    import traceback
                    self.log(traceback.format_exc(), "ERROR")
                    return {
                        "success": False,
                        "response": f"❌ Erro ao criar limite. Tente novamente ou digite *não* para pular.",
                        "setup_complete": False,
                        "next_step": "limits"
                    }
            
            elif action == "finish":
                return self._finish_setup(user_phone)
            
            else:
                # Outra resposta
                llm_response = result.get("response", "Entendi! Quer definir um limite? Envie: *Categoria Valor* ou digite *não* para finalizar.")
                return {
                    "success": True,
                    "response": llm_response,
                    "setup_complete": False,
                    "next_step": "limits"
                }
        
        except Exception as e:
            self.log(f"Erro no LLM: {e}", "ERROR")
            # Fallback
            msg_lower = message.lower().strip()
            if "n" in msg_lower[:3]:
                return self._finish_setup(user_phone)
            return {
                "success": False,
                "response": "Não entendi. Envie: *Categoria Valor* (ex: Alimentação 2000) ou digite *não* para finalizar.",
                "setup_complete": False,
                "next_step": "limits"
            }
    
    def _finish_setup(self, user_phone: str) -> Dict[str, Any]:
        """Finaliza o setup."""
        self.log("Setup concluído")
        
        response = """
🎉 *Configuração Concluída!*

Tudo pronto para começar a usar o Jarvis!

✅ Categorias configuradas
✅ Pronto para registrar gastos

*Como usar:*
• "gastei 50 no mercado" → registra gasto
• "quanto gastei esse mês?" → consulta total
• "ajuda" → ver todos os comandos

*Vamos começar!* 🚀

Experimente: "gastei 50 reais no supermercado"
        """.strip()
        
        self._clear_setup_step(user_phone)
        
        return {
            "success": True,
            "response": response,
            "setup_complete": True,
            "next_step": None
        }
    
    def _save_setup_step(self, user_phone: str, step: str):
        """Salva o próximo passo do setup no banco."""
        conn = get_connection()
        conn.execute("UPDATE users SET setup_step = ? WHERE user_phone = ?", (step, user_phone))
        conn.commit()
        self.log(f"Setup step salvo: {step}")
    
    def _clear_setup_step(self, user_phone: str):
        """Limpa o estado de setup."""
        conn = get_connection()
        conn.execute("UPDATE users SET setup_step = NULL WHERE user_phone = ?", (user_phone,))
        conn.commit()
        self.log("Setup concluído - estado limpo")
    
    def _find_category_with_llm(self, user_phone: str, category_input: str) -> Optional[Dict[str, Any]]:
        """
        Usa LLM para encontrar a categoria mais próxima (matching inteligente).
        
        Isso resolve problemas de:
        - Erros de digitação (Alimentacao vs Alimentação)
        - Diferenças de acentuação
        - Variações de nome (Alimentação vs Alimentacao vs Alimentacao)
        """
        # Primeiro tenta busca exata
        category = SQLTool.get_category_by_name(user_phone, category_input)
        if category:
            return category
        
        # Se não encontrou, busca todas as categorias do usuário
        all_categories = SQLTool.get_user_categories(user_phone)
        if not all_categories:
            return None
        
        # Se não tem LLM, retorna None
        if not self.llm_client or not self.llm_client.model:
            return None
        
        # Usa LLM para encontrar a categoria mais próxima
        try:
            category_names = [cat["category_name"] for cat in all_categories]
            
            prompt = f"""Você é um assistente que faz matching inteligente de categorias.

**Categoria que o usuário digitou:** "{category_input}"

**Categorias disponíveis:**
{chr(10).join(f"- {name}" for name in category_names)}

**Sua tarefa:** Encontre a categoria mais próxima da que o usuário digitou.

Considere:
- Erros de digitação (ex: "Alimentacao" → "Alimentação")
- Diferenças de acentuação
- Variações de nome
- Similaridade fonética

Retorne APENAS o nome exato da categoria mais próxima, ou "NENHUMA" se não houver correspondência razoável.

Categoria mais próxima:"""
            
            # Usa LLMClient que funciona com ambas as APIs
            response_llm = self.llm_client.generate_content(prompt)
            matched_name = response_llm.text.strip()
            
            # Remove aspas se houver
            matched_name = matched_name.strip('"\'')
            
            if matched_name.upper() == "NENHUMA" or matched_name == "":
                return None
            
            # Busca a categoria encontrada pelo LLM
            for cat in all_categories:
                if cat["category_name"].lower() == matched_name.lower():
                    self.log(f"LLM encontrou categoria: '{category_input}' → '{cat['category_name']}'")
                    return cat
            
            return None
            
        except Exception as e:
            self.log(f"Erro no LLM de matching: {e}", "ERROR")
            return None
