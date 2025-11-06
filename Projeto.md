4. Projeto 

O  avanço  dos  Large  Language  Models  (LLMs)  e  a  consolidação  de  frameworks 
como  ReAct  (Yao  et  al.,  2022)  e  Toolformer  (Schick  et  al.,  2023)  permitiram  o 
desenvolvimento de agentes autônomos capazes de raciocinar, interagir e executar 
tarefas complexas em sistemas reais. 

Com  base  nessas  abordagens,  este  projeto  apresenta  o  Jarvis,  um  assistente 
financeiro  integrado  ao  WhatsApp,  cujo  objetivo  é  simplificar  o  controle de gastos 
pessoais  utilizando  LLM  Agents  e  integração  direta  com  bancos  de  dados  e 
ferramentas externas. 

O  objetivo principal do projeto é ajudar as pessoas a terem um maior controle 
dos seus gastos, tornando esse processo mais acessível, intuitivo e automatizado. 

A  ideia surgiu da observação de que muitas pessoas utilizam planilhas para anotar 
manualmente suas despesas, o que, apesar de útil, é trabalhoso e pouco prático no 
dia a dia. 

A  proposta,  então,  foi  imaginar  uma  solução  mais  natural:  e  se  fosse  possível 
apenas  enviar  uma  mensagem  de  texto  com  os  gastos  do  dia,  e  um  agente 
automatizasse todo o processo de registro e personalização? 

Dessa  reflexão  surgiu  o  Jarvis.  Em  versões  futuras,  o  sistema  poderá  oferecer 
funcionalidades  pagas,  como  a  geração  automática  de  planilhas  e  relatórios 
financeiros, ampliando o acesso da população a ferramentas de controle financeiro 
mais eficientes e personalizadas. 

O  Jarvis  foi  projetado  como  um  sistema  multiagente,  em  que  cada  módulo  tem 
forma  assíncrona  e 
responsabilidades 
organizada. 

independentes,  comunicando-se  de 

As  interações  ocorrem  totalmente  em  linguagem  natural,  por  meio  de  texto  via 
WhatsApp,  o que torna a aplicação acessível, sem a necessidade de instalação de 
aplicativos ou uso de interfaces gráficas adicionais. 

Além disso, também será possível receber gráficos personalizados dos gastos, 
gerados automaticamente pelos agentes, a partir das informações armazenadas no 
banco de dados. 

Nos próximos tópicos, serão descritos os principais componentes e funcionalidades 
do sistema: 

●  Na  Seção  4.1,  serão  apresentadas  as  funcionalidades  implementadas, 
com uma visão detalhada das ações que o sistema é capaz de realizar, como 

registrar gastos, emitir alertas e gerar gráficos. 

●  Na  Seção  4.2,  serão  explicados  os  agentes  que  compõem  a  arquitetura 
multiagente,  suas  responsabilidades  e  como  interagem  entre  si  para 
coordenar as decisões do sistema. 

●  Na  Seção  4.3,  serão  descritas  as  Tools,  explicando  seu  conceito, 
fundamentação  teórica  nos  trabalhos  ReAct  e  Toolformer,  e  a  importância 
delas  para  que  os  agentes  possam  executar  ações  reais,  como  acessar 
bancos de dados, realizar cálculos e gerar visualizações. 

●  A Seção 4.4 abordará as tecnologias utilizadas, apresentando os principais 
frameworks,  bibliotecas  e  serviços  integrados  que  compõem  o  ambiente  de 
execução do sistema. 

●  A  Seção  4.5  descreve  as  funções  principais  do  código,  tanto  das  Tools 
quanto  dos  Agentes,  especificando  suas  responsabilidades  e  exemplos  de 
uso. 

●  Por  fim,  a  Seção  4.6  apresentará  a  estrutura  do  banco  de  dados, 
explicando  como  as  informações  dos  usuários,  categorias  e transações são 
armazenadas  e 
relacionadas  entre  si  para  garantir  persistência  e 
escalabilidade. 

Dessa forma, o Capítulo 4 tem como objetivo apresentar a implementação prática 
do  sistema  Jarvis  —  desde  a  concepção  de  suas  funcionalidades  até  a 
organização de seus componentes internos —, evidenciando como os conceitos de 
agentes,  ferramentas  e  aprendizado  de  máquina  foram  integrados  para  criar  um 
assistente financeiro funcional, automatizado e acessível. 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
4.1 Funcionalidades implementadas 

4.1.1. Registro de gastos 
O registro de gastos constitui a funcionalidade central do Jarvis. 
O  usuário  envia  mensagens  em  linguagem  natural,  como  “Gastei  50  reais  no 
mercado”  ou  “Almoço  30  reais”,  e  o  sistema  interpreta  automaticamente  o  valor 
monetário, a categoria e a descrição da transação. 
Antes  da  gravação  definitiva,  o  agente  responsável  realiza  uma  etapa  de 
confirmação,  retornando  uma mensagem ao usuário para validação da informação, 
como no exemplo: 
“Confirmar: R$50,00 na categoria Mercado?” 
Somente após a confirmação positiva, o gasto é inserido na base de dados. 
Cada transação é registrada com os seguintes atributos principais: 
●  número do telefone do usuário (chave primária composta); 

●  valor do gasto; 

●  categoria associada; 

●  descrição textual informada pelo usuário; 

●  data e hora de criação 

O  armazenamento  desses  dados  garante  persistência,  rastreabilidade  e  precisão 
temporal, possibilitando análises históricas e comparativos consistentes. 
Esse  procedimento  assegura,  ainda,  a 
confiabilidade dos resultados apresentados ao usuário. 

informações  e  a 

integridade  das 

2. Resumo total e por categoria 
O  Jarvis  consolida  e  apresenta  informações  financeiras  de  maneira  dinâmica  e 
personalizada. 
Quando  o  usuário  solicita,  por  exemplo,  “Quanto  gastei  este  mês?”  ou  “Quanto 
gastei com transporte?”, o sistema realiza consultas específicas ao banco de dados, 
aplicando filtros por período e por categoria. 
O  resultado  é  processado  e  retornado  de  forma  formatada,  apresentando  o  total 
consolidado em reais. 
Essa  funcionalidade  permite  uma  visão  clara  e  imediata  dos  hábitos  de  consumo, 
dispensando cálculos manuais ou a utilização de planilhas externas. 

3. Comparativo semanal e mensal 
Os  comparativos 
armazenamento redundante de resultados. 

temporais  são  calculados  em 

tempo 

real,  evitando  o 

 
 
 
 
 
 
 
 
Quando  o usuário solicita, por exemplo, “Gastei mais que na semana passada?”, o 
sistema  executa  duas  consultas  diretas  à  base  de  dados:  uma  correspondente ao 
período atual e outra ao período anterior. 
Os  valores  resultantes são somados e comparados, e o agente calcula a diferença 
absoluta e o percentual de variação entre os períodos. 
Essa  abordagem  assegura  que  as  informações  apresentadas  estejam  sempre 
atualizadas,  sem  necessidade  de  armazenamento  prévio  de  dados  derivados, 
garantindo consistência e precisão analítica. 
Com isso, o Jarvis oferece uma ferramenta eficaz para a identificação de tendências 
e o acompanhamento da evolução dos gastos ao longo do tempo. 

