# Avaliação seletiva e fontes das ideias

Consulta: **17 de novembro de 2026**. Repositório: [openai/math/preprints](https://github.com/openai/math/tree/main/preprints).

## Escopo e qualidade da evidência

Esta é uma triagem para engenharia do FGCL, com leitura de um trecho matemático
selecionado; **não é uma revisão integral dos manuscritos ou validação das provas**.
O [README da coleção](https://github.com/openai/math/blob/main/README.md) informa
níveis diferentes de verificação e possíveis problemas em resultados não
formalizados. A existência de uma formalização na coleção não certifica outros
manuscritos nem o código NumPy deste projeto.

Foram consultados o README, o [catálogo overview.tex](https://github.com/openai/math/blob/main/overview.tex)
e as convenções de análise booleana abaixo. O índice CONTENTS foi localizado,
mas seu conteúdo integral não foi recuperado. O acesso direto via conector
GitHub e HTTPS local falhou; o mecanismo de pesquisa/navegação recuperou os
textos indicados. Os PDFs de extensão e Bochner–Riesz não puderam ser lidos
nesse acesso. Essas duas seleções são **baseadas no catálogo**, não em leitura
das provas. URLs usam `main`, que pode mudar; não foi obtido SHA do commit.
Não apresentamos esses links como um snapshot imutável. Antes de uma publicação,
fixar revisão e hashes dos documentos efetivamente utilizados.

## Registro de decisões

| ID | Fonte e nível de leitura | Ideia aproveitada | Implementação / limite |
|---|---|---|---|
| `oai-extension-2026` | [Diagonal Fourier extension for positively curved surfaces in three dimensions](https://github.com/openai/math/tree/main/preprints/Diagonal-Fourier-extension-for-positively-curved-surfaces-in-three-dimensions-September-24-2026), resumo no catálogo | Estudar operadores de extensão com geometria explícita | `FourierExtension`: soma finita com quadratura fornecida pelo usuário, em qualquer dimensão. Não implementa a prova, hipóteses geométricas ou estimativas contínuas alegadas. |
| `oai-br-2026` | [Bochner–Riesz Multipliers in Three Dimensions](https://github.com/openai/math/tree/main/preprints/Bochner-Riesz-Multipliers-in-Three-Dimensions-September-24-2026), resumo no catálogo | Família radial de controles espectrais parametrizada por ordem e corte | `bochner_riesz_mask/filter`: multiplicador clássico em grade periódica. Fórmula e discretização são escolhas padrão de engenharia, não novidade atribuída ao preprint. Não valida limites Lp em R³. |
| `oai-ug-conventions-2026` | [The Unique Games Theorem, seção Conventions](https://github.com/openai/math/blob/main/preprints/The-Unique-Games-Theorem-September-23-2026/build/sections/01-preliminaries.tex), trecho efetivamente lido: Binary linear algebra and Fourier analysis | Convenção normalizada de Fourier em F₂ e identidade de Parseval | `walsh_transform` e `boolean_spectrum`. Identidades clássicas; não implementa o teorema Unique Games, redução, repetição paralela ou decodificador do manuscrito. |
| `fgcl-engineering-2026` | Código e testes locais | CPU, funções independentes, controles e rastreabilidade | `reproducibility.py`, exemplo e testes; contribuição de engenharia local, sem alegação de origem em preprint. |

## Outras linhas examinadas na triagem

- **Kakeya:** pertinente à motivação geométrica, mas os histogramas existentes
  não medem normas maximais de tubos. Adiada implementação que exigiria uma
  discretização geométrica e estudo de convergência próprios.
- **Convergência de Fourier em L log L e suavização local:** testes finitos não
  estabelecem convergência quase em toda parte nem estimativas assintóticas.
  Não foram adicionados como métodos certificados.
- **DFT abaixo de n log n:** o catálogo explicita um modelo de aritmética
  complexa exata. Isso não justifica trocar `numpy.fft` nem anunciar aceleração
  prática em ponto flutuante. Mantido FFT como baseline.
- **Complexidade/SAT:** não se importou qualquer alegação sobre ETH ou jogos
  como solver SAT. O novo módulo booleano enumera uma tabela inteira e tem
  custo exponencial no número de bits; não produz certificado UNSAT.
- **Teoria dos números, geometria algébrica e outras famílias:** sem aplicação
  direta estabelecida ao FGCL nesta revisão seletiva; não avaliadas em detalhe.

Esses itens são decisões de escopo baseadas no catálogo, não pareceres sobre a
correção dos manuscritos. As provas da coleção não foram auditadas.

## Separação das alegações

1. **Fonte:** assuntos e convenções explicitamente descritos nos links acima.
2. **Aproximação numérica:** operadores finitos, periodicidade, quadratura e
   erros de ponto flutuante documentados em [LIBRARY.md](LIBRARY.md).
3. **Hipótese aplicada:** utilidade em deepfake, XAI, volumes e SAT depende de
   experimentos futuros. Nenhum ganho nesses domínios foi demonstrado aqui.

As fontes anteriores de Cairo e Cairo–Zhang permanecem no README histórico.
Nenhum novo método constitui reprodução ou prova desses contraexemplos.

## Como atualizar este registro

### FGCL Route Lab (17/11/2026)

O módulo de roteamento e o aplicativo local têm uma documentação própria de
[fórmulas, fontes e adaptações](ROUTING.md). IDs utilizados nos relatórios:

- `clarke-wright-1964`: [Clarke & Wright](https://doi.org/10.1287/opre.12.4.568),
  economias de união; metadados/resumo da editora e trecho indexado da fórmula.
- `cvrplib-conventions`: [CVRPLib](https://galgos.inf.puc-rio.br/cvrplib/en/instances)
  como contexto e [SINTEF Solomon](https://www.sintef.no/projectweb/top/vrptw/100-customers/)
  para objetivo hierárquico e precisão. A imagem fornecida pelo usuário orientou
  o layout; a página específica de plot não pôde ser recuperada na pesquisa.
- `fgcl-bochner-riesz`: reaproveitamento do filtro FGCL clássico documentado
  acima. Aplicar às coordenadas por índice de visita é adaptação exploratória
  local; não representa algoritmo de otimização de rotas.

2-opt tem referência histórica em [Croes (1958)](https://doi.org/10.1287/opre.6.6.791),
com metadados/resumo consultados; avaliação de janelas e heurísticas são locais.
O roteamento não é derivado dos teoremas de Cairo ou dos preprints openai/math.

### Referências adicionais consultadas para o README público (17/11/2026)

- [NumPy, Discrete Fourier Transform](https://numpy.org/doc/stable/reference/routines.fft.html):
  convenções de sinal/normalização da FFT e IFFT; documentação consultada.
- [SciPy, scipy.fft.dct](https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.dct.html):
  definição da DCT-II e normalização ortogonal; documentação consultada.
- [Terence Tao, Lecture Notes 4 de análise harmônica](https://www.math.ucla.edu/~tao/247a.1.06f/notes4.pdf):
  fórmula clássica do multiplicador de Bochner–Riesz localizada no texto indexado.
  Referência à definição, sem auditoria das provas ou atualização de conjecturas.
- [Cairo, arXiv:2502.06137v2](https://arxiv.org/abs/2502.06137v2) e
  [Cairo–Zhang, arXiv:2512.08064v1](https://arxiv.org/abs/2512.08064v1):
  metadados e resumos consultados para contextualizar a motivação histórica.
  Esse acesso não constitui nova leitura integral dos artigos.

Essas referências documentam convenções e motivação. Não atribuímos às fontes
externas as escolhas de implementação, normalização de máscaras ou clipping.

Para cada nova ideia: registrar URL e revisão, seção realmente lida, hipótese
matemática, adaptação numérica, baseline, teste, limitação e exemplo. Relatórios
de execução usam os IDs desta tabela em `sources`; seus hashes cobrem arrays
de entrada, **não** os documentos remotos. Não copiar código ou artefatos do
repositório de origem sem verificar seus termos de licença.
