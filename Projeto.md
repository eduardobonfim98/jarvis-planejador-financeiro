# Projeto

## Visão Geral

O avanço dos **Large Language Models (LLMs)** e frameworks como **ReAct** (Yao et al., 2022) e **Toolformer** (Schick et al., 2023) possibilitou a criação de **agentes autônomos** capazes de raciocinar, planejar e executar ações em sistemas reais.  

Com base nesses conceitos, este projeto apresenta o **Jarvis** — um **assistente financeiro pessoal integrado ao WhatsApp**, desenvolvido para **automatizar o controle de gastos** e facilitar o acompanhamento financeiro diário.

O Jarvis combina **interpretação em linguagem natural**, **raciocínio financeiro** e **execução automatizada**.  
O usuário interage apenas via texto (“Gastei 40 reais no mercado”), e o sistema interpreta, classifica e registra a transação automaticamente.

---

## Objetivos

### Objetivo Geral
Desenvolver um sistema conversacional inteligente, baseado em agentes e LLMs, capaz de automatizar o controle financeiro pessoal.

### Objetivos Específicos
- Permitir **registro de gastos via linguagem natural** pelo WhatsApp.  
- Oferecer **resumos e comparativos** de despesas por categoria e período.  
- Enviar **alertas automáticos** de limites de gasto.  
- Gerar **gráficos personalizados** e relatórios em tempo real.  
- Garantir **personalização de categorias e metas financeiras**.  
- Suportar **mensagens automáticas** e lembretes configuráveis.  

---

## Arquitetura do Sistema

O Jarvis adota uma arquitetura **multiagente assíncrona**, onde cada agente executa uma função cognitiva específica e interage com os demais via mensagens estruturadas.

### Principais Agentes
| Agente | Função Principal |
|--------|------------------|
| **PartnerAgent** | Recebe e classifica a intenção da mensagem do usuário. |
| **SetupAgent** | Gerencia a configuração inicial e personalização de categorias e limites. |
| **FinanceAgent** | Núcleo operacional: registra gastos, gera resumos e gráficos. |
| **ValidadorAgent** | Valida consistência e coerência dos resultados. |
| **MessageAgent** | Envia lembretes e mensagens automáticas. |
| **ModeratorAgent** | Garante segurança e tom adequado das mensagens. |

Os agentes se comunicam de forma modular, permitindo fácil expansão e manutenção do sistema.

---

## Tools (Ferramentas)

As **Tools** são componentes responsáveis por executar ações concretas, como cálculos, consultas e geração de gráficos — seguindo os princípios do **ReAct** e **Toolformer** (*reasoning + acting*).  

### Tools Implementadas
| Tool | Função |
|------|--------|
| **SQLTool** | Acessa o banco de dados (CRUD, queries dinâmicas). |
| **CalculatorTool** | Realiza cálculos e comparativos percentuais. |
| **FilterTool** | Aplica filtros de categoria, data e limite. |
| **FormatterTool** | Formata mensagens e valores monetários. |
| **PlotTool** | Gera gráficos (pizza, barras, séries temporais) via Matplotlib/Plotly. |

Essa separação entre **agentes (raciocínio)** e **Tools (ação)** garante modularidade, escalabilidade e clareza arquitetural.

---

## Funcionalidades Implementadas

| Funcionalidade | Descrição |
|----------------|-----------|
| **Registro de gastos** | Interpreta mensagens e registra automaticamente no banco de dados. |
| **Resumo por período/categoria** | Exibe totais e comparativos mensais ou semanais. |
| **Alertas automáticos** | Notifica o usuário quando limites definidos são atingidos. |
| **Gráficos automáticos** | Gera e envia visualizações personalizadas via WhatsApp. |
| **Configuração inicial** | Permite definir categorias e metas na primeira interação. |
| **Lembretes automáticos** | Envia notificações de engajamento diário. |
| **Consulta de histórico** | Lista transações filtradas por data ou categoria. |

---

## Banco de Dados

O sistema utiliza **SQLite** como banco de dados relacional local, com estrutura compatível com migração futura para **PostgreSQL**.

### Principais Tabelas
| Tabela | Função | Chave Primária | Relacionamentos |
|--------|---------|----------------|-----------------|
| **users** | Identifica usuários via número de telefone. | `user_phone` | 1:N com *categories* |
| **categories** | Armazena categorias personalizadas. | `category_id` | 1:N com *transactions*, *user_rules* |
| **transactions** | Registra cada despesa. | `transaction_id` | FK → *users*, *categories* |
| **user_rules** | Define limites de gasto por categoria/período. | `rule_id` | FK → *users*, *categories* |

Essa modelagem segue princípios de normalização (1FN–3FN) e suporta múltiplos usuários e categorias sem redundância.

---

## Tecnologias Utilizadas

| Tecnologia | Função |
|-------------|--------|
| **Python 3.11** | Linguagem principal e base para todos os módulos. |
| **LangGraph** | Orquestração dos agentes e Tools. |
| **FastAPI** | Criação de APIs assíncronas integradas ao WhatsApp. |
| **Twilio API (WhatsApp)** | Envio e recebimento de mensagens. |
| **SQLite** | Banco de dados relacional leve e portátil. |
| **Matplotlib / Plotly** | Geração de gráficos e visualizações. |
| **APScheduler** | Agendamento de tarefas automáticas. |

---

## Fluxo de Execução

1. O usuário envia uma mensagem via WhatsApp.  
2. O **PartnerAgent** valida e identifica a intenção.  
3. O **FinanceAgent** ou **SetupAgent** executa a ação solicitada.  
4. As **Tools** são chamadas conforme a necessidade (consulta, cálculo, gráfico).  
5. O **ValidadorAgent** garante a coerência da resposta.  
6. A mensagem final é enviada de volta ao WhatsApp.

---

## Conclusão

O **Jarvis** demonstra como arquiteturas baseadas em agentes e LLMs podem ser aplicadas a problemas práticos, como o controle financeiro pessoal.  
O sistema integra raciocínio textual, persistência de dados e execução automatizada em um ambiente acessível via WhatsApp — oferecendo uma experiência conversacional **inteligente, segura e personalizável**.

Em versões futuras, o Jarvis poderá incluir **relatórios automáticos, previsões financeiras e integração bancária**, consolidando-se como um assistente completo de gestão financeira pessoal.