4. Alertas automáticos de limite 
O sistema possibilita que o usuário defina limites de gasto por categoria ou período, 
como, por exemplo, R$500,00 para alimentação ou R$300,00 para lazer. 
A cada nova transação registrada, o agente financeiro responsável atualiza os totais 
acumulados das regras associadas ao usuário e realiza uma verificação automática. 
Caso  o  valor  acumulado  ultrapasse  o  limite  definido,  o  sistema  envia  uma 
mensagem  de  alerta  pelo  WhatsApp,  informando  o valor excedente e o percentual 
de gasto atingido. 
Essa  arquitetura,  baseada  em  atualizações  incrementais,  evita  a  necessidade  de 
somas  completas  a  cada  nova  inserção,  otimizando  o  desempenho  do  sistema  e 
reduzindo o custo computacional. 
A  separação  entre  as  tabelas  de  transações  e  regras  também  permite  maior 
flexibilidade  e  escalabilidade,  facilitando  a  adição  de  novos  tipos  de  limites  e 
relatórios personalizados no futuro. 

5. Configuração inicial e personalização de categorias 
Na  primeira  interação  com  o  sistema,  o  usuário  é  guiado  por  um  processo  de 
configuração inicial. 
Durante essa etapa, o agente solicita que o usuário informe as categorias de gastos 
que  deseja  monitorar  —  como  alimentação,  lazer, transporte e delivery — e defina 
os limites de despesa correspondentes. 
Essas  informações  são  armazenadas  no  banco  de  dados  e  vinculadas ao número 
de telefone do usuário, permitindo a personalização do sistema. 
O  usuário  pode  revisar  ou  alterar  suas  categorias  e  limites  a  qualquer  momento, 
assegurando flexibilidade e adequação às suas necessidades financeiras. 

6. Geração de gráficos 
Além  das  respostas  em  formato  textual,  o  Jarvis  é  capaz  de  gerar  gráficos 
personalizados sobre o comportamento financeiro do usuário. 
Essa  funcionalidade  é  implementada  pela  PlotTool,  que  utiliza  bibliotecas  de 
visualização,  como  Matplotlib  e  Plotly,  para  gerar  representações  gráficas  a  partir 
dos dados armazenados. 
Inicialmente, nessa primeira versão, os gráficos produzidos são:  

 
 
 
●  Gráficos de pizza, que apresentam a distribuição dos gastos por categoria; 

●  Gráficos de barras, que comparam gastos entre períodos distintos; 

●  Séries temporais, que exibem a evolução dos gastos ao longo do tempo. 

Os  gráficos  são  gerados  sob  demanda  e  enviados automaticamente ao WhatsApp 
do  usuário,  permitindo  a  visualização  imediata  das  informações de forma prática e 
intuitiva. 

7. Mensagens automáticas e lembretes 

O  sistema  possui  uma  rotina  automática  de  mensagens  proativas,  executada 
diariamente  às  22  horas.  Essa  rotina  verifica  o  tempo  transcorrido  desde  o  último 
registro  de  cada  usuário, com base no campo last_message_at. Se for identificado 
um  período  de  inatividade  superior  ao  limite  estabelecido,  o  MessageAgent envia 
uma  mensagem  de  lembrete,  incentivando  o  usuário  a  continuar  registrando  seus 
gastos.  Essa  funcionalidade  visa  aumentar  o  engajamento  e  fomentar  o  uso 
contínuo do sistema, promovendo o hábito de acompanhamento financeiro diário. 

Durante  o  processo  de  configuração  inicial  (setup),  o  usuário  é  informado 
explicitamente  sobre  a  existência  dessa  rotina  e  recebe  a  sugestão  de 
recebimento  às  22  horas.  Nessa  etapa,  o  usuário  pode  optar  por  ativar  ou 
desativar  o  envio  de  lembretes  e,  se  desejar,  ajustar  o  horário  preferencial.  As 
preferências  são  armazenadas  no  perfil  do  usuário  (por  exemplo,  campos 
notify_opt_in e notify_hour), podendo ser alteradas a qualquer momento por meio 
de  comando  direto  no  WhatsApp  (e.g.,  “desativar  lembretes”  ou  “mudar  lembrete 
para  20h”).  Dessa  forma,  assegura-se  transparência,  consentimento  e  controle  do 
usuário sobre comunicações automáticas. 

8. Consultas e histórico de transações 

O  usuário  pode  solicitar  o  histórico  completo  de  suas  transações,  aplicando  filtros 
por período ou categoria. 
Comandos  como  “Mostre  meus  gastos  de  setembro”  ou  “Quero  ver  todas  as 
despesas de lazer” acionam consultas específicas no banco de dados. 
Os  resultados  são  apresentados  em  formato  textual  ou  visual,  conforme  a 
solicitação do usuário. 
Essa  funcionalidade  assegura  transparência,  possibilitando  revisões  detalhadas  e 
promovendo o controle integral das finanças pessoais. 

 
 
 
 
 
 
4.2 Agentes 

O  sistema  Jarvis  foi  projetado  segundo  uma  arquitetura  multiagente,  na  qual 
interagem  entre  si  para  compreender 
diferentes  componentes  autônomos 
comandos, executar ações, validar resultados e responder ao usuário. 

Cada agente é responsável por uma parte específica do fluxo de processamento, o 
que permite modularidade, escalabilidade e manutenção simplificada. 

Essa  estrutura  segue  o  princípio  de  divisão  de  responsabilidades,  característico 
dos sistemas inteligentes baseados em agentes, em que cada unidade desempenha 
uma função cognitiva distinta, cooperando para alcançar o objetivo global. 

Os  agentes  do  Jarvis  comunicam-se  de  forma  assíncrona,  trocando  informações 
intermediárias e acionando Tools quando necessário para realizar ações concretas, 
como cálculos, consultas ou geração de gráficos. 

A Figura 4.2 representa de forma esquemática a interação entre os agentes. 

 
 
Figura 4: Diagrama dos agentes 

4.2.1 PartnerAgent 

O PartnerAgent é o ponto inicial do fluxo de processamento do sistema. 

Sua função é receber a mensagem enviada pelo usuário, aplicar validações básicas 
e determinar o tipo de solicitação. 

Antes  de  qualquer  processamento  por  parte  dos  demais  agentes,  o  PartnerAgent 
executa  um  filtro de segurança e formatação, baseado em expressões regulares 
(Regular Expressions), para verificar se a mensagem contém conteúdo inadequado, 
é excessivamente longa ou apresenta formato inconsistente. 

Essa  etapa  assegura  que  apenas  mensagens  válidas  sejam  processadas, 
garantindo estabilidade e segurança ao sistema. 

 
 
