"""
FinanceAgent - Agente responsável por operações financeiras.

Este é o agente CORE do sistema - processa todas as operações financeiras
usando LLM Gemini para interpretação inteligente de linguagem natural.

Responsabilidades:
- Detecção de intenção usando LLM (registro, consulta, ajuda, setup)
- Extração de dados de gastos (valor, categoria, descrição)
- Registro de transações no banco de dados
- Consultas de totais e relatórios
- Verificação de limites e geração de alertas
- Criação automática de categoria "Geral" se não identificar categoria

Fluxo principal:
1. Recebe mensagem do usuário
2. LLM detecta intenção e extrai dados
3. Executa ação apropriada (registrar, consultar, etc)
4. Retorna resposta formatada

Para debug:
- Logs mostram intenção detectada e dados extraídos
- Erros são logados com detalhes
- Use self.log() para rastrear fluxo de execução
"""

import re
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent
from tools import SQLTool, FormatterTool
from config import GEMINI_API_KEY, GEMINI_MODEL, GOOGLE_CLOUD_PROJECT
from llm_client import create_llm_client


class FinanceAgent(BaseAgent):
    """
    FinanceAgent - Agente principal para operações financeiras.
    
    Este agente usa LLM Gemini para:
    - Entender intenções do usuário (registro, consulta, ajuda)
    - Extrair dados de gastos de linguagem natural
    - Executar ações apropriadas (salvar, consultar, alertar)
    
    Todas as decisões são tomadas pelo LLM, garantindo flexibilidade máxima.
    """
    
    def __init__(self):
        """
        Inicializa o FinanceAgent e configura o LLM Gemini.
        
        O LLM é essencial para este agente funcionar corretamente.
        Se não houver API key, o agente não funcionará adequadamente.
        """
        super().__init__("FinanceAgent")
        
        # Configura LLM (Gemini API ou Vertex AI) para processamento inteligente
        # O LLMClient detecta automaticamente qual usar baseado na chave
        # IMPORTANTE: Este agente depende do LLM para funcionar
        if GEMINI_API_KEY:
            try:
                self.llm_client = create_llm_client(
                    api_key=GEMINI_API_KEY,
                    model_name=GEMINI_MODEL,
                    project_id=GOOGLE_CLOUD_PROJECT
                )
                self.model = self.llm_client.model  # Compatibilidade com código existente
                self.log(f"LLM configurado ({self.llm_client.client_type}, {GEMINI_MODEL}) para extração de gastos")
            except Exception as e:
                self.llm_client = None
                self.model = None
                self.log(f"Erro ao configurar LLM: {e}. Extração limitada", "ERROR")
        else:
            self.llm_client = None
            self.model = None
            self.log("LLM não configurado - extração limitada", "WARNING")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal de processamento do FinanceAgent.
        
        Roteia para diferentes métodos baseado na ação solicitada.
        A ação padrão é "process" que usa LLM para decidir tudo.
        
        Args:
            data: Dicionário com dados de entrada
                  Deve conter:
                  - user_phone: str (ID do usuário)
                  - message: str (mensagem do usuário)
                  - action: str (opcional, padrão: "process")
                            - "process": Usa LLM para detectar intenção e processar
                            - "extract": Extrai e registra gasto (legado)
                            - "query_total": Consulta total de gastos
                            - "query_category": Consulta por categoria
                            - "setup": Placeholder para setup
        
        Returns:
            Dicionário com resultado do processamento:
            {
                "success": bool (True se processou com sucesso),
                "response": str (mensagem de resposta ao usuário),
                "data": dict (dados adicionais, como transaction_id)
            }
        
        Para debug:
        - Ação "process" é a mais usada - rastreie process_with_llm()
        - Outras ações são legado ou específicas
        """
        action = data.get("action", "process")
        
        # Ação padrão: usa LLM para detectar intenção e processar
        # Esta é a forma moderna e flexível de processar mensagens
        if action == "process":
            clarification_context = data.get("clarification_context")
            return self.process_with_llm(data["user_phone"], data["message"], clarification_context)
        
        # Ação de esclarecimento: processa resposta de esclarecimento
        elif action == "clarification":
            clarification_context = data.get("clarification_context", {})
            return self.handle_clarification(data["user_phone"], data["message"], clarification_context)
        
        # Ações legadas/específicas (menos usadas)
        elif action == "extract":
            return self.extract_and_register(data["user_phone"], data["message"])
        elif action == "query_total":
            return self.query_total(data["user_phone"], data.get("period", "month"))
        elif action == "query_category":
            return self.query_by_category(data["user_phone"], data.get("category"))
        elif action == "setup":
            return self.setup_placeholder(data["user_phone"])
        else:
            return {"success": False, "response": "Ação desconhecida"}
    
    def handle_clarification(self, user_phone: str, message: str, clarification_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa resposta de esclarecimento do usuário.
        
        Quando o usuário responde a uma pergunta de esclarecimento, este método
        combina a informação original (do contexto) com a nova informação (da mensagem)
        e processa a ação completa.
        
        Args:
            user_phone: ID do usuário
            message: Resposta do usuário ao esclarecimento
            clarification_context: Contexto do esclarecimento contendo:
                - missing_info: O que estava faltando
                - ambiguous_field: Campo ambíguo
                - target_agent: Agente que deve processar
                - suggestion: Sugestão original
        
        Returns:
            Dicionário com resultado do processamento
        """
        self.log(f"Processando esclarecimento: {clarification_context.get('missing_info')}")
        
        # Usa LLM para combinar informação original com esclarecimento
        if not self.llm_client or not self.llm_client.model:
            return {
                "success": False,
                "response": "Sistema de IA não disponível. Tente novamente mais tarde."
            }
        
        missing_info = clarification_context.get("missing_info", "")
        ambiguous_field = clarification_context.get("ambiguous_field", "")
        
        prompt = f"""Você está processando uma resposta de esclarecimento.

**Contexto do esclarecimento:**
- Informação faltando: {missing_info}
- Campo ambíguo: {ambiguous_field}

**Resposta do usuário:** "{message}"

**Sua tarefa:**
1. Extraia a informação que estava faltando da resposta do usuário
2. Combine com o contexto para formar uma mensagem completa
3. Retorne JSON com a intenção e dados completos

**Exemplos:**

Contexto: categoria faltando, usuário respondeu "Alimentação"
→ {{"intent": "registro", "valor": [valor original], "categoria": "Alimentação", "descricao": "[descrição original]"}}

Contexto: valor faltando, usuário respondeu "50 reais"
→ {{"intent": "registro", "valor": 50, "categoria": "[categoria original]", "descricao": "[descrição original]"}}

Contexto: nome da categoria faltando, usuário respondeu "Pets"
→ {{"intent": "adicionar_categoria", "categoria": "Pets"}}

**IMPORTANTE:**
- Se a resposta ainda estiver ambígua, use intent="pedir_esclarecimento"
- Retorne JSON válido

JSON:"""
        
        try:
            response = self.llm_client.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extrai JSON (pode estar em bloco markdown ou direto)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            json_text = json_match.group(1) if json_match else response_text
            
            result_data = json.loads(json_text)
            intent = result_data.get("intent")
            
            # Processa com a intenção completa
            if intent == "pedir_esclarecimento":
                # Ainda ambíguo, pede mais esclarecimento
                response_msg = result_data.get("resposta", "Ainda não consegui entender. Pode reformular?")
                return {
                    "success": False,
                    "response": response_msg,
                    "needs_clarification": True
                }
            else:
                # Processa normalmente com dados completos
                # Chama process_with_llm com a mensagem combinada
                return self.process_with_llm(user_phone, message)
        
        except Exception as e:
            self.log(f"Erro ao processar esclarecimento: {e}", "ERROR")
            return {
                "success": False,
                "response": "Erro ao processar sua resposta. Pode tentar novamente?"
            }
    
    def process_with_llm(self, user_phone: str, message: str, clarification_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa mensagem usando LLM Gemini para detecção inteligente de intenção.
        
        Este é o método PRINCIPAL do FinanceAgent. Ele usa LLM para:
        1. Detectar a intenção do usuário (registro, consulta, ajuda, setup)
        2. Extrair dados estruturados (valor, categoria, descrição)
        3. Executar ação apropriada (registrar, consultar, responder)
        4. Gerar resposta natural e formatada
        
        Fluxo:
        1. Busca contexto do usuário (total gasto no mês)
        2. Cria prompt detalhado para o LLM
        3. LLM retorna JSON com intenção e dados
        4. Executa ação baseada na intenção
        5. Retorna resposta formatada
        
        Args:
            user_phone: ID único do usuário (telefone ou ID do Telegram)
            message: Mensagem do usuário em linguagem natural
                    Exemplos:
                    - "gastei 50 reais no mercado"
                    - "quanto gastei esse mês?"
                    - "oi, como funciona?"
        
        Returns:
            Dicionário com resultado:
            {
                "success": bool (True se processou com sucesso),
                "response": str (mensagem de resposta ao usuário),
                "data": dict (dados adicionais, como transaction_id)
            }
        
        Para debug:
        - Logs mostram intenção detectada pelo LLM
        - Erros são logados com detalhes completos
        - Adicione print() para ver JSON retornado pelo LLM
        """
        # Validação: LLM é obrigatório para este método
        if not self.llm_client or not self.llm_client.model:
            return {"success": False, "response": "IA não configurada"}
        
        try:
            # 1. Busca ou cria usuário no banco de dados
            # Isso garante que o usuário existe antes de processar
            user = SQLTool.get_or_create_user(user_phone)
            
            # 2. Busca contexto financeiro do usuário para dar ao LLM
            # Total gasto no mês ajuda o LLM a dar respostas mais contextuais
            try:
                end = datetime.now()
                start = end - timedelta(days=30)  # Últimos 30 dias
                total_month = SQLTool.get_total_by_period(user_phone, start, end)
            except:
                # Se falhar ao buscar total, não é crítico - continua com 0
                total_month = 0.0
            
            # 2.5. Busca histórico de conversas recentes para contexto
            # Busca últimas 5 interações para dar contexto ao LLM
            conversation_history = SQLTool.get_conversation_history(user_phone, limit=5)
            history_text = ""
            if conversation_history:
                history_lines = []
                for conv in conversation_history:
                    # Limita tamanho da resposta do bot para não exceder tokens
                    bot_response_short = conv['bot_response'][:150] + "..." if len(conv['bot_response']) > 150 else conv['bot_response']
                    history_lines.append(f"Usuário: {conv['user_message']}")
                    history_lines.append(f"Bot: {bot_response_short}")
                history_text = "\n\n".join(history_lines)
            
            # 3. Cria prompt detalhado para o LLM
            # O prompt instrui o LLM sobre:
            # - Contexto do usuário (ID, total gasto)
            # - Histórico de conversas recentes (context window)
            # - Intenções possíveis (registro, consulta, ajuda, setup)
            # - Formato de resposta esperado (JSON estruturado)
            # - Como extrair dados de gastos
            # Prepara histórico para incluir no prompt
            history_section = ""
            if history_text:
                history_section = f"**Histórico de conversas recentes (para contexto):**\n{history_text}\n\n"
            
            prompt = f"""Você é o Jarvis, um assistente financeiro pessoal via Telegram.

**Contexto do usuário:**
- ID: {user_phone}
- Total gasto este mês: R$ {total_month:.2f}

{history_section}**Mensagem atual do usuário:** "{message}"

**IMPORTANTE:** Use o histórico de conversas acima para entender o contexto da conversa. Se o usuário fizer referência a algo mencionado anteriormente, use o histórico para entender melhor.

**Sua tarefa:**
1. Entenda a intenção do usuário:
   - REGISTRO: quer registrar um gasto (ex: "gastei 50 reais", "paguei 30")
   - CONSULTA: quer ver gastos gerais (ex: "quanto gastei?", "resumo")
   - CONSULTA_CATEGORIA: quer ver gastos de uma categoria específica (ex: "quanto gastei com Alimentação?", "gastos de Transporte", "quanto gastei em Lazer?")
   - CONSULTA_ULTIMA_TRANSACAO: quer ver a última transação registrada (ex: "quanto foi meu ultimo gasto?", "qual foi minha última compra?", "última transação")
   - CONSULTA_LIMITES: quer ver limites configurados (ex: "me mostre meus limites", "quais são meus limites?", "limites")
   - LISTAR_CATEGORIAS: quer ver/listar todas as categorias cadastradas (ex: "me mostre minhas categorias", "quais são minhas categorias?", "listar categorias", "minhas categorias")
   - ADICIONAR_CATEGORIA: quer criar uma nova categoria (ex: "adicionar categoria Pets", "criar categoria Academia", "adicionar categoria bebidas alcoolicas")
   - REMOVER_CATEGORIA: quer remover/excluir/deletar uma categoria (ex: "remover categoria Lazer", "excluir categoria Pets", "deletar categoria X")
   - REMOVER_TRANSACAO: quer remover/excluir/deletar uma transação específica (ex: "remover transação cinema do dia 20/11", "excluir gasto de 50 reais", "deletar transação de ontem")
   - REMOVER_LIMITE: quer remover/excluir/deletar um limite de gasto (ex: "remover limite de Alimentação", "excluir limite Lazer 200", "remover lazer 200")
   - AJUDA: quer ajuda/informação sobre o bot financeiro (ex: "oi", "como funciona?", "ajuda")
   - SETUP: quer configurar (ex: "quero me cadastrar", "configurar")
   - FORA_ESCOPO: pergunta NÃO relacionada a finanças/gastos (ex: "qual o tamanho do brasil", "quem ganhou a copa", perguntas gerais)
   - PEDIR_ESCLARECIMENTO: mensagem ambígua ou incompleta que precisa de confirmação (ex: "gastei 50" sem categoria clara, "paguei" sem valor)

2. Se for REGISTRO:
   - **IMPORTANTE - Tratamento de Ambiguidade (seja flexível):**
     * Permita suposições razoáveis baseadas em contexto:
       - "50" sem contexto → assuma R$ 50,00 (não R$ 0,50)
       - "gastei 50" sem categoria → use categoria "Geral" como fallback
       - "paguei 30 reais" → valor claro, categoria pode ser "Geral" se não identificada
     * Só peça esclarecimento (intent="pedir_esclarecimento") se:
       - Valor estiver REALMENTE ambíguo (ex: "50 centavos" vs "50 reais" sem contexto)
       - Informação estiver COMPLETAMENTE ausente e não puder inferir
     * Se categoria não for identificada, use "Geral" como fallback
   - Extraia: valor (número), categoria (texto, use "Geral" se não identificada), descrição (texto)
   - Se conseguir extrair valor e categoria (mesmo que "Geral"), retorne: {{"intent": "registro", "valor": X, "categoria": "Y", "descricao": "Z"}}
   - Só use intent="pedir_esclarecimento" se REALMENTE não conseguir processar

3. Se for CONSULTA:
   - **IMPORTANTE - Diferença entre CONSULTA e CONSULTA_CATEGORIA:**
     * CONSULTA_CATEGORIA: quando menciona uma categoria específica (ex: "quanto gastei com Alimentação?", "gastos de Transporte")
     * CONSULTA: quando quer ver gastos gerais sem categoria específica (ex: "quanto gastei?", "resumo")
   - **Se for CONSULTA_CATEGORIA:**
     * Extraia o nome da categoria da mensagem
     * Retorne JSON: {{"intent": "consulta_categoria", "categoria": "NomeDaCategoria"}}
     * Exemplos: "quanto gastei com Alimentação?" → {{"intent": "consulta_categoria", "categoria": "Alimentação"}}
   - **Se for CONSULTA (geral):**
     * Se o período não estiver especificado (ex: "quanto gastei?"), use intent="consulta_total" com period="month" (assume mês atual)
     * Se mencionar "hoje" ou "dia" (ex: "quanto gastei hoje?", "gastos do dia"), use intent="consulta_total" com period="day"
     * Se mencionar "semana" ou "7 dias" (ex: "quanto gastei esta semana?"), use intent="consulta_total" com period="week"
     * **Se mencionar datas específicas** (ex: "quanto gastei de 18/11 até 25/11", "gastos entre 18 e 25 de novembro"), use intent="consulta_total" com start_date e end_date
     * Se a consulta estiver muito ambígua (ex: "resumo"), use intent="pedir_esclarecimento" e pergunte o que quer ver
   - Retorne JSON: {{"intent": "consulta_categoria", "categoria": "Nome"}} OU {{"intent": "consulta_total", "period": "day|week|month|all"}} OU {{"intent": "consulta_total", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}} ou {{"intent": "pedir_esclarecimento", "resposta": "pergunta"}}

4. Se for CONSULTA_LIMITES:
   - **IMPORTANTE - Tratamento de Ambiguidade:**
     * Se o período não estiver especificado, use intent="consulta_limites" (mostra todos)
     * Se a categoria não estiver especificada, use intent="consulta_limites" (mostra todos)
   - Retorne JSON: {{"intent": "consulta_limites"}}
   - Eu vou buscar os limites e você formata a resposta

5. Se for LISTAR_CATEGORIAS:
   - **IMPORTANTE - Diferença entre LISTAR_CATEGORIAS e CONSULTA_CATEGORIA:**
     * LISTAR_CATEGORIAS: quando quer ver TODAS as categorias cadastradas (ex: "me mostre minhas categorias", "quais são minhas categorias?", "listar categorias")
     * CONSULTA_CATEGORIA: quando quer ver gastos de UMA categoria específica (ex: "quanto gastei com Alimentação?")
   - Se a mensagem pedir para listar/mostrar/ver todas as categorias, use intent="listar_categorias"
   - Retorne JSON: {{"intent": "listar_categorias"}}
   - Exemplos: "me mostre minhas categorias", "quais são minhas categorias?", "listar categorias", "minhas categorias"

6. Se for FORA_ESCOPO ou mensagem incompreensível:
   - Se a mensagem for completamente aleatória ou não relacionada a finanças, responda educadamente
   - Retorne JSON: {{"intent": "fora_escopo", "resposta": "sua resposta educada aqui"}}
   - Exemplos de resposta:
     * "Desculpe, não entendi. Sou um assistente financeiro. Como posso ajudar você com suas finanças?"
     * "Não consegui entender sua mensagem. Pode reformular? Posso ajudar com gastos, consultas e categorias."
     * "Desculpe, não entendi. Você quer registrar um gasto, ver um resumo ou adicionar uma categoria?"

7. Se for ADICIONAR_CATEGORIA:
   - **IMPORTANTE - Tratamento de Ambiguidade:**
     * Se o nome da categoria não estiver claro (ex: "adicionar categoria" sem nome), use intent="pedir_esclarecimento"
     * Se o nome estiver ambíguo (ex: "sim" pode ser nome ou confirmação), use intent="pedir_esclarecimento"
   - Extraia o nome da categoria da mensagem
   - Se o nome estiver claro, retorne: {{"intent": "adicionar_categoria", "categoria": "NomeDaCategoria"}}
   - Se houver ambiguidade, retorne: {{"intent": "pedir_esclarecimento", "resposta": "Qual o nome da categoria que você quer adicionar?"}}

8. Se for REMOVER_CATEGORIA:
   - **IMPORTANTE - Tratamento de Ambiguidade:**
     * Identifique sinônimos: "remover", "excluir", "deletar", "apagar", "tirar"
     * Se o nome da categoria não estiver claro, use intent="pedir_esclarecimento"
   - Extraia o nome da categoria da mensagem
   - Se o nome estiver claro, retorne: {{"intent": "remover_categoria", "categoria": "NomeDaCategoria"}}
   - Se houver ambiguidade, retorne: {{"intent": "pedir_esclarecimento", "resposta": "Qual categoria você quer remover?"}}
   - Exemplos: "remover categoria Lazer", "excluir categoria Pets", "deletar categoria X"

9. Se for REMOVER_TRANSACAO:
   - **IMPORTANTE - Diferença entre REMOVER_CATEGORIA e REMOVER_TRANSACAO:**
     * REMOVER_TRANSACAO: quando menciona "transação", "gasto", "compra" + detalhes (data, valor, descrição) OU "último gasto", "última transação"
     * REMOVER_CATEGORIA: quando menciona apenas "categoria" sem detalhes de transação
   - **IMPORTANTE - Tratamento de Ambiguidade:**
     * Identifique sinônimos: "remover transação", "excluir gasto", "deletar compra", "remover transação de [data/descrição]", "remover ultimo gasto", "remover ultima transacao"
     * Extraia informações: descrição (ex: "cinema", "Transação para remover"), data (ex: "20/11/2024", "19/11/2025"), valor (ex: "50 reais")
     * **IMPORTANTE:** Se mencionar "último gasto", "última transação", "ultimo gasto", "ultima transacao", defina "remover_ultimo": true
     * **IMPORTANTE:** Se a data estiver no formato DD/MM/YYYY, mantenha nesse formato ou converta para YYYY-MM-DD
     * Se não conseguir identificar qual transação, use intent="pedir_esclarecimento"
   - Retorne JSON: {{"intent": "remover_transacao", "descricao": "texto" (opcional), "data": "DD/MM/YYYY" ou "YYYY-MM-DD" (opcional), "valor": número (opcional), "remover_ultimo": true/false (true se mencionar "último")}}
   - Exemplos: 
     * "remover transação cinema do dia 20/11/2024" → {{"intent": "remover_transacao", "descricao": "cinema", "data": "20/11/2024"}}
     * "excluir gasto de 50 reais" → {{"intent": "remover_transacao", "valor": 50}}
     * "remover ultimo gasto" → {{"intent": "remover_transacao", "remover_ultimo": true}}
     * "pode remover o ultimo gasto" → {{"intent": "remover_transacao", "remover_ultimo": true}}

10. Se for REMOVER_LIMITE:
   - **IMPORTANTE - Tratamento de Ambiguidade:**
     * Identifique sinônimos: "remover limite", "excluir limite", "deletar limite", "tirar limite"
     * Se a categoria não estiver clara, use intent="pedir_esclarecimento"
     * Se mencionar valor (ex: "remover lazer 200"), o valor é ignorado - apenas remove o limite da categoria
   - Extraia o nome da categoria da mensagem (ignore valores numéricos se houver)
   - Se o nome estiver claro, retorne: {{"intent": "remover_limite", "categoria": "NomeDaCategoria"}}
   - Se houver ambiguidade, retorne: {{"intent": "pedir_esclarecimento", "resposta": "De qual categoria você quer remover o limite?"}}
   - Exemplos: "remover limite de Alimentação", "excluir limite Lazer 200", "remover lazer 200"

11. Se for AJUDA ou SAUDAÇÃO:
   - Responda de forma amigável explicando o que você faz (assistente financeiro)
   - Retorne JSON: {{"intent": "ajuda", "resposta": "sua resposta aqui"}}

12. Se for SETUP:
   - Explique que o sistema cria categorias automaticamente
   - Retorne JSON: {{"intent": "setup", "resposta": "sua explicação"}}

13. Se for PEDIR_ESCLARECIMENTO (mensagem ambígua):
   - Identifique o que está faltando ou ambíguo
   - Peça esclarecimento de forma educada e específica
   - Retorne JSON: {{"intent": "pedir_esclarecimento", "resposta": "sua pergunta de esclarecimento aqui"}}
   - Exemplos:
     * "Você mencionou R$ 50, mas não identifiquei a categoria. Em qual categoria devo registrar? (ex: Alimentação, Transporte, Lazer)"
     * "Você disse que gastou, mas não consegui identificar o valor. Quanto foi o gasto?"
     * "Você mencionou '50', isso é R$ 50,00 ou R$ 0,50?"

**IMPORTANTE - Seja flexível e inteligente:**
- Se a mensagem for completamente aleatória ou incompreensível, use intent="fora_escopo" ou "ajuda" e responda educadamente que não entendeu
- Seja flexível: faça suposições razoáveis quando possível (ex: "50" = R$ 50,00, categoria "Geral" se não identificada)
- Só peça esclarecimento se REALMENTE necessário - prefira processar com suposições razoáveis
- Se não conseguir entender NADA da mensagem, responda educadamente: "Desculpe, não entendi. Como posso ajudar?"
- Sempre responda em português brasileiro
- Seja amigável e conciso
- Use emojis quando apropriado
- Retorne SEMPRE um JSON válido

**Formato de resposta:**
```json
{{
  "intent": "registro|consulta_total|consulta_categoria|consulta_ultima_transacao|consulta_limites|adicionar_categoria|remover_categoria|remover_transacao|remover_limite|ajuda|setup|fora_escopo|pedir_esclarecimento",
  "valor": número (apenas para registro ou remover_transacao quando completo e claro),
  "categoria": "texto" (para registro, adicionar_categoria, remover_categoria, remover_limite ou consulta_categoria quando claro),
  "descricao": "texto" (apenas para registro ou remover_transacao),
  "data": "DD/MM/YYYY" ou "YYYY-MM-DD" (apenas para remover_transacao quando mencionar data específica),
  "remover_ultimo": true/false (apenas para remover_transacao quando mencionar "último gasto" ou "última transação"),
  "period": "day|week|month|all" (apenas para consulta_total quando não há datas específicas),
  "start_date": "YYYY-MM-DD" (apenas para consulta_total com datas específicas),
  "end_date": "YYYY-MM-DD" (apenas para consulta_total com datas específicas),
  "resposta": "texto" (para ajuda/setup/fora_escopo/pedir_esclarecimento)
}}
```
"""
            
            # 4. Chama o LLM (Gemini API ou Vertex AI) com o prompt
            # O LLM analisa a mensagem e retorna JSON estruturado
            response = self.llm_client.generate_content(prompt)
            response_text = response.text.strip()
            
            # 5. Extrai JSON da resposta do LLM
            # O LLM pode retornar JSON dentro de blocos de código markdown ou diretamente como texto
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            json_text = json_match.group(1) if json_match else response_text
            
            # 6. Faz parse do JSON retornado pelo LLM
            # O JSON contém: intent, valor, categoria, descricao, resposta
            try:
                result_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                self.log(f"Erro ao fazer parse do JSON do LLM: {e}. Resposta: {response_text[:200]}", "ERROR")
                return {
                    "success": False,
                    "response": "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
                    "needs_clarification": True
                }
            
            # Valida que result_data não é None
            if not result_data:
                self.log("LLM retornou JSON vazio ou None", "ERROR")
                return {
                    "success": False,
                    "response": "Desculpe, não consegui entender sua mensagem. Pode reformular?",
                    "needs_clarification": True
                }
            
            intent = result_data.get("intent")
            
            self.log(f"LLM detectou intenção: {intent}")
            
            # 7. Executa ação baseada na intenção detectada pelo LLM
            if intent == "pedir_esclarecimento":
                # ============================================================
                # INTENÇÃO: PEDIR ESCLARECIMENTO (MENSAGEM AMBÍGUA)
                # ============================================================
                # LLM detectou ambiguidade e pediu esclarecimento
                # Resposta já vem formatada do LLM no campo "resposta"
                response_msg = result_data.get("resposta", 
                    "Não consegui entender completamente. Pode reformular sua mensagem?")
                self.log("Mensagem ambígua detectada - pedindo esclarecimento")
                return {"success": True, "response": response_msg, "data": {}}
            
            elif intent == "registro":
                # Registra o gasto
                # Confia no LLM - se ele retornou "registro", tenta processar
                valor_str = result_data.get("valor")
                categoria = result_data.get("categoria", "").strip()
                descricao = result_data.get("descricao", message[:50])
                
                # Se não tem valor, deixa LLM lidar (já deveria ter detectado como pedir_esclarecimento)
                if not valor_str or valor_str == 0:
                    self.log("Valor não identificado - deixando LLM lidar", "WARNING")
                    return {
                        "success": True,
                        "response": result_data.get("resposta", "Não consegui identificar o valor. Pode informar quanto foi?"),
                        "needs_clarification": True
                    }
                
                try:
                    valor = float(valor_str)
                    if valor <= 0:
                        self.log("Valor inválido - deixando LLM lidar", "WARNING")
                        return {
                            "success": True,
                            "response": result_data.get("resposta", "O valor precisa ser maior que zero. Pode informar o valor correto?"),
                            "needs_clarification": True
                        }
                except (ValueError, TypeError):
                    self.log("Erro ao parsear valor - deixando LLM lidar", "WARNING")
                    return {
                        "success": True,
                        "response": result_data.get("resposta", "Não consegui entender o valor. Pode informar em números?"),
                        "needs_clarification": True
                    }
                
                # Validação de categoria - usa "Geral" como fallback se não identificada
                if not categoria or categoria.strip() == "":
                    categoria = "Geral"
                    self.log(f"Categoria não identificada, usando 'Geral' como fallback")
                
                # Usa matching inteligente com LLM para encontrar categoria existente
                # A categoria já foi validada acima, então não está vazia aqui
                cat = self._find_category_with_llm(user_phone, categoria)
                if not cat:
                    # Se não encontrou categoria existente, cria nova categoria
                    # Isso garante que "Geral" será criada se não existir
                    cat_id = SQLTool.create_category(user_phone, categoria, f"Categoria {categoria}")
                    self.log(f"Categoria '{categoria}' criada automaticamente")
                else:
                    cat_id = cat["category_id"]
                    # Usa o nome correto da categoria encontrada
                    categoria = cat["category_name"]
                
                # Registra transação
                trans_id = SQLTool.insert_transaction(user_phone, cat_id, valor, descricao)
                
                # Verifica limites e gera alerta se necessário
                alert_message = self._check_limits(user_phone, cat_id, valor)
                
                response_msg = f"✅ Gasto registrado: {FormatterTool.format_currency(valor)} em {categoria}"
                
                # Adiciona alerta à resposta se houver
                if alert_message:
                    response_msg += f"\n\n{alert_message}"
                
                return {"success": True, "response": response_msg, "data": {"transaction_id": trans_id}}
            
            elif intent == "consulta_total":
                # ============================================================
                # INTENÇÃO: CONSULTA DE GASTOS
                # ============================================================
                # Usuário quer ver quanto gastou
                # Chama método que busca dados e formata resposta
                # O LLM pode retornar:
                # - period: "day|week|month|all" (períodos relativos)
                # - start_date e end_date: datas específicas (YYYY-MM-DD)
                
                # Verifica se há datas específicas
                start_date_str = result_data.get("start_date")
                end_date_str = result_data.get("end_date")
                
                if start_date_str and end_date_str:
                    # Consulta por período específico (datas customizadas)
                    try:
                        start_date = self._parse_date(start_date_str)
                        end_date = self._parse_date(end_date_str)
                        
                        # Garante que end_date inclui o dia inteiro (até 23:59:59)
                        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                        
                        self.log(f"Consulta por período específico: {start_date_str} até {end_date_str}")
                        return self.query_by_date_range(user_phone, start_date, end_date)
                    except Exception as e:
                        self.log(f"Erro ao parsear datas: {e}", "ERROR")
                        return {
                            "success": False,
                            "response": "❓ Não consegui entender as datas informadas. Pode informar no formato DD/MM/YYYY? (ex: 'quanto gastei de 18/11/2024 até 25/11/2024')"
                        }
                else:
                    # Consulta por período relativo (day, week, month, all)
                    period = result_data.get("period", "month")  # Default: mês atual
                    self.log(f"Consulta de gastos solicitada (período: {period})")
                    return self.query_total(user_phone, period)
            
            elif intent == "consulta_categoria":
                # ============================================================
                # INTENÇÃO: CONSULTA POR CATEGORIA ESPECÍFICA
                # ============================================================
                # Usuário quer ver gastos de uma categoria específica
                categoria = result_data.get("categoria", "").strip()
                if not categoria:
                    return {
                        "success": False,
                        "response": "❓ Não consegui identificar qual categoria você quer consultar. Pode informar o nome da categoria?"
                    }
                self.log(f"Consulta por categoria solicitada: {categoria}")
                return self.query_by_category(user_phone, categoria)
            
            elif intent == "consulta_ultima_transacao":
                # ============================================================
                # INTENÇÃO: CONSULTA ÚLTIMA TRANSAÇÃO
                # ============================================================
                # Usuário quer ver a última transação registrada
                self.log("Consulta de última transação solicitada")
                transactions = SQLTool.get_transactions(user_phone, limit=1)
                
                if not transactions:
                    return {
                        "success": True,
                        "response": "📭 Você ainda não tem transações registradas."
                    }
                
                transaction = transactions[0]
                date = datetime.fromisoformat(transaction['created_at']) if isinstance(transaction['created_at'], str) else transaction['created_at']
                datetime_str = FormatterTool.format_datetime(date)
                amount_str = FormatterTool.format_currency(transaction['amount'])
                category = transaction.get('category_name', 'Sem categoria')
                description = transaction.get('expense_description', 'Sem descrição')
                
                response = f"📋 *Última Transação:*\n\n"
                response += f"• {datetime_str} - {amount_str}\n"
                response += f"  {description} ({category})"
                
                return {
                    "success": True,
                    "response": response,
                    "data": {"transaction": transaction}
                }
            
            elif intent == "consulta_limites":
                # ============================================================
                # INTENÇÃO: CONSULTA DE LIMITES
                # ============================================================
                # Usuário quer ver seus limites configurados
                self.log("Consulta de limites solicitada")
                return self.query_limits(user_phone)
            
            elif intent == "listar_categorias":
                # ============================================================
                # INTENÇÃO: LISTAR CATEGORIAS
                # ============================================================
                # Usuário quer ver todas as categorias cadastradas
                self.log("Listagem de categorias solicitada")
                return self.list_categories(user_phone)
            
            elif intent == "fora_escopo":
                # ============================================================
                # INTENÇÃO: MENSAGEM FORA DO ESCOPO
                # ============================================================
                # Usuário fez pergunta não relacionada a finanças
                # Resposta já vem formatada do LLM no campo "resposta"
                response_msg = result_data.get("resposta", 
                    "Desculpe, mas eu sou um assistente financeiro e só posso ajudar com questões relacionadas a gastos, categorias, limites e consultas financeiras. Como posso ajudar você com suas finanças?")
                self.log("Mensagem fora do escopo detectada")
                return {"success": True, "response": response_msg, "data": {}}
            
            elif intent == "adicionar_categoria":
                # ============================================================
                # INTENÇÃO: ADICIONAR CATEGORIA
                # ============================================================
                # Usuário quer criar uma nova categoria
                # Confia no LLM - se ele retornou "adicionar_categoria", tenta processar
                categoria = result_data.get("categoria", "").strip()
                
                # Se não tem categoria, deixa LLM lidar (já deveria ter detectado como pedir_esclarecimento)
                if not categoria or len(categoria) < 2:
                    self.log("Nome da categoria não identificado - deixando LLM lidar", "WARNING")
                    return {
                        "success": True,
                        "response": result_data.get("resposta", "Não consegui identificar o nome da categoria. Pode informar o nome?"),
                        "needs_clarification": True
                    }
                
                # Verifica se categoria já existe (busca exata primeiro, depois matching restritivo)
                # Primeiro tenta busca exata (case-insensitive)
                existing_exact = SQLTool.get_category_by_name(user_phone, categoria)
                if existing_exact:
                    return {
                        "success": True,
                        "response": f"✅ A categoria *{existing_exact['category_name']}* já existe! Você pode usá-la para registrar gastos."
                    }
                
                # Se não encontrou exato, usa matching inteligente mas RESTRITIVO
                # Só retorna se for realmente a mesma categoria (erro de digitação/acentuação)
                existing = self._find_category_with_llm(user_phone, categoria)
                if existing:
                    # Verifica se o nome é realmente similar (não apenas relacionado)
                    # Se a categoria digitada for claramente diferente, cria nova
                    if existing['category_name'].lower() == categoria.lower():
                        return {
                            "success": True,
                            "response": f"✅ A categoria *{existing['category_name']}* já existe! Você pode usá-la para registrar gastos."
                        }
                    # Se for similar mas não igual, pergunta ao usuário
                    return {
                        "success": True,
                        "response": f"❓ Encontrei uma categoria similar: *{existing['category_name']}*\n\nVocê quer criar uma nova categoria chamada *{categoria}* ou usar a categoria *{existing['category_name']}* existente?",
                        "needs_clarification": True
                    }
                
                # Cria nova categoria
                try:
                    cat_id = SQLTool.create_category(user_phone, categoria, f"Categoria personalizada: {categoria}")
                    self.log(f"Categoria '{categoria}' criada (ID: {cat_id})")
                    return {
                        "success": True,
                        "response": f"✅ Categoria *{categoria}* criada com sucesso!\n\nAgora você pode usar ela para registrar gastos. Ex: 'gastei 50 em {categoria}'"
                    }
                except Exception as e:
                    self.log(f"Erro ao criar categoria: {e}", "ERROR")
                    return {
                        "success": False,
                        "response": f"❌ Erro ao criar categoria '{categoria}'. Tente novamente com outro nome."
                    }
            
            elif intent == "remover_categoria":
                # ============================================================
                # INTENÇÃO: REMOVER CATEGORIA
                # ============================================================
                # Usuário quer remover/excluir uma categoria
                categoria = result_data.get("categoria", "").strip()
                
                # Se não tem categoria, deixa LLM lidar
                if not categoria or len(categoria) < 2:
                    self.log("Nome da categoria não identificado para remoção - deixando LLM lidar", "WARNING")
                    return {
                        "success": True,
                        "response": result_data.get("resposta", "Qual categoria você quer remover?"),
                        "needs_clarification": True
                    }
                
                # Busca categoria usando matching inteligente
                cat = self._find_category_with_llm(user_phone, categoria)
                if not cat:
                    return {
                        "success": False,
                        "response": f"❌ Categoria '{categoria}' não encontrada."
                    }
                
                # Tenta remover
                if SQLTool.delete_category(user_phone, cat["category_id"]):
                    self.log(f"Categoria '{cat['category_name']}' removida com sucesso")
                    return {
                        "success": True,
                        "response": f"✅ Categoria *{cat['category_name']}* removida com sucesso!"
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ Não é possível remover a categoria *{cat['category_name']}* porque ela possui transações registradas.\n\nPara remover, primeiro você precisa deletar ou mover todas as transações dessa categoria."
                    }
            
            elif intent == "remover_transacao":
                # ============================================================
                # INTENÇÃO: REMOVER TRANSAÇÃO
                # ============================================================
                # Usuário quer remover/excluir uma transação específica
                # Valida result_data
                if not result_data:
                    return {
                        "success": False,
                        "response": "❌ Erro ao processar solicitação de remoção. Tente novamente.",
                        "needs_clarification": True
                    }
                
                descricao = result_data.get("descricao", "").strip() if result_data.get("descricao") else ""
                data_str = result_data.get("data", "").strip() if result_data.get("data") else ""
                valor = result_data.get("valor")
                remover_ultimo = result_data.get("remover_ultimo", False)  # Flag para remover última transação
                
                # Busca transações que correspondem aos critérios
                all_transactions = SQLTool.get_transactions(user_phone, limit=100)
                
                if not all_transactions:
                    return {
                        "success": False,
                        "response": "❌ Você não tem transações registradas."
                    }
                
                # Se pediu para remover o último gasto e não especificou critérios, remove a última
                if remover_ultimo or (not descricao and not data_str and valor is None):
                    # Verifica se a mensagem menciona "último" ou "última"
                    message_lower = message.lower()
                    if any(word in message_lower for word in ["ultimo", "último", "ultima", "última", "ultimo gasto", "ultima transacao"]):
                        # Remove a última transação (primeira da lista, pois está ordenada por data DESC)
                        transaction = all_transactions[0]
                        transaction_id = transaction['transaction_id']
                        
                        if SQLTool.delete_transaction(user_phone, transaction_id):
                            date = datetime.fromisoformat(transaction['created_at']) if isinstance(transaction['created_at'], str) else transaction['created_at']
                            datetime_str = FormatterTool.format_datetime(date)
                            amount_str = FormatterTool.format_currency(transaction['amount'])
                            self.log(f"Última transação {transaction_id} removida com sucesso")
                            return {
                                "success": True,
                                "response": f"✅ Última transação removida com sucesso!\n\n• {datetime_str} - {amount_str}\n  {transaction.get('expense_description') or 'Sem descrição'} ({transaction.get('category_name', 'Sem categoria')})"
                            }
                        else:
                            return {
                                "success": False,
                                "response": "❌ Erro ao remover a transação. Tente novamente."
                            }
                
                # Filtra transações baseado nos critérios fornecidos
                matching_transactions = []
                for t in all_transactions:
                    match = True
                    
                    # Filtro por descrição
                    if descricao:
                        expense_desc = t.get('expense_description') or ''
                        if not expense_desc or descricao.lower() not in expense_desc.lower():
                            match = False
                    
                    # Filtro por data
                    if data_str:
                        try:
                            # Tenta vários formatos de data
                            target_date = None
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                                try:
                                    target_date = datetime.strptime(data_str, fmt).date()
                                    break
                                except:
                                    continue
                            
                            if target_date:
                                t_date = datetime.fromisoformat(t['created_at']).date() if isinstance(t['created_at'], str) else t['created_at'].date()
                                if t_date != target_date:
                                    match = False
                        except Exception as e:
                            self.log(f"Erro ao processar data '{data_str}': {e}", "WARNING")
                            pass
                    
                    # Filtro por valor
                    if valor is not None:
                        if abs(float(t['amount']) - float(valor)) > 0.01:  # Tolerância para float
                            match = False
                    
                    if match:
                        matching_transactions.append(t)
                
                if not matching_transactions:
                    return {
                        "success": False,
                        "response": "❌ Não encontrei transações que correspondam aos critérios informados."
                    }
                
                if len(matching_transactions) > 1:
                    # Múltiplas transações encontradas - mostra para o usuário escolher
                    response = f"❓ Encontrei {len(matching_transactions)} transações que correspondem:\n\n"
                    for i, t in enumerate(matching_transactions[:5], 1):  # Mostra até 5
                        date = datetime.fromisoformat(t['created_at']) if isinstance(t['created_at'], str) else t['created_at']
                        datetime_str = FormatterTool.format_datetime(date)
                        amount_str = FormatterTool.format_currency(t['amount'])
                        response += f"{i}. {datetime_str} - {amount_str} - {t.get('expense_description', 'Sem descrição')}\n"
                    response += "\nPor favor, seja mais específico (adicione data ou descrição mais detalhada)."
                    return {
                        "success": True,
                        "response": response,
                        "needs_clarification": True
                    }
                
                # Exatamente uma transação encontrada - remove
                transaction = matching_transactions[0]
                transaction_id = transaction['transaction_id']
                
                if SQLTool.delete_transaction(user_phone, transaction_id):
                    date = datetime.fromisoformat(transaction['created_at']) if isinstance(transaction['created_at'], str) else transaction['created_at']
                    datetime_str = FormatterTool.format_datetime(date)
                    amount_str = FormatterTool.format_currency(transaction['amount'])
                    self.log(f"Transação {transaction_id} removida com sucesso")
                    return {
                        "success": True,
                        "response": f"✅ Transação removida com sucesso!\n\n• {datetime_str} - {amount_str}\n  {transaction.get('expense_description', 'Sem descrição')}"
                    }
                else:
                    return {
                        "success": False,
                        "response": "❌ Erro ao remover a transação. Tente novamente."
                    }
            
            elif intent == "remover_limite":
                # ============================================================
                # INTENÇÃO: REMOVER LIMITE
                # ============================================================
                # Usuário quer remover/excluir um limite de gasto
                categoria = result_data.get("categoria", "").strip()
                
                # Se não tem categoria, deixa LLM lidar
                if not categoria or len(categoria) < 2:
                    self.log("Nome da categoria não identificado para remover limite - deixando LLM lidar", "WARNING")
                    return {
                        "success": True,
                        "response": result_data.get("resposta", "De qual categoria você quer remover o limite?"),
                        "needs_clarification": True
                    }
                
                # Busca categoria usando matching inteligente
                cat = self._find_category_with_llm(user_phone, categoria)
                if not cat:
                    return {
                        "success": False,
                        "response": f"❌ Categoria '{categoria}' não encontrada."
                    }
                
                # Remove limite
                if SQLTool.delete_limit_rule(user_phone, cat["category_id"]):
                    self.log(f"Limite da categoria '{cat['category_name']}' removido com sucesso")
                    return {
                        "success": True,
                        "response": f"✅ Limite da categoria *{cat['category_name']}* removido com sucesso!"
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ Não foi possível remover o limite da categoria *{cat['category_name']}*.\n\nA categoria não possui limite configurado."
                    }
            
            elif intent == "setup":
                # ============================================================
                # INTENÇÃO: SETUP/CONFIGURAÇÃO
                # ============================================================
                # Usuário quer configurar o sistema
                # Redireciona para SetupAgent que tem fluxo guiado
                self.log("Setup detectado - redirecionando para SetupAgent")
                return {
                    "success": True,
                    "response": None,  # SetupAgent vai gerar a resposta
                    "data": {},
                    "route_to": "setup"  # Flag para o workflow rotear corretamente
                }
            
            elif intent == "ajuda":
                # ============================================================
                # INTENÇÃO: AJUDA/SAUDAÇÃO
                # ============================================================
                # Usuário quer ajuda ou está cumprimentando
                # Resposta já vem formatada do LLM no campo "resposta"
                response_msg = result_data.get("resposta", "Como posso ajudar?")
                return {"success": True, "response": response_msg, "data": {}}
            
            else:
                # ============================================================
                # FALLBACK: INTENÇÃO DESCONHECIDA
                # ============================================================
                # Se o LLM retornou uma intenção não reconhecida,
                # usa a resposta que o LLM gerou (pode ser útil)
                response_msg = result_data.get("resposta", "Não entendi. Pode reformular?")
                self.log(f"Intenção desconhecida: {intent}, usando resposta do LLM")
                return {"success": True, "response": response_msg, "data": {}}
        
        except json.JSONDecodeError as e:
            # Erro ao fazer parse do JSON retornado pelo LLM
            # Pode acontecer se o LLM não retornar JSON válido
            self.log(f"Erro ao fazer parse do JSON do LLM: {e}", "ERROR")
            self.log(f"Resposta do LLM: {response_text[:200]}", "ERROR")
            return {"success": False, "response": "Erro ao processar resposta. Tente novamente!"}
        
        except Exception as e:
            # Erro genérico - loga detalhes para debug
            self.log(f"Erro ao processar com LLM: {e}", "ERROR")
            import traceback
            traceback.print_exc()  # Stack trace completo para debug
            return {"success": False, "response": f"Erro ao processar: {str(e)}"}
    
    def setup_placeholder(self, user_phone: str) -> Dict[str, Any]:
        """
        Resposta temporária para configuração (até implementar SetupAgent).
        """
        response = """
⚙️ *Configuração Automática*

Não se preocupe! As categorias são criadas automaticamente quando você registra gastos.

*Como funciona:*
• Diga "gastei 50 no mercado" → cria categoria "Alimentação"
• Diga "uber 20 reais" → cria categoria "Transporte"
• Diga "cinema 40" → cria categoria "Lazer"

*Categorias disponíveis:*
• Alimentação (mercado, restaurante, almoço)
• Transporte (uber, ônibus, taxi)
• Lazer (cinema, festas)
• Saúde (farmácia, consultas)
• Educação (livros, cursos)

*Para definir limites:*
Em breve você poderá configurar limites por categoria!

Por enquanto, só começar a usar: "gastei 50 no supermercado" 😊
        """.strip()
        
        return {
            "success": True,
            "response": response,
            "data": None
        }
    
    def extract_expense(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extrai valor, categoria e descrição de uma mensagem usando LLM.
        
        IMPORTANTE: Este método não é mais usado no fluxo principal.
        A extração é feita diretamente no process_with_llm() que usa LLM.
        Mantido apenas para compatibilidade.
        
        Args:
            message: Mensagem do usuário (ex: "gastei 50 reais no mercado")
            
        Returns:
            None (força uso do método principal process_with_llm())
        """
        # Este método não é mais usado - toda extração é feita via LLM no process_with_llm()
        # Se chamado, retorna None para forçar uso do método principal
        self.log("extract_expense() chamado - use process_with_llm() em vez disso", "WARNING")
        return None
    
    def extract_and_register(self, user_phone: str, message: str) -> Dict[str, Any]:
        """
        Extrai informações e registra gasto no banco.
        
        Returns:
            {"success": bool, "response": str, "expense": dict}
        """
        # Garante que usuário existe
        SQLTool.get_or_create_user(user_phone)
        
        # Extrai informações
        expense = self.extract_expense(message)
        
        if not expense or not expense.get("amount"):
            return {
                "success": False,
                "response": "Não consegui identificar o valor do gasto. Tente algo como: 'gastei 50 reais no mercado'",
                "expense": None
            }
        
        # Busca ou cria categoria
        category_name = expense["category"]
        category = SQLTool.get_category_by_name(user_phone, category_name)
        
        if not category:
            # Cria categoria automaticamente
            category_id = SQLTool.create_category(user_phone, category_name, f"Categoria {category_name}")
            self.log(f"Categoria '{category_name}' criada automaticamente (ID: {category_id})")
        else:
            category_id = category["category_id"]
        
        # Registra transação
        transaction_id = SQLTool.insert_transaction(
            user_phone,
            category_id,
            expense["amount"],
            expense["description"]
        )
        
        # Verifica limites
        alert_message = self._check_limits(user_phone, category_id, expense["amount"])
        
        # Formata resposta
        response = FormatterTool.format_success_message(
            f"Gasto registrado: {FormatterTool.format_currency(expense['amount'])} em {category_name}"
        )
        
        if alert_message:
            response += f"\n\n{alert_message}"
        
        self.log(f"Transação {transaction_id} registrada: R$ {expense['amount']}")
        
        return {
            "success": True,
            "response": response,
            "expense": {
                "transaction_id": transaction_id,
                "amount": expense["amount"],
                "category": category_name,
                "description": expense["description"]
            }
        }
    
    def _check_limits(self, user_phone: str, category_id: int, new_amount: float) -> Optional[str]:
        """Verifica se algum limite foi atingido e retorna alerta se necessário."""
        
        rules = SQLTool.get_active_rules(user_phone)
        
        for rule in rules:
            if rule["category_id"] == category_id:
                # Define período baseado no tipo da regra
                end_date = datetime.now()
                if rule["period_type"] == "mensal":
                    # Primeiro dia do mês atual
                    start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                elif rule["period_type"] == "semanal":
                    # 7 dias atrás
                    start_date = end_date - timedelta(days=7)
                else:
                    # Default: mês atual
                    start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Calcula total do período
                current_total = SQLTool.get_total_by_category(
                    user_phone, 
                    category_id, 
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Atualiza regra
                SQLTool.update_rule_total(rule["rule_id"], current_total)
                
                # Verifica se excedeu
                if current_total >= rule["limit_value"]:
                    return FormatterTool.format_limit_alert(
                        rule["category_name"],
                        current_total,
                        rule["limit_value"],
                        rule["period_type"]
                    )
        
        return None
    
    def query_total(self, user_phone: str, period: str = "month") -> Dict[str, Any]:
        """
        Consulta total gasto em um período.
        
        Args:
            period: "day", "week", "month", "all"
        """
        now = datetime.now()
        
        if period == "day":
            # Hoje (do início do dia até agora)
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_label = "hoje"
        elif period == "week":
            start_date = now - timedelta(days=7)
            period_label = "nos últimos 7 dias"
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_label = "este mês"
        else:  # period == "all"
            # Para "all", usa data muito antiga para buscar todas as transações
            start_date = datetime(2000, 1, 1)
            period_label = "no total"
        
        # Busca total
        total = SQLTool.get_total_by_period(user_phone, start_date, now)
        
        # Busca por categoria (usa None para start_date quando for "all" para buscar todas)
        if period == "all":
            spending_data = SQLTool.get_spending_by_category(user_phone, None, now)
        else:
            spending_data = SQLTool.get_spending_by_category(user_phone, start_date, now)
        
        # Formata resposta
        summary = FormatterTool.format_category_summary(spending_data)
        response = f"📊 *Resumo de Gastos* ({period_label}):\n\n{summary}"
        
        return {
            "success": True,
            "response": response,
            "data": {
                "total": total,
                "period": period,
                "categories": spending_data
            }
        }
    
    def query_limits(self, user_phone: str) -> Dict[str, Any]:
        """
        Consulta e retorna todos os limites configurados pelo usuário.
        
        Args:
            user_phone: ID único do usuário
            
        Returns:
            Dicionário com resposta formatada contendo todos os limites
        """
        # Busca todas as regras ativas do usuário
        rules = SQLTool.get_active_rules(user_phone)
        
        if not rules:
            return {
                "success": True,
                "response": "📊 *Seus Limites*\n\n"
                           "Você ainda não configurou nenhum limite de gasto.\n\n"
                           "Para definir limites, use o comando de setup ou diga algo como:\n"
                           "'definir limite de 2000 para alimentação'",
                "data": {}
            }
        
        # Formata lista de limites
        lines = ["📊 *Seus Limites Configurados:*\n"]
        
        for rule in rules:
            category_name = rule["category_name"]
            limit_value = rule["limit_value"]
            current_total = rule.get("current_total", 0)
            period_type = rule["period_type"]
            
            # Calcula percentual usado
            percentage = (current_total / limit_value * 100) if limit_value > 0 else 0
            
            # Emoji baseado no percentual
            if percentage >= 100:
                emoji = "🔴"
                status = "EXCEDIDO"
            elif percentage >= 80:
                emoji = "🟡"
                status = "ATENÇÃO"
            else:
                emoji = "🟢"
                status = "OK"
            
            # Formata período
            period_label = "mensal" if period_type == "mensal" else period_type
            
            lines.append(
                f"{emoji} *{category_name}* ({period_label})\n"
                f"   Limite: {FormatterTool.format_currency(limit_value)}\n"
                f"   Gasto atual: {FormatterTool.format_currency(current_total)}\n"
                f"   Status: {status} ({FormatterTool.format_percentage(percentage)})\n"
            )
        
        response_msg = "\n".join(lines)
        
        return {
            "success": True,
            "response": response_msg,
            "data": {"rules_count": len(rules)}
        }
    
    def list_categories(self, user_phone: str) -> Dict[str, Any]:
        """
        Lista todas as categorias cadastradas do usuário.
        
        Args:
            user_phone: ID único do usuário
            
        Returns:
            Dicionário com resposta formatada contendo todas as categorias
        """
        categories = SQLTool.get_user_categories(user_phone)
        
        if not categories:
            return {
                "success": True,
                "response": "📁 *Suas Categorias*\n\n"
                           "Você ainda não tem categorias cadastradas.\n\n"
                           "Para criar uma categoria, diga algo como:\n"
                           "'adicionar categoria Alimentação' ou 'criar categoria Transporte'",
                "data": {"categories": []}
            }
        
        # Formata lista de categorias
        lines = ["📁 *Suas Categorias:*\n"]
        
        for i, cat in enumerate(categories, 1):
            category_name = cat["category_name"]
            description = cat.get("description", "")
            
            # Adiciona descrição se houver
            if description:
                lines.append(f"{i}. *{category_name}* - {description}")
            else:
                lines.append(f"{i}. *{category_name}*")
        
        response_msg = "\n".join(lines)
        
        return {
            "success": True,
            "response": response_msg,
            "data": {"categories": categories, "count": len(categories)}
        }
    
    def query_by_category(self, user_phone: str, category_name: str) -> Dict[str, Any]:
        """Consulta gastos de uma categoria específica."""
        category = SQLTool.get_category_by_name(user_phone, category_name)
        
        if not category:
            return {
                "success": False,
                "response": f"❌ Categoria '{category_name}' não encontrada.",
                "data": None
            }
        
        total = SQLTool.get_total_by_category(user_phone, category["category_id"])
        transactions = SQLTool.get_transactions(user_phone, category["category_id"], limit=10)
        
        formatted_list = FormatterTool.format_transaction_list(transactions)
        response = f"*Categoria: {category_name}*\n\n"
        response += f"Total: {FormatterTool.format_currency(total)}\n\n"
        response += formatted_list
        
        return {
            "success": True,
            "response": response,
            "data": {"total": total, "transactions": transactions}
        }
    
    def _find_category_with_llm(self, user_phone: str, category_input: str) -> Optional[Dict[str, Any]]:
        """
        Usa LLM para encontrar a categoria mais próxima (matching inteligente).
        
        Isso resolve problemas de:
        - Erros de digitação (Alimentacao vs Alimentação)
        - Diferenças de acentuação
        - Variações de nome
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

**IMPORTANTE - Seja RESTRITIVO:**
- Só retorne uma categoria se for REALMENTE a mesma (ex: "Alimentacao" → "Alimentação")
- NÃO confunda categorias diferentes (ex: "bebidas alcoolicas" ≠ "Alimentação")
- NÃO retorne categorias apenas por serem relacionadas (ex: "Pets" ≠ "Saúde")
- Se a categoria digitada for claramente diferente, retorne "NENHUMA"

Considere APENAS:
- Erros de digitação (ex: "Alimentacao" → "Alimentação")
- Diferenças de acentuação (ex: "Alimentação" = "Alimentacao")
- Variações mínimas de nome (ex: "Alimentação" = "Alimentacao")

NÃO considere:
- Categorias relacionadas mas diferentes (ex: "bebidas" ≠ "Alimentação")
- Categorias que compartilham palavras mas são diferentes (ex: "bebidas alcoolicas" ≠ "Alimentação")

Retorne APENAS o nome exato da categoria mais próxima, ou "NENHUMA" se não houver correspondência EXATA ou muito próxima.

Categoria mais próxima:"""
            
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
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Converte string de data em datetime.
        
        Suporta múltiplos formatos:
        - YYYY-MM-DD (ISO)
        - DD/MM/YYYY
        - DD-MM-YYYY
        - DD/MM/YY (assume 20XX)
        
        Args:
            date_str: String com data em qualquer formato
            
        Returns:
            datetime objeto
            
        Raises:
            ValueError: Se não conseguir parsear a data
        """
        date_str = date_str.strip()
        
        # Tenta formato ISO primeiro (YYYY-MM-DD)
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass
        
        # Tenta formato brasileiro (DD/MM/YYYY)
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            pass
        
        # Tenta formato com hífen (DD-MM-YYYY)
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            pass
        
        # Tenta formato curto (DD/MM/YY) - assume 20XX
        try:
            dt = datetime.strptime(date_str, "%d/%m/%y")
            # Se ano for < 2000, assume 20XX
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 2000)
            return dt
        except ValueError:
            pass
        
        # Se nenhum formato funcionou, lança erro
        raise ValueError(f"Formato de data não reconhecido: {date_str}")
    
    def query_by_date_range(self, user_phone: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Consulta gastos por período específico (datas customizadas).
        
        Retorna:
        - Total gasto no período
        - Resumo por categoria
        - Lista de transações
        
        Args:
            user_phone: ID do usuário
            start_date: Data inicial (inclusive)
            end_date: Data final (inclusive, até 23:59:59)
            
        Returns:
            Dicionário com resposta formatada contendo total, resumo e lista
        """
        # Garante que start_date começa no início do dia
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Garante que end_date termina no final do dia
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Validação: end_date deve ser >= start_date
        if end_date < start_date:
            return {
                "success": False,
                "response": "❓ A data final deve ser posterior à data inicial. Verifique as datas informadas."
            }
        
        # Busca total do período
        total = SQLTool.get_total_by_period(user_phone, start_date, end_date)
        
        # Busca resumo por categoria
        spending_data = SQLTool.get_spending_by_category(user_phone, start_date, end_date)
        
        # Busca lista de transações (limite de 50)
        transactions = SQLTool.get_transactions(
            user_phone,
            category_id=None,
            start_date=start_date,
            end_date=end_date,
            limit=50
        )
        
        # Formata período para exibição
        start_str = FormatterTool.format_date(start_date)
        end_str = FormatterTool.format_date(end_date)
        period_label = f"de {start_str} até {end_str}"
        
        # Formata resposta
        summary = FormatterTool.format_category_summary(spending_data)
        transaction_list = FormatterTool.format_transaction_list(transactions)
        
        # Monta resposta completa
        response_lines = [
            f"📊 *Resumo de Gastos* ({period_label}):\n",
            summary,
            "\n",
            transaction_list
        ]
        
        response = "\n".join(response_lines)
        
        return {
            "success": True,
            "response": response,
            "data": {
                "total": total,
                "start_date": start_date,
                "end_date": end_date,
                "categories": spending_data,
                "transactions": transactions,
                "transactions_count": len(transactions)
            }
        }

