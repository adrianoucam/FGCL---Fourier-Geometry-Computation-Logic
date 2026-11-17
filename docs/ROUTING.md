# FGCL Route Lab — documentação acadêmica

Aplicação local CVRP/VRPTW inspirada no [visualizador da CVRPLib / PUC-Rio](https://galgos.inf.puc-rio.br/cvrplib/en/plot/835).
Data de consulta: 17/11/2026. A página específica não pôde ser recuperada pelo
navegador de pesquisa; a captura fornecida pelo usuário orientou o layout e as
interações. O catálogo oficial e as fontes abaixo foram consultados.
Não há vínculo institucional ou cópia da base de dados da CVRPLib.

## Executar

Na raiz do projeto, com NumPy instalado:

No Windows CMD, o caminho completo deste checkout é:

~~~cmd
cd /d E:\bc_niteroi_rj\fgcl-math\fgcl
python3 -m pip install -e .
python3 -m fgcl.route_app --port 8765
~~~

Em outros checkouts, entre na pasta que contém `pyproject.toml` e a subpasta
`fgcl` com `__init__.py`. Executar na pasta pai `fgcl-math` pode fazer o Python
encontrar a pasta externa como namespace sem `__version__`. O comando
`pip install .` também precisa da pasta que contém `pyproject.toml`.

Com o executável `python`, o comando equivalente do aplicativo é:

~~~bash
python -m fgcl.route_app --port 8765
~~~

Abra [http://127.0.0.1:8765](http://127.0.0.1:8765).
Também pode usar python3. Encerre com Ctrl+C. O servidor atende somente
127.0.0.1 e usa Python stdlib + NumPy; não precisa de Streamlit ou serviços
externos. Não é servidor de produção. Saídas em results/routing/ por padrão;
use --out OUTRA_PASTA para mudar. Arquivos da interface acompanham a instalação
pelo package-data do pyproject.toml.

A interface permite:

- Gerar dados sintéticos com seed, distribuição, capacidade e janelas opcionais.
- Importar instâncias e soluções locais, com numeração explícita.
- Exibir/ocultar rotas, selecionar clientes/rotas, ampliar, arrastar e ajustar.
- Usar setas e escolher a visibilidade das arestas do depósito.
- Animar veículos nos horários efetivamente calculados, incluindo espera/serviço.
- Comparar vizinho mais próximo, Clarke–Wright e refinamentos 2-opt.
- Inspecionar carga, saída, retorno, espera, duração e distância por rota.
- Visualizar fórmulas e exemplos numéricos calculados com a instância atual.
- Exportar SVG, JSON de experimento/instância, tabela CSV e solução .sol.
- Ativar a curva FGCL de diagnóstico espectral, explicitamente não executável.

A animação representa deslocamento linear entre os pontos originais. Não há
mapa viário, coordenadas geográficas, trânsito ou velocidade variável.

## 1. Modelo e notação

Um depósito 0, clientes V={1,...,n}, coordenadas p_i=(x_i,y_i), demandas q_i>=0,
capacidade homogênea Q>0, serviço s_i>=0, q_0=s_0=0.
Opcionalmente: janelas [a_i,b_i] para o início do atendimento e limite de frota K.

Uma rota é uma sequência r=(0,i_1,...,i_m,0). No código, a lista contém apenas
clientes; os dois extremos de depósito são adicionados pelo avaliador.
Cada cliente deve aparecer exatamente uma vez na solução completa.

Código: RoutingInstance, route_schedule, validate_routes, em fgcl/routing.py.

## 2. Distância e custo — geometria euclidiana e convenções do benchmark

$$
d_{ij}=\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}.
$$

Há duas convenções explícitas:

$$
c_{ij}=
\begin{cases}
\lfloor d_{ij}+0.5\rfloor,&\texttt{EUC_2D},\\
d_{ij},&\texttt{EXACT_2D}.
\end{cases}
$$

O arredondamento usa empate para cima, não o round bancário de Python.
A matriz é simétrica. Não há custo para coordenadas suavizadas ou vias reais.
A velocidade é 1 unidade de distância por unidade de tempo, de modo que
t_ij=c_ij; distâncias arredondadas também geram tempos arredondados.

Custo da rota:

$$
C(r)=c_{0i_1}+\sum_{k=1}^{m-1}c_{i_ki_{k+1}}+c_{i_m0}.
$$

CVRP usa distância total como objetivo entre candidatos; a convenção é informada
e não inferida a partir de um BKS. Solomon é importado como EXACT_2D, compatível
com a precisão e o objetivo hierárquico descritos pelo
[SINTEF](https://www.sintef.no/projectweb/top/vrptw/100-customers/).
EUC_2D segue a convenção TSPLIB; outras métricas são rejeitadas.

Código: distance_matrix e route_schedule.

## 3. Capacidade, cobertura e objetivos

$$
L(r)=\sum_{i\in r\setminus\{0\}}q_i\le Q,\qquad
\sum_r\mathbf1_{\{i\in r\}}=1\quad\forall i\in V.
$$

Com K fornecido, o validador também exige |R|<=K. Quando não fornecido, a
construção pode abrir mais veículos. O limite inferior elementar é:

$$
K_{\mathrm{cap}}=\left\lceil\frac{\sum_iq_i}{Q}\right\rceil.
$$

Esse é apenas um limite inferior por capacidade, não um limite para distância,
nem prova de ótimo do problema completo; janelas podem exigir mais veículos.

Objetivos declarados:

$$
\text{CVRP: }\min \sum_{r\in R}C(r),\qquad
\text{VRPTW: }\min_{\mathrm{lex}}\left(|R|,\sum_{r\in R}C(r)\right).
$$

A escolha lexicográfica prioriza frota; distância é comparada apenas em empate.
A interface compara poucos candidatos heurísticos, não todas as soluções.

Para exposição acadêmica, uma formulação por rotas seria usar todas as rotas
viáveis r da família F e variáveis binárias y_r:

$$
\sum_{r\in F:i\in r}y_r=1\quad(i\in V),\qquad
\sum_{r\in F}y_r\le K\ \text{(se houver K)},\qquad y_r\in\{0,1\}.
$$

CVRP minimizaria soma C(r)y_r, VRPTW minimizaria lex(soma y_r, soma C(r)y_r).
**Essa formulação não é resolvida pelo programa.** As construções produzem
conjuntos completos de rotas, que são avaliados diretamente.
Fonte das restrições: modelo clássico de roteamento; a formulação acima é uma
explicação matemática do contrato implementado, não um algoritmo extra.

## 4. Cronograma com janelas — propagação direta

Partida na abertura do depósito, D_0=a_0 (zero se não há janelas).
Em cada arco (i,j):

$$
A_j=D_i+c_{ij},\quad
B_j=\max(A_j,a_j),\quad
W_j=B_j-A_j,\quad
D_j=B_j+s_j,\quad
B_j\le b_j.
$$

A=chegada, B=início do serviço, W=espera, D=saída.
A janela limita o início: terminar depois de b_j não é automaticamente inválido.
O retorno final ao depósito deve respeitar b_0. Janelas são testadas com tolerância
absoluta de 1e-9 nas unidades do problema. Serviço no depósito é zero.

$$
T(r)=D_{\mathrm{retorno}}-D_{\mathrm{partida}},\quad
W(r)=\sum_{j\in r}W_j,\quad
T(r)=C(r)+\sum_{j\in r\setminus\{0\}}s_j+W(r).
$$

O último balanço vale na convenção velocidade 1 adotada aqui. Na interface,
tempo somado é soma T(r), não tempo de conclusão da frota. A linha de animação
usa tempo absoluto e inclui clientes esperando ou em serviço.

Exemplo do teste: depósito (0,0), clientes (3,0), (3,4), demandas 2 e 3,
Q=5, EXACT_2D, serviço 2 e 1, janela do cliente 1=[10,12].
Na rota 0→1→2→0, chegada ao cliente 1=3, espera=7, saída=12,
chegada ao cliente 2=16, saída=17, retorno=22. Distância=12 e duração=22.
Com fechamento do depósito em 20, essa ordem é rejeitada.

Essas recorrências são avaliação determinística da sequência, não solução do
problema combinatório. A convenção de VRPTW é contextualizada pelo SINTEF e por
[Solomon (1987)](https://doi.org/10.1287/opre.35.2.254); a adaptação do avaliador
e das heurísticas é código local FGCL.

## 5. Baseline: vizinho mais próximo viável

Dada a extremidade i, tente clientes remanescentes em ordem crescente (c_ij,j):

$$
j^*=\arg\min_{j\text{ remanescente e extensão viável}}(c_{ij},j).
$$

A verificação avalia a rota completa, incluindo retorno ao depósito.
Sem extensão viável, encerra a rota e inicia outra. Os empates usam índice
interno; não há aleatoriedade no solver. Se uma construção falhar, isso não
certifica que a instância inteira seja inviável.

Código: nearest_neighbor. Método guloso clássico implementado localmente;
não atribuímos essa implementação aos preprints matemáticos.

## 6. Economias de Clarke–Wright

Duas rotas unitárias teriam custo (c_0i+c_i0)+(c_0j+c_j0).
A rota unida 0→i→j→0 teria custo c_0i+c_ij+c_j0.
Por simetria, a economia é:

$$
s_{ij}=c_{0i}+c_{0j}-c_{ij}.
$$

Ordene economias decrescentes; tente unir rotas diferentes quando i,j são
extremidades. Oriente as sequências para ligar i→j, e teste também o percurso
total inverso. Só aceite rotas com carga e cronograma viáveis. Economias <=0
são ignoradas. Empates são determinísticos.

**Fonte:** G. Clarke; J. W. Wright (1964), Scheduling of Vehicles from a Central
Depot to a Number of Delivery Points, Operations Research 12(4), 568–581.
[DOI](https://doi.org/10.1287/opre.12.4.568).
Metadados/resumo da editora e trecho indexado do artigo com a economia foram
consultados. A checagem de janelas e a seleção da orientação por menor duração
são adaptações locais do FGCL, não reprodução integral do artigo.

Código: clarke_wright. A matriz e os pares de economia custam memória O(n²).
O trabalho de ordenação é O(n² log n); avaliar cronogramas acrescenta custo
dependente do tamanho das rotas. A implementação Python é didática, não um
solver competitivo para instâncias muito grandes.

## 7. Refinamento 2-opt

Para arestas (a,b) e (c,d) da mesma rota, substitua por (a,c),(b,d), revertendo
o segmento entre b e c. Com distância simétrica:

$$
\Delta=c_{ac}+c_{bd}-c_{ab}-c_{cd}.
$$

Aceitar somente se Delta<-1e-9, o custo recalculado diminuir e o cronograma
permanecer viável. No máximo duas passagens por rota e 20.000 verificações por
candidato completo. Não há troca entre veículos, relocação ou reparo de frota.

**Referência histórica:** G. A. Croes (1958), A Method for Solving Traveling-Salesman
Problems, Operations Research 6(6), 791–812.
[DOI](https://doi.org/10.1287/opre.6.6.791).
Metadados/resumo da editora consultados; o delta acima é deduzido pela diferença
das quatro arestas, e os limites de busca são escolhas locais. Não alegamos
implementar toda a técnica do artigo. Código: two_opt.

## 8. Participação do FGCL: análise espectral, não otimização disfarçada

Para r, forme z_l=(x_l,y_l) na ordem cíclica de visitas, com o depósito uma vez.
As amostras são uniformes em **índice de visita**, não tempo ou comprimento de arco.
Cada coluna recebe o filtro já existente da biblioteca:

$$
m(f_k)=\left(1-\frac{|f_k|^2}{c^2}\right)_+^\delta,\quad
\widetilde z=\mathrm{IFFT}\left[m\cdot\mathrm{FFT}(z)\right].
$$

Default c=.2 ciclos/visita, delta=1. O app usa
fgcl.fourier.bochner_riesz_filter, axes=(0,). O último ponto é repetido apenas
para fechar a curva visualizada, após o filtro.

$$
\mathrm{MSE}_{xy}=\frac1{2N}\sum_{\ell=0}^{N-1}
\|z_\ell-\widetilde z_\ell\|_2^2,\qquad
\rho=\frac{\sum_\ell\|z_\ell-\widetilde z_\ell\|_2^2}
{\sum_\ell\|z_\ell-\overline z\|_2^2}.
$$

Para denominador zero, rho é definido como zero. Rho é uma energia residual
de filtragem; não é contagem de frequências altas, grau de dificuldade ou
qualidade logística. Mudar a ordem ou a amostragem muda o diagnóstico.

A fórmula do multiplicador é clássica, documentada nas
[notas de Terence Tao](https://www.math.ucla.edu/~tao/247a.1.06f/notes4.pdf).
A aplicação à sequência de coordenadas é **adaptação exploratória local**.
Fontes históricas da biblioteca estão em SOURCES.md.

A curva pode deslocar clientes e depósito, violar janelas/capacidade interpretada
como visita e cortar caminhos. Portanto ela não substitui coordenadas, não altera
a solução, não entra no custo e não é usada pela animação. É habilitada por checkbox
e desenhada tracejada. Código: spectral_route.

O FGCL também fornece experiment_record: seeds, configuração, hashes de arrays
e textos importados, versões Python/NumPy/FGCL, CPU/plataforma e tempo. O relatório
completo inclui instância e rotas para recomputação.

## 9. Importação e exportação

### JSON FGCL

~~~json
{
  "name": "triangulo",
  "coordinates": [[0,0],[3,0],[3,4]],
  "demands": [0,2,3],
  "capacity": 5,
  "distance": "EXACT_2D",
  "ids": [0,1,2],
  "vehicles": null,
  "windows": [[0,30],[10,12],[0,30]],
  "service": [0,2,1]
}
~~~

Depósito na primeira linha; demands[0]=service[0]=0. Windows, service, ids,
vehicles são opcionais. Sem windows é CVRP. Todos os valores numéricos devem
ser finitos. As janelas começam em tempo não negativo.

### VRPLIB .vrp

Suporta TYPE: CVRP, EDGE_WEIGHT_TYPE: EUC_2D, DIMENSION, CAPACITY,
NODE_COORD_SECTION, DEMAND_SECTION e um DEPOT_SECTION terminado por -1.
IDs originais são preservados; o depósito é movido para índice interno 0 e os
demais IDs são ordenados para índices 1…n. Seções/arestas não suportadas são
rejeitadas, em vez de ignorar restrições. Não há EXPLICIT, ATT, GEO, múltiplos
depósitos, pickup-delivery, duração máxima de rota ou janelas VRPLIB arbitrárias.
O cabeçalho opcional VEHICLES é preservado como limite de frota. Cabeçalhos
desconhecidos são rejeitados para não omitir restrições como DISTANCE.

### Solomon .txt

Nome, seção VEHICLE com número/capacidade, seção CUSTOMER com sete colunas:
ID X Y DEMAND READY DUE SERVICE. Depósito de ID 0 na primeira linha.
Usa EXACT_2D e preserva o limite de veículos informado.

O formato XTW do screenshot não foi baixado ou implementado por inferência.
Se não for Solomon, converter as restrições explicitamente para o JSON suportado.
Nunca remover janelas para transformar um VRPTW em CVRP e comparar os custos.

### Soluções .sol ou JSON

~~~text
Route #1: 1 2
Cost 12
~~~

~~~json
{"numbering":"external","routes":[[11,90]]}
~~~

Selecione internal (índices normalizados 1…n) ou external (IDs originais).
Depósito implícito: não incluir nas listas. A aplicação recalcula o custo e
verifica cobertura, carga, janelas e frota. O valor Cost declarado é ignorado.
Só soluções importadas viáveis podem ser escolhidas no mapa. Soluções inválidas
têm suas violações expostas e não são apresentadas como viáveis.

O .sol exportado usa índices internos; o nome do arquivo informa isso. Para
reutilizá-lo com os mesmos índices, exporte também a instância JSON. O JSON de
relatório contém índices internos e o mapeamento ids; CSV inclui métricas por rota.

## 10. Exemplo pequeno e protocolo experimental

~~~bash
python -m examples.routing_demo --customers 80 --seed 42
python -m examples.routing_demo --customers 80 --seed 42 --time-windows
python -m unittest discover -s tests -v
~~~

O primeiro comando de referência (CVRP, agrupado, Q=60, EUC_2D) produziu:

| Método | Rotas | Distância |
|---|---:|---:|
| Vizinho mais próximo | 8 | 1016 |
| Vizinho + 2-opt | 8 | 966 |
| Clarke–Wright | 8 | 859 |
| Clarke–Wright + 2-opt | 8 | 855 |

São resultados sintéticos desta seed, não performance em benchmarks ou BKS.
Todos os custos usam a mesma instância original. Não há hipótese de que o filtro
espectral melhore o solver; seria um estudo novo com baseline próprio.

Para um trabalho acadêmico: definir datasets/versões/hashes, convenções de custo,
orçamento de tempo, múltiplas instâncias/seeds e medidas pareadas por instância;
reportar viabilidade, frota, distância, tempo e falhas. Comparar BKS somente após
compatibilizar formato, arredondamento, objetivo e todas as restrições.
Não inferir significância estatística a partir de arestas ou clientes correlacionados.

## 11. Limitações e referências

- Heurísticas podem produzir mais veículos do que K, mesmo havendo solução
  melhor. NO_FEASIBLE_CANDIDATE não é certificado de inviabilidade.
- Ótimo nunca é certificado no aplicativo. Testes exaustivos são apenas oráculos
  para exemplos minúsculos.
- Um depósito, demanda não negativa, frota homogênea, custos simétricos, velocidade 1.
- Limites: até 1000 clientes, arquivo até 2 MB, requisição até 4.1 MB.
- CPU e memória O(n²); limites de clientes não garantem latência interativa.
- Análise espectral não foi validada como métrica de qualidade de rota.
- Servidor é local, sem autenticação ou infraestrutura de hospedagem de produção.

Referências consultadas em 17/11/2026:

1. [CVRPLib, catálogo oficial](https://galgos.inf.puc-rio.br/cvrplib/en/instances):
   instâncias e identificação do benchmark, sem importação automática de BKS.
2. [SINTEF, Solomon 100 customers](https://www.sintef.no/projectweb/top/vrptw/100-customers/):
   objetivo hierárquico e distância/tempo em precisão dupla.
3. [Clarke & Wright (1964)](https://doi.org/10.1287/opre.12.4.568):
   metadados/resumo da editora e trecho indexado da fórmula de economia.
4. [Croes (1958)](https://doi.org/10.1287/opre.6.6.791):
   metadados/resumo; referência histórica de 2-opt.
5. [Solomon (1987)](https://doi.org/10.1287/opre.35.2.254):
   referência bibliográfica do benchmark; não foi feita auditoria integral do artigo.
6. [TSPLIB95, Reinelt](https://www.iwr.uni-heidelberg.de/groups/comopt/software/TSPLIB95/):
   referência para EUC_2D. A tentativa de recuperar o manual PDF nesta sessão
   expirou; a implementação do arredondamento é explicitamente definida acima.
7. [Tao, notas de análise harmônica](https://www.math.ucla.edu/~tao/247a.1.06f/notes4.pdf):
   multiplicador clássico; consulta anterior registrada em SOURCES.md.

Nenhuma fórmula logística é atribuída a Cairo, Cairo–Zhang ou aos preprints de
openai/math. Reaproveitar a infraestrutura FGCL não transfere as alegações
matemáticas dessas fontes ao problema de roteamento.