Após a validação, o PartnerAgent analisa o conteúdo da mensagem e classifica sua 
intenção  principal  (por  exemplo:  registro,  consulta,  configuração,  alerta  ou 
solicitação de gráfico). 

Com  base  nessa  classificação,  a mensagem é encaminhada ao agente apropriado 
—  como  o  SetupAgent  ou  o  FinanceAgent  —  para  execução  da  ação 
correspondente. 

4.2.2 SetupAgent 

O  SetupAgent  é  responsável  pelo  processo  de  configuração  inicial  e  pelas 
atualizações posteriores de categorias e limites financeiros. 

Durante  a  primeira  interação  do  usuário  com  o  sistema,  esse  agente  conduz  um 
diálogo guiado, solicitando informações sobre as principais categorias de gasto e os 
respectivos valores de limite. 

Esses  dados são então registrados no banco de dados e vinculados ao número de 
telefone do usuário. 

O  SetupAgent  também  permite  revisões  posteriores,  possibilitando  que  o  usuário 
adicione  novas  categorias,  altere  valores  de  limite  ou  redefina  suas  preferências 
financeiras. 

Sua  atuação  é  essencial  para  personalizar  o  sistema  e  adaptar  o  comportamento 
dos demais agentes de acordo com o perfil de cada usuário. 

4.2.3 FinanceAgent 

O FinanceAgent constitui o núcleo operacional do sistema, sendo responsável pela 
maior parte das funcionalidades de controle financeiro. 

Esse agente executa as operações de registro, consulta, análise e alerta de gastos, 
interagindo  diretamente  com  as  Tools  para  acessar  o  banco  de  dados,  realizar 
cálculos e formatar resultados. 

Suas principais funções incluem: 

●  Registrar gastos confirmados pelo usuário e inserir os dados na base de 

transações; 

 
 
 
●  Analisar despesas por período ou categoria, realizando consultas dinâmicas 

no banco de dados; 

●  Comparar períodos (semanal, mensal ou personalizado), calculando 

variações percentuais; 

●  Verificar limites e gerar alertas com base nas regras cadastradas pelo 

SetupAgent; 

●  Solicitar gráficos à PlotTool, quando o usuário deseja representações visuais 

dos dados. 

O  FinanceAgent  é  também  o  componente  responsável  por  coordenar  o  fluxo  de 
decisão  entre  as  ferramentas,  garantindo  que  cada  solicitação  do  usuário  siga  a 
sequência correta de ações — interpretação, cálculo, validação e resposta. 

4.2.4 ValidadorAgent 

O  ValidadorAgent  atua  na  etapa  final  do  fluxo  de  processamento,  verificando  a 
consistência das respostas geradas antes de enviá-las ao usuário. 

Esse agente tem como função confirmar se os resultados retornados pelos cálculos 
e consultas são coerentes com os parâmetros solicitados. 

Ele verifica, por exemplo, se a categoria informada existe, se o valor retornado está 
dentro de limites válidos ou se a mensagem gerada segue o formato esperado. 

Essa etapa é fundamental para garantir a precisão e a confiabilidade do sistema, 
especialmente em casos de múltiplas interações entre agentes e ferramentas. 

futuras,  o  ValidadorAgent  poderá  ser  expandido  para 

incluir 
Em  versões 
mecanismos  de  verificação  semântica,  assegurando  que  as  respostas  sigam 
padrões de empatia e clareza linguística. 

4.2.5 MessageAgent 

O  MessageAgent  é  responsável  pela  execução  de  tarefas  programadas de forma 
automática. 

 
 
 
 
 
 
Atualmente,  sua  principal  função  é  realizar  verificações  periódicas  no  banco  de 
dados  para  identificar  usuários  inativos  e,  com  base  nessa  análise,  enviar 
mensagens de lembrete. 

Embora  essa  funcionalidade  esteja  planejada  para  versões  futuras  do  sistema 
(denominadas Pro), o MessageAgent já foi estruturado conceitualmente para operar 
em conjunto com um agendador de tarefas (scheduler), como o APScheduler. 

Em  versões  posteriores,  esse  agente também poderá ser utilizado para o envio de 
relatórios  automáticos,  resumos  mensais  e  notificações  de  eventos  financeiros 
relevantes, consolidando o Jarvis como um assistente proativo e personalizado. 

4.2.6 ModeratorAgent 

O ModeratorAgent é responsável por assegurar a conformidade ética, linguística e 
tanto  de  entrada 
contextual  das  mensagens  processadas  pelo  sistema  — 
(mensagens  enviadas  pelo  usuário)  quanto  de  saída  (respostas  geradas  pelos 
agentes). 

Na  fase  de  entrada,  o  ModeratorAgent  atua  logo  após  o  PartnerAgent,  aplicando 
verificações  adicionais  para  detectar  linguagem  ofensiva,  termos  sensíveis, 
dados pessoais ou mensagens fora do escopo financeiro. 

Quando  necessário,  ele  bloqueia o processamento e envia uma resposta empática 
ao usuário, informando sobre o motivo da rejeição de forma educativa e respeitosa. 

Na  fase  de  saída,  o  ModeratorAgent  revisa  as  respostas formuladas pelos demais 
agentes  (principalmente  o  FinanceAgent e o ValidadorAgent) para assegurar que o 
tom  da  mensagem  seja  adequado  —  empático,  informativo  e  coerente  com  o 
propósito do sistema. 

Essa  moderação  dupla  garante  a  segurança,  consistência  comunicativa  e 
confiabilidade do Jarvis. 

Além  disso,  o  ModeratorAgent  utiliza  Tools  específicas,  como  o  RegexTool  (para 
filtragem  textual)  e  o  FormatterTool,  assegurando  que  a  comunicação  siga  boas 
práticas de UX conversacional. 

Em versões futuras, esse agente poderá incorporar modelos de sentiment analysis e 
toxicity  detection,  ampliando  sua  capacidade  de  moderação  automática  e 
adaptativa. 

 
 
4.2.7 Conclusão da Seção 

Em  conjunto,  os  agentes descritos formam um sistema cooperativo e autônomo, 
em que cada componente executa uma função específica, mas interdependente das 
ações dos demais. 

Essa abordagem modular facilita a manutenção e a evolução do sistema, permitindo 
a inclusão de novos agentes e funcionalidades sem comprometer a arquitetura geral 
do projeto. 

O  resultado  é  um  ecossistema  de  agentes  que  combina  interpretação  de 
linguagem  natural,  raciocínio  financeiro,  validação  e  moderação  ética, 
entregando  uma  experiência  conversacional  segura,  precisa  e  personalizada  ao 
usuário. 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
4.3 Tools 

As  Tools  (ferramentas)  constituem  o  conjunto  de  funções externas utilizadas pelos 
agentes para executar ações concretas no ambiente computacional. 
  Enquanto  os  agentes  são  responsáveis pelo raciocínio e pela tomada de decisão, 
as  Tools  realizam  as  operações  práticas  —  como  cálculos,  consultas ao banco de 
dados e geração de gráficos. 

Essa  separação  de  responsabilidades  segue  o  paradigma  proposto  pelos 
frameworks  ReAct  (Yao  et  al.,  2022)  e  Toolformer  (Schick  et  al.,  2023),  que 
introduziram o conceito de Reasoning + Acting (raciocinar e agir) como base para o 
funcionamento de agentes inteligentes. 

4.3.1 Conceito e fundamentação teórica 

função 

No contexto de sistemas baseados em LLMs (Large Language Models), uma Tool é 
uma 
implementada  externamente  e  exposta  ao  agente  como  uma 
capacidade cognitiva adicional. 
 Dessa forma, o agente pode decidir, de maneira autônoma, quando e como utilizar 
uma ferramenta para atingir determinado objetivo. 

O  modelo  de  linguagem  atua  como  o  “cérebro”  do  sistema,  responsável  pelo 
raciocínio  textual  e  a  interpretação  das  intenções  do  usuário,  enquanto  as  Tools 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
funcionam  como  as  “mãos”  e  “olhos”  —  executando  operações  no  mundo  real  e 
retornando os resultados ao agente para continuidade do raciocínio. 

Essa arquitetura foi inicialmente descrita no framework ReAct (Yao et al., 2022), que 
combinou raciocínio linguístico com ações externas (reasoning + acting), permitindo 
que agentes alternassem entre “pensar” e “agir” de forma coordenada. 
  Posteriormente,  o  trabalho  Toolformer  (Schick  et  al.,  2023)  demonstrou  que 
modelos  de  linguagem  podem  aprender  autonomamente  quando  e  como  usar 
ferramentas externas, aprimorando sua capacidade de resolver tarefas complexas e 
integrar sistemas reais. 

No  Jarvis,  as  Tools  representam  interfaces  funcionais  reutilizáveis,  acessadas  por 
diferentes agentes conforme a necessidade. 
  Elas  garantem  modularidade,  escalabilidade  e consistência, permitindo que novas 
funcionalidades sejam adicionadas sem modificar a arquitetura central do sistema. 

4.3.2 Tools implementadas no Jarvis 

O sistema Jarvis implementa cinco Tools principais, responsáveis por operações de 
manipulação de dados, cálculos, filtragem, formatação e visualização. 
  Essas  ferramentas  são  invocadas  dinamicamente  pelos  agentes,  conforme  o  tipo 
de solicitação do usuário. 

4.3.2.1 SQLTool 

A SQLTool é responsável pela comunicação direta com o banco de dados relacional 
(SQLite, nesta versão do sistema). 
 Ela executa as operações de criação, inserção, atualização e consulta nas tabelas 
users, categories, transactions e user_rules. 

É  utilizada  principalmente  pelo  FinanceAgent  e  pelo  SetupAgent,  garantindo  o 
acesso seguro, consistente e eficiente às informações armazenadas. 
  Além  disso,  encapsula  as  consultas  SQL  em  funções  reutilizáveis,  abstraindo  a 
lógica  de  manipulação  de  dados  e  simplificando  o  fluxo  de  interação  entre  os 
agentes. 

4.3.2.2 CalculatorTool 

A  CalculatorTool  executa  cálculos  matemáticos  e  percentuais  relacionados  às 
despesas, como somas, médias, diferenças absolutas e variações entre períodos. 
  É  acionada  pelo  FinanceAgent  durante operações de comparação temporal e nas 
análises  de alertas, permitindo que o sistema identifique tendências e variações de 
consumo. 

Essa  Tool  contribui  para  transformar  dados  brutos  em  informações  quantitativas, 
como: 

●  “Você gastou 20% a mais do que na semana passada.” 

●  “O total acumulado até o momento é de R$ 315,00.” 

4.3.2.3 FilterTool 

A  FilterTool  realiza  o  pré-processamento  dos  resultados,  aplicando  filtros  sobre  os 
dados antes da formatação final. 
  Ela  permite  selecionar  registros  por  categoria,  data  ou  valor  máximo/mínimo, 
servindo  como  camada  intermediária  entre  as  consultas  SQL  e  a  geração  da 
resposta textual. 

Essa  abordagem  melhora  a  eficiência  do  sistema,  pois  reduz  o  volume  de  dados 
manipulados pelos agentes e torna as consultas mais precisas e personalizadas. 
  A  FilterTool  é  amplamente  utilizada  nas  funções  analyze_expenses()  e 
compare_spending() do FinanceAgent. 

4.3.2.4 FormatterTool 

A  FormatterTool  é  responsável  por  formatar  a  saída  textual  que  será  enviada  ao 
usuário. 
  Ela  converte  valores numéricos para o formato monetário brasileiro (R$), organiza 
os  dados  retornados  em  listas  ou  tabelas  e  ajusta  o  estilo  das  mensagens  de 
resposta, garantindo clareza e padronização comunicativa. 

Por exemplo: 

Entrada: valor_total = 153.7 
 Saída formatada: "Total de gastos: R$ 153,70" 

A FormatterTool também é responsável por formatar alertas automáticos, garantindo 
uma comunicação empática e acessível ao usuário. 

4.3.2.5 PlotTool 

A  PlotTool  é  utilizada  para  a  geração  de  gráficos  personalizados,  baseados  nos 
dados financeiros do usuário. 
  Ela  emprega  bibliotecas  de  visualização  como  Matplotlib  e  Plotly  para  criar 
representações gráficas do comportamento financeiro. 

Os principais tipos de gráficos implementados são: 

 
 
 
●  Gráficos de pizza – mostram a distribuição de gastos por categoria; 

●  Gráficos de barras – comparam valores entre semanas ou meses; 

●  Séries temporais – exibem a evolução diária dos gastos. 

Esses  gráficos  são  gerados  sob  demanda  e  enviados  automaticamente  ao 
WhatsApp  como  imagens,  oferecendo  uma  visualização  clara  e  intuitiva  dos 
resultados. 

4.3.3 Diferença entre Tools e funções comuns 

Embora as Tools sejam implementadas como funções em Python, o conceito é mais 
abrangente. 
  Enquanto  uma  função  comum  é  executada  diretamente  pelo  código  do  sistema, 
uma  Tool  é  registrada  e  disponibilizada  ao  agente,  que  decide  autonomamente 
quando e por que utilizá-la. 

Em outras palavras: 

O agente raciocina sobre o problema, decide a ação apropriada e chama 
a Tool correspondente para executar essa ação no ambiente real. 

Essa distinção é o que transforma o Jarvis em um sistema cognitivo integrado — o 
agente  não  apenas  interpreta  comandos,  mas  age  de  forma  autônoma,  utilizando 
suas ferramentas para interagir com o mundo (consultar, calcular, gerar, alertar). 

4.3.4 Conclusão da seção 

As Tools descritas acima constituem a base funcional do Jarvis. 
 Elas ampliam o escopo de atuação dos agentes, permitindo que o sistema combine 
raciocínio  linguístico,  execução  prática  e  geração  de  insights  de  forma  fluida  e 
modular. 
  Essa  integração  é  o  que torna o Jarvis um assistente financeiro inteligente, capaz 
de  unir  processamento  de  linguagem  natural, persistência de dados e visualização 
de informações em um único fluxo automatizado. 

4.4 Tecnologias Utilizadas 

 
 
 
 
 
 
 
 
 
O  desenvolvimento  do  sistema  Jarvis  baseou-se  em  um  conjunto  de  tecnologias 
modernas  que  possibilitam  a  integração  entre  modelos  de  linguagem  natural, 
bancos de dados relacionais e interfaces de mensageria. 
A  escolha  dessas  ferramentas  levou  em  consideração  critérios  como  leveza, 
escalabilidade,  compatibilidade  com  bibliotecas  de  inteligência  artificial e facilidade 
de integração com o WhatsApp, canal principal de interação com o usuário. 
A  Tabela  4.1  apresenta  as  principais  tecnologias  utilizadas,  seguidas  de  uma 
descrição detalhada de seu papel no sistema. 

Tabela 4.1 – Tecnologias empregadas no desenvolvimento do sistema 

Tecnologia 

Função principal 

Python 3.11 

LangGraph 

FastAPI 

Linguagem  principal  do  sistema  e  base  para  todos  os 
módulos e agentes. 

Framework  para  orquestração  e  gerenciamento  dos  fluxos 
entre agentes e ferramentas. 

Framework  para  criação  de  APIs  assíncronas,  responsável 
pela integração com o WhatsApp. 

Twilio 
(WhatsApp) 

API 

Serviço de mensageria que permite o envio e recebimento de 
mensagens de texto e imagens. 

SQLite 

Banco  de  dados  relacional  leve  e  embutido,  utilizado  para 
armazenamento local das informações. 

Matplotlib / Plotly  Bibliotecas  de  visualização  de  dados,  responsáveis  pela 

geração dos gráficos financeiros. 

APScheduler 

Biblioteca  de  agendamento  de  tarefas,  empregada  para  o 
envio de mensagens automáticas (versão futura). 

4.4.1 Python 3.11 
A  linguagem  Python  foi  escolhida  como  base  de  desenvolvimento  por  sua  ampla 
adoção  em  projetos  de  inteligência  artificial,  ciência  de  dados  e  automação  de 
processos. 
 Sua sintaxe simples e expressiva favorece o desenvolvimento rápido de protótipos 
e a integração com bibliotecas externas. 
  Além  disso,  Python  oferece  suporte  nativo  a  bibliotecas  de  processamento  de 
linguagem natural e frameworks de agentes, o que o torna especialmente adequado 
para o contexto do Jarvis. 

4.4.2 LangGraph 

 
 
 
 
 
 
O  LangGraph  é  um  framework  voltado  à  orquestração  de agentes de linguagem e 
gerenciamento de fluxos conversacionais complexos. 
  Ele  permite  estruturar  as  interações  entre  múltiplos  agentes  e  Tools,  definindo  a 
ordem de execução, as dependências e as condições de transição entre etapas do 
raciocínio. 
  No  Jarvis,  o  LangGraph  é  responsável  por  coordenar  o  fluxo  principal  das 
interações  —  desde  o  recebimento  da  mensagem  até a execução das consultas e 
geração da resposta final. 
  A  adoção  desse  framework  garante  modularidade,  legibilidade  e  controle  sobre a 
lógica de decisão dos agentes. 

4.4.3 FastAPI 
O FastAPI é um framework para o desenvolvimento de APIs REST assíncronas em 
Python. 
  Ele  foi  utilizado  como camada de integração entre o sistema Jarvis e o serviço de 
mensageria  do  WhatsApp,  servindo como receptor das mensagens enviadas pelos 
usuários e como ponto de envio das respostas geradas pelos agentes. 
  Além  de  sua  performance  elevada,  o  FastAPI oferece suporte nativo a operações 
assíncronas, o que permite o processamento simultâneo de múltiplas requisições — 
característica essencial para sistemas que visam escalar o número de usuários. 

4.4.4 Twilio API (WhatsApp) 
A API do Twilio é o serviço responsável pela comunicação direta com o usuário. 
 Ela permite o envio e recebimento de mensagens de texto, imagens e documentos 
através do WhatsApp, de forma segura e padronizada. 
 No Jarvis, todas as interações ocorrem por meio dessa integração, desde o registro 
de despesas até o envio de gráficos e alertas. 
  A  utilização  do Twilio garante conformidade com as políticas oficiais do WhatsApp 
Business e fornece estabilidade na transmissão das mensagens. 

4.4.5 SQLite 
O  SQLite  foi  adotado  como  banco  de  dados  relacional  principal  por  sua  leveza, 
portabilidade e simplicidade de configuração. 
  Por  ser  um  banco  embarcado,  o  SQLite  não  requer  a  instalação  de  servidores 
externos,  o  que  o  torna  ideal  para  o  desenvolvimento  de  protótipos  e sistemas de 
pequeno e médio porte. 
  Sua  estrutura  relacional  permite  o  armazenamento  de  informações  de  forma 
organizada,  com  integridade  referencial  entre  tabelas  como  users,  categories, 
transactions e user_rules. 
 Além disso, o SQLite oferece desempenho suficiente para suportar a execução de 
múltiplas consultas simultâneas, mantendo baixo consumo de recursos. 

4.4.6. Matplotlib e Plotly 

 
 
 
 
 
As  bibliotecas  Matplotlib  e  Plotly  são  amplamente  utilizadas  para  visualização  de 
dados em Python. 
  No  Jarvis,  essas  bibliotecas  são  empregadas  pela  PlotTool  para  gerar 
representações  visuais  dos  gastos  do  usuário,  como  gráficos  de  pizza,  barras  e 
séries temporais. 
  O  Matplotlib  foi  escolhido  pela  simplicidade  e  versatilidade  na  criação de gráficos 
estáticos, enquanto o Plotly fornece recursos interativos e maior qualidade visual. 
  Essas  ferramentas  complementam  a  experiência  do  usuário  ao  permitir  que  as 
informações financeiras sejam apresentadas de forma clara e intuitiva. 

4.4.7 APScheduler 
O  APScheduler  (Advanced  Python  Scheduler)  é  uma  biblioteca  de  agendamento 
utilizada para executar tarefas em horários específicos. 
  No  contexto  do  Jarvis,  ela  é  empregada  pelo  MessageAgent  para  o  envio 
automatizado de mensagens e lembretes diários. 
  Embora  essa  funcionalidade  esteja  planejada  para  versões  futuras  (Pro),  sua 
arquitetura  já  foi  incorporada  ao  sistema,  garantindo  suporte  a  agendamentos 
periódicos, como notificações semanais e resumos mensais. 

4.4.8 Integração entre tecnologias 
A  combinação  dessas  tecnologias  proporciona  um  ambiente  robusto,  modular  e 
escalável,  em  que  cada  componente  cumpre  um  papel  específico  no  fluxo  de 
execução. 
  O  LangGraph  gerencia  o  comportamento  dos  agentes  e  das  Tools,  o  FastAPI 
intermedia  a  comunicação  entre  o  sistema  e  o  WhatsApp,  e  o  SQLite  garante  a 
persistência e integridade dos dados. 
  Por  sua  vez,  o  Twilio  viabiliza  a  interação  com  o  usuário  final,  enquanto  as 
bibliotecas  de  visualização  (Matplotlib  e  Plotly)  fornecem  representações  gráficas 
intuitivas dos resultados. 
Essa  integração  harmoniosa  entre  frameworks  e  serviços  consolida  o  Jarvis como 
uma  aplicação  moderna,  leve  e  funcional,  capaz  de  unir  inteligência  artificial, 
automação e experiência conversacional em um único ecossistema integrado. 

4.5 Funções Principais 

 
 
 
 
 
 
 
 
 
 
 
 
 
O sistema Jarvis é composto por um conjunto de funções modulares que interagem 
de forma coordenada entre os agentes e as Tools. 
  Essas funções representam as ações fundamentais executadas durante o ciclo de 
operação do sistema, desde o recebimento de mensagens até a geração e envio de 
respostas. 
  A  organização  das  funções  segue o princípio da separação de responsabilidades, 
garantindo clareza, reusabilidade e manutenção simplificada do código. 
As funções foram agrupadas em duas categorias principais: 

1.  Funções  relacionadas  aos  agentes,  responsáveis  pelo  raciocínio  e  pela 

coordenação das etapas de processamento; 

2.  Funções  associadas  às  Tools,  responsáveis  pela  execução  prática  das 

tarefas, como cálculos, consultas e formatações. 

4.5.1 Funções dos Agentes 
As  funções  dos  agentes  estão  diretamente  ligadas  às etapas do fluxo cognitivo do 
sistema. 
 Cada agente executa rotinas específicas que correspondem ao seu papel dentro da 
arquitetura multiagente. 
 A seguir, são descritas as principais funções implementadas em cada agente. 

a) PartnerAgent 

●  validate_input():  realiza  a  validação  inicial  da  mensagem  enviada  pelo 
formatação  com  base  em 

filtros  de  segurança  e 

usuário,  aplicando 
expressões regulares (Regular Expressions). 
  Essa 
excessivamente longas ou contendo conteúdo inadequado. 

função  impede  o  processamento  de  mensagens  malformadas, 

●  detect_intent(): 

identifica  a 

intenção  principal  da  mensagem  (registro, 
consulta,  configuração,  alerta  ou  gráfico),  utilizando  padrões  linguísticos  e 
análise semântica básica. 

●  route_message(): direciona a mensagem para o agente apropriado, conforme 

o tipo de solicitação identificado. 

três 

Essas 
solicitações do usuário e mantenha a coerência do fluxo de processamento. 

funções  asseguram  que  o  sistema 

interprete  corretamente  as 

b) SetupAgent 

●  create_categories(): conduz o processo de configuração inicial, solicitando ao 
usuário  as  categorias  de  gastos  desejadas  e  seus  respectivos  limites 
financeiros. 

 
 
 
 
 
 
 
 
●  set_limits(): define os limites de gasto por categoria e período, armazenando 

as informações na tabela user_rules. 

●  update_setup():  permite  a  atualização  posterior  das  categorias  e  limites, 

garantindo a personalização contínua do sistema. 

O  conjunto  dessas  funções  possibilita  que  o  sistema  se  adapte  às  preferências 
individuais de cada usuário, assegurando flexibilidade e personalização. 

c) FinanceAgent  
O  FinanceAgent  concentra  a  maior  parte  da  lógica  operacional  do  sistema,  sendo 
responsável  pela  manipulação  dos  dados  financeiros  e  pela  comunicação  com  as 
Tools. 
Suas principais funções são: 

●  record_expense():  realiza  o  registro  de  novas despesas após a confirmação 
do  usuário,  inserindo  os  dados na tabela transactions com os campos valor, 
categoria, descrição e created_at. 
  Também  atualiza  os  totais  acumulados  na  tabela  user_rules,  quando 
aplicável. 

●  analyze_expenses():  executa  consultas  no  banco  de  dados  para  gerar 
resumos e análises detalhadas por categoria, período ou limite de gasto. 

●  compare_spending(): 

realiza  comparativos  entre  períodos  distintos 
(semanais,  mensais  ou  personalizados),  calculando  variações  absolutas  e 
percentuais com base nas consultas realizadas. 

●  check_limits():  verifica  se  os  valores  acumulados  ultrapassaram  os  limites 
definidos  pelo  usuário  e,  em  caso  positivo,  aciona  o  envio  automático  de 
alertas. 

●  generate_plot():  solicita  à  PlotTool  a  criação  de  gráficos  personalizados,  de 

acordo com o período e as categorias selecionadas pelo usuário. 

Essas  funções  são  executadas  de  forma  orquestrada  pelo  agente,  que  decide 
dinamicamente quais Tools devem ser acionadas em cada situação. 

d) ValidadorAgent 

●  validate_output(): avalia se a resposta gerada pelos agentes e ferramentas é 

coerente com os parâmetros da solicitação original. 
  Verifica  a 
conformidade do formato textual. 

integridade  dos  dados,  a  consistência  dos  cálculos  e  a 

 
 
 
 
 
 
 
 
 
 
●  check_category_validity():  certifica-se  de  que  as  categorias  consultadas  ou 
mencionadas  existam  no  banco  de  dados  do  usuário,  prevenindo  erros  de 
execução. 

O  ValidadorAgent  atua  como  um  filtro  final  de  qualidade,  garantindo  que  apenas 
resultados consistentes sejam apresentados ao usuário. 

e) MessageAgent 

●  send_reminder_if_inactive(): verifica, periodicamente, o tempo desde a última 
interação do usuário e envia mensagens de lembrete em caso de inatividade 
prolongada. 
 Essa função utiliza o campo last_message_at da tabela users para calcular o 
intervalo de inatividade. 

●  schedule_daily_run():  agenda a execução automática de tarefas recorrentes, 

como o envio de lembretes diários e relatórios semanais. 

Embora  parte  dessas  funções  esteja  planejada  para  versões  futuras  (Pro),  sua 
estrutura  foi  projetada para garantir integração com agendadores externos, como o 
APScheduler. 

4.5.2 Funções das Tools 
As Tools contêm as funções que executam as ações práticas do sistema. 
  Elas  são  chamadas  pelos  agentes  conforme  a  necessidade  e  fornecem  os 
resultados que servirão de base para a formulação das respostas ao usuário. 
 As principais Tools e suas funções estão descritas a seguir. 

a) SQLTool 

●  create_tables():  inicializa  as  tabelas  do  banco  de  dados  (users,  categories, 

transactions e user_rules). 

● 

insert_transaction():  insere  novas  transações  na tabela transactions, com os 
respectivos campos de valor, categoria e data de criação. 

●  get_total_by_category():  retorna  o  total  de  gastos  de  um  usuário  em  uma 

categoria específica. 

●  get_total_by_period(): soma os gastos em um intervalo de tempo definido. 

●  update_rule_totals(): atualiza os totais acumulados na tabela user_rules após 

a adição de novos gastos. 

Essas  funções  garantem  o  correto  gerenciamento  das  informações financeiras e a 
consistência dos dados armazenados. 

 
 
 
 
 
 
 
 
 
 
 
b) CalculatorTool 

●  sum_values():  realiza  somas  de  valores  numéricos  provenientes  das 

consultas de gastos. 

●  avg(): calcula médias de despesas em períodos ou categorias específicas. 

●  percent_change():  calcula  variações  percentuais  entre  períodos  distintos, 

sendo utilizada nas análises comparativas. 

A CalculatorTool fornece suporte matemático essencial aos agentes, permitindo que 
os resultados apresentados sejam precisos e contextualizados. 

c) FilterTool 

● 

filter_by_category():  seleciona  os  registros correspondentes a uma categoria 
específica. 

● 

filter_by_period():  retorna  apenas  as  transações  dentro  de  um  intervalo  de 
datas. 

● 

filter_by_limit():  permite  consultas  filtradas  com  base  em  valores  máximos 
definidos pelo usuário. 

Essa ferramenta é empregada para refinar consultas e melhorar o desempenho das 
análises. 

d) FormatterTool 

● 

format_currency():  converte  valores  numéricos  para  o  formato  monetário 
brasileiro (R$). 

● 

format_message():  organiza  o  texto  final  que  será  enviado  ao  usuário, 
assegurando clareza e padronização nas respostas. 

A FormatterTool atua como a etapa final antes da entrega da resposta, contribuindo 
para a experiência de comunicação fluida e natural. 

e) PlotTool 

●  plot_piechart():  gera  gráficos  de  pizza  com  a  distribuição  dos  gastos  por 

categoria. 

●  plot_barchart(): cria gráficos de barras comparando períodos distintos. 

●  plot_timeseries(): elabora séries temporais com a evolução diária dos gastos. 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
●  export_plot():  exporta  o  gráfico  gerado  em  formato  de  imagem e o envia ao 

WhatsApp do usuário. 

A  PlotTool 
oferecendo suporte visual às análises realizadas pelos agentes. 

transforma  dados  quantitativos  em  visualizações  compreensíveis, 

4.5.3 Relação entre funções, agentes e Tools 
As funções dos agentes e das Tools estão interligadas em um fluxo contínuo. 
  O  PartnerAgent  interpreta  a  mensagem  e  direciona  a  solicitação; o FinanceAgent 
executa  o  raciocínio  financeiro  e  aciona  as  Tools  necessárias;  e  o  ValidadorAgent 
verifica a coerência da resposta antes do envio. 
  Esse  encadeamento  cria  um  ciclo  autônomo  de  raciocínio  e  ação,  em  que  cada 
função contribui para o processamento completo da solicitação do usuário. 
A  Tabela  4.2  apresenta  um  resumo  das  principais  funções  e  sua  relação  com  os 
agentes correspondentes. 

Tabela 4.2 – Principais funções e agentes responsáveis 

Agente/Tool 

Função principal 

Descrição resumida 

PartnerAgent  validate_input() 

Valida e formata a entrada do usuário. 

PartnerAgent  detect_intent() 

FinanceAgent 

record_expense() 

Identifica  a 
mensagem. 

Registra 
confirmadas. 

intenção  principal  da 

novas 

transações 

FinanceAgent  compare_spending() 

Calcula comparativos de períodos. 

FinanceAgent  check_limits() 

Verifica limites definidos pelo usuário. 

SetupAgent 

create_categories() 

Configura categorias e limites iniciais. 

ValidadorAge
nt 

validate_output() 

Confirma a coerência dos resultados. 

SQLTool 

get_total_by_category()  Consulta total de gastos por categoria. 

CalculatorToo
l 

percent_change() 

Calcula  variação  percentual  entre 
períodos. 

PlotTool 

plot_piechart() 

Gera  gráficos  visuais  e  envia  ao 
usuário. 

As  funções  descritas  acima  compõem  o  núcleo  lógico  e  operacional  do  sistema, 
assegurando  a  interação  harmoniosa  entre  raciocínio  textual,  execução  prática  e 
apresentação de resultados. 
  Essa  estrutura  modular  e  organizada  reflete  a  aplicação  dos  princípios  de 

 
 
 
 
engenharia  de  software  em  sistemas baseados em agentes inteligentes e modelos 
de linguagem natural. 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
4.6 Estrutura do Banco de Dados 

A  implementação  do  Jarvis  exige  uma  estrutura  de  dados  capaz  de  representar 
usuários, categorias de gastos, transações financeiras e regras de controle de limite 
por período. 

Optou-se pela utilização do SQLite, um banco de dados relacional leve e embutido, 
adequado ao contexto de desenvolvimento local e prototipagem do sistema. 

A escolha baseou-se em três fatores principais: 

(i)  integração  direta  com  Python,  permitindo  execução  dentro  do  ambiente  do 
notebook; 

(ii) simplicidade de configuração, dispensando servidores externos; e 

(iii)  compatibilidade  total  com  o  padrão  SQL,  o  que  possibilita  futura  migração 
transparente  para  bancos  mais  robustos,  como  o  PostgreSQL,  em  versões 
multiusuário. 

A  modelagem  relacional  do  sistema  foi  concebida  para  refletir  de  forma  direta  as 
regras de negócio descritas nas seções 4.1 a 4.5. 

Cada entidade corresponde a um componente funcional do Jarvis e se relaciona de 
modo a preservar integridade referencial e escalabilidade futura. 

4.6.1 Visão Geral da Arquitetura de Dados 

O banco é composto por quatro tabelas principais: 

1.  users – identifica cada pessoa que interage com o Jarvis via WhatsApp; 

2.  categories – armazena as categorias personalizadas de gasto de cada 

usuário; 

 
 
 
 
 
 
 
3.  transactions – registra o histórico detalhado das despesas; 

4.  user_rules – controla as regras de limite de gasto por categoria e período. 

A  Figura  4.6  (caso  adicionada)  pode ilustrar o relacionamento entre essas tabelas, 
conforme o diagrama lógico: 

None

users (1) 

 ├── categories (N) 

 │     ├── transactions (N) 

 │     └── user_rules (N) 

Essa estrutura adota o princípio de separação de responsabilidades: cada tabela 
mantém apenas as informações pertinentes ao seu domínio, reduzindo redundância 
e facilitando manutenção. 

4.6.2 users 

A tabela users guarda os dados de identificação e uso do sistema. 

O  campo  user_phone  é  utilizado  como  chave  primária,  pois  o  número  de 
WhatsApp é um identificador natural e único de cada usuário. 

Essa  escolha  elimina  a  necessidade  de  um  id  autoincremental  e  simplifica  a 
integração  com  a  API  do  WhatsApp,  já  que  todas  as  interações  são  rastreadas  a 
partir desse número. 

None

CREATE TABLE users ( 

    user_phone TEXT PRIMARY KEY, 

    user_name TEXT, 

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 

 
 
 
    last_message_at DATETIME, 

    days_inactive INTEGER DEFAULT 0 

); 

Essa  tabela  é utilizada pelos agentes PartnerAgent e MessageAgent para validar 
o remetente, atualizar a data da última mensagem e controlar o envio de lembretes 
automáticos. 

4.6.3 categories 

A  tabela  categories  armazena  as  categorias  personalizadas  definidas  por  cada 
usuário (ex.: “alimentação”, “transporte”, “lazer”). 

facilitar  o 
Cada  categoria  possui  um  category_id  autoincremental  para 
relacionamento  com  outras  tabelas,  e  mantém  uma  associação  direta  com 
user_phone. 

None

CREATE TABLE categories ( 

    category_id INTEGER PRIMARY KEY AUTOINCREMENT, 

    user_phone TEXT, 

    category_name TEXT, 

    description TEXT, 

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 

    FOREIGN KEY (user_phone) REFERENCES users(user_phone) 

); 

A  presença  do category_id simplifica consultas e permite renomear categorias sem 
quebrar vínculos de integridade com transactions ou user_rules. 

 
O  agente SetupAgent é responsável por inserir e atualizar esses registros durante 
o processo de configuração inicial. 

4.6.4 transactions 

A tabela transactions registra cada despesa individual comunicada pelo usuário. 

registro  contém  o  valor  gasto,  a  descrição 

Cada 
correspondente. 

textual  e  a  categoria 

O  campo  created_at  permite  análises  temporais,  comparativos  semanais  ou 
mensais e geração de gráficos. 

None

CREATE TABLE transactions ( 

    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, 

    user_phone TEXT, 

    category_id INTEGER, 

    amount REAL, 

    expense_description TEXT, 

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 

FOREIGN 

KEY 

(user_phone) 

REFERENCES 

users(user_phone), 

FOREIGN 

KEY 

(category_id) 

REFERENCES 

categories(category_id) 

); 

A  opção  por manter um identificador próprio (transaction_id) e relacionamentos por 
chaves  estrangeiras  simplifica  a  execução  de consultas agregadas e a geração de 
relatórios sem necessidade de junções complexas. 

O agente FinanceAgent é responsável por inserir esses dados e realizar consultas 
sumarizadas. 

 
    
    
4.6.5 user_rules 

A tabela user_rules implementa o mecanismo de controle de limites de gasto. 

Sua criação permite que um mesmo usuário tenha múltiplas regras por categoria, 
associadas a diferentes períodos (semanal, mensal ou personalizado). 

Dessa forma, é possível expressar restrições como 

“gastar no máximo R$ 200 com iFood por mês” e simultaneamente 

“gastar até R$ 80 com delivery por semana”. 

None

CREATE TABLE user_rules ( 

    rule_id INTEGER PRIMARY KEY AUTOINCREMENT, 

    user_phone TEXT, 

    category_id INTEGER, 

    period_type TEXT DEFAULT 'mensal', 

    period_start DATETIME DEFAULT CURRENT_TIMESTAMP, 

    period_end DATETIME, 

    limit_value REAL, 

    current_total REAL DEFAULT 0, 

    last_updated DATETIME, 

    active INTEGER DEFAULT 1, 

FOREIGN 

KEY 

(user_phone) 

REFERENCES 

users(user_phone), 

FOREIGN 

KEY 

(category_id) 

REFERENCES 

categories(category_id) 

 
    
    
); 

O  campo  current_total  é  atualizado  de  forma  incremental  a  cada  nova  transação, 
evitando a necessidade de somar novamente todos os registros de transactions. 

Quando  current_total  ultrapassa  limit_value,  o  ValidadorAgent  gera  um  alerta 
automático ao usuário. 

Os  campos  period_start  e  period_end  definem  o  intervalo  de  validade  da  regra, 
permitindo  que  o  sistema  reinicie  o  controle  ao  início  de  cada  novo  período,  de 
acordo com period_type. 

Essa  abordagem  modular  torna  o  Jarvis  flexível:  novas  regras  (por  trimestre, 
categoria  agrupada  ou  meta  de  economia)  podem  ser  inseridas  sem  alterar  a 
estrutura principal das tabelas. 

4.6.6 Discussões de Arquitetura e Escalabilidade 

A  modelagem  proposta  adota  princípios  de  normalização  (1FN  a  3FN), 
assegurando integridade e eliminando redundâncias. 

Os  relacionamentos  entre  as  entidades  seguem  o  padrão  1-para-N,  garantindo 
coerência lógica entre usuários, categorias e transações. 

A  escolha  do  SQLite  para  o  MVP  se  justifica  por  sua  leveza,  portabilidade  e 
integração  nativa  com  Python,  o que permite executar toda a aplicação localmente 
dentro do notebook, sem dependência de infraestrutura externa. 

No  entanto,  o  modelo  foi  construído  para  ser  compatível  com  PostgreSQL, 
bastando alterar a linha de conexão no código. 

Essa  compatibilidade  permite  que  versões  futuras  do  Jarvis  migrem  para  um 
ambiente  multiusuário  e  distribuído,  com  maior  tolerância  a  concorrência  e 
suporte a milhares de transações simultâneas. 

Em  ambientes  de  produção,  recomenda-se  substituir  o  SQLite  por PostgreSQL ou 
outro SGBD de nível servidor, a fim de: 

●  permitir acesso concorrente de múltiplos usuários via API (FastAPI + Twilio); 

●  garantir escalabilidade horizontal; 

 
 
 
●  e habilitar rotinas de backup, replicação e autenticação. 

Assim,  a  arquitetura  de  dados  mantém  a  simplicidade  necessária  ao 
desenvolvimento acadêmico e, ao mesmo tempo, prepara o sistema para expansão 
futura sem reformulação estrutural. 

4.6.7 Síntese Estrutural 

Tabela 

Chave 
Primária 

Chaves 
Estrangeiras 

Função Principal 

users 

user_phone  — 

Identificar  o  usuário  e  registrar 
metadados de interação. 

categorie
s 

category_id 

user_phone 

Armazenar 
personalizadas de cada usuário. 

categorias 

transactio
ns 

transaction_i
d 

user_phone, 
category_id 

Registrar  o histórico detalhado de 
gastos. 

user_rule
s 

rule_id 

user_phone, 
category_id 

Controlar 
períodos de verificação. 

limites  de  gasto  e 

Essa  estrutura  fornece  ao  Jarvis  uma  base sólida para integração com os agentes 
inteligentes  descritos  nas  seções  anteriores,  garantindo  coerência  entre  raciocínio 
linguístico, persistência de dados e execução de ações automatizadas. 

Quer que eu te monte também a versão em código (bloco único para notebook) 
dessa  estrutura  —  idêntica  ao  que  está  descrito  aqui,  já  pronta  para  executar  no 
SQLite local (jarvis.db)? 

 
 
 
 
 
 
 
 
