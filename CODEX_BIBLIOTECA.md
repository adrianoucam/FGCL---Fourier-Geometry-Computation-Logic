# FGCL — Guia de consulta e pesquisa para o Codex

Nome completo: **Fourier, Geometry, Computation & Logic**. Biblioteca Python
para análise espectral, computação geométrica e exploração de funções lógicas,
com experimentos numéricos reproduzíveis.

Use este arquivo como contexto para buscar informações, explicar APIs e propor
ideias para a biblioteca FGCL. As instruções de `AGENTS.md` continuam aplicáveis.

## Prompt pronto para usar

> Trabalhe no projeto `E:\bc_niteroi_rj\fgcl-math\fgcl` e leia
> `CODEX_BIBLIOTECA.md` e `AGENTS.md`. Consulte a documentação, o código e os
> testes antes de responder. Explique quais recursos da biblioteca atendem ao
> meu objetivo, mostre um exemplo mínimo e pesquise ideias relevantes nas fontes
> originais quando necessário. Distinga o que já está implementado, o que é uma
> proposta e o que foi efetivamente validado. Registre as novas fontes consultadas
> com seus limites de verificação. Meu objetivo nesta consulta é: [descreva aqui].

## Onde procurar primeiro

Todos os caminhos abaixo são relativos à raiz deste projeto. Confirme o conteúdo
atual: este guia é um mapa, não substitui a leitura das implementações.

| Pergunta | Arquivos a consultar |
|---|---|
| Quais regras científicas e operacionais seguir? | `AGENTS.md` |
| Como instalar e começar? | `README.md`, `pyproject.toml` |
| Como usar a API 0.3 e configurar os métodos? | `docs/LIBRARY.md`, `fgcl/__init__.py` |
| De onde vieram as ideias? | `docs/SOURCES.md` |
| Extensão de Fourier, adjunto e filtragem em N dimensões | `fgcl/fourier.py`, `tests/test_library.py` |
| Transformada de Walsh, energia por grau e influência | `fgcl/boolean.py`, `tests/test_library.py` |
| Seeds, hashes, versões, hardware e tempo | `fgcl/reproducibility.py` |
| Exemplo reproduzível e resultado local | `examples/library_smoke.py`, `results/library.json` |
| FFT/DCT, máscaras e distorção casada | `fgcl/spectral.py`, `fgcl/core.py` |
| Avaliação de classificadores e dados agrupados | `README_v0.2.md`, `fgcl/benchmark.py`, `fgcl/metrics.py` |
| Modelos existentes e checkpoints | `fgcl/adapters.py`, `examples/model_module_template.py` |
| Explicabilidade e estabilidade | `fgcl/xai.py` |
| Exemplos geométricos e SAT com testemunha | `fgcl/core.py`, `fgcl/sat.py`, `tests/test_core.py` |
| Comandos disponíveis | `fgcl/__main__.py` |
| Aplicativo local CVRP/VRPTW e fórmulas de roteamento | `docs/ROUTING.md`, `fgcl/routing.py`, `fgcl/routing_io.py`, `fgcl/route_app.py`, `tests/test_routing.py` |

## Recursos que já existem

- `FourierExtension(nodes, targets, weights=None, block_size=256)`: soma
  quadraturada finita com fase positiva `exp(2πi x·xi)`. `apply` calcula o campo;
  `adjoint` calcula o adjunto euclidiano, não uma inversa. Pesos omitidos valem 1.
- `bochner_riesz_mask` e `bochner_riesz_filter`: filtros em grade periódica,
  com corte, ordem, espaçamento e eixos explícitos. Em imagens HWC, usar
  `axes=(0, 1)` para preservar os canais. Não há clipping automático.
- `walsh_transform`: Fourier normalizado no cubo booleano, com inversão.
  `boolean_spectrum`: energia por grau e energias de mudança de coordenadas.
  Trabalha sobre tabela completa; custo exponencial no número de bits.
- `experiment_record`: contexto opt-in para registrar métricas e metadados.
  Recebe os arrays de entrada para hashing; não configura o RNG global.
- APIs históricas: descritores FFT/DCT, perturbações controladas, avaliação
  de probabilidades, bootstrap por grupo, XAI opcional e instâncias SAT plantadas.

As assinaturas completas, fórmulas e limites estão em `docs/LIBRARY.md` e no código.
Não invente parâmetros, comandos ou suporte a GPU que não existam na API.

## Como responder a uma consulta

1. Identifique o objetivo: sinal, imagem, volume, função booleana, avaliação
   de modelo, XAI ou experimento geométrico.
2. Localize a função e os testes pertinentes com `rg`; verifique a assinatura.
3. Explique o recurso em português, incluindo formato de entrada, saída,
   normalização, periodicidade, custo e dependências que forem relevantes.
4. Forneça um exemplo mínimo com dados sintéticos e seed explícita quando houver
   aleatoriedade. Exemplos sintéticos verificam funcionamento, não desempenho real.
5. Cite o arquivo local que sustenta a explicação. Para ideias externas, cite
   a fonte primária e a seção consultada.
6. Informe o que a evidência permite concluir e o que permanece em aberto.

## Como buscar novas ideias

Comece em `docs/SOURCES.md`. Para a coleção externa, consulte o
[README](https://github.com/openai/math/blob/main/README.md), o
[catálogo](https://github.com/openai/math/blob/main/overview.tex) e os
[preprints](https://github.com/openai/math/tree/main/preprints).
Use o catálogo para selecionar trabalhos; leia o trecho original antes de
atribuir um algoritmo ou uma fórmula específica a um manuscrito.

Para cada fonte nova, registre em `docs/SOURCES.md`:

- Título, autores conforme a fonte, URL e data de acesso.
- Commit, versão e hash quando efetivamente obtidos; nunca inventar esses dados.
- O que foi lido: catálogo, resumo, seção, prova ou artefato executável.
- Ideia aproveitada, hipóteses e diferença para a adaptação finita do FGCL.
- Estado: referência apenas, proposta, implementação ou validação executada.
- Arquivos relacionados, baseline, teste, exemplo e limitações.

Se o acesso falhar, declare isso e limite as conclusões ao material recuperado.
Não trate manuscritos, formalizações alheias ou testes NumPy como certificação
automática de outras alegações. Não copie código externo sem verificar a licença.

## Ideias para investigar, ainda não implementadas neste guia

| Linha | Experimento inicial | Baseline e evidência necessária |
|---|---|---|
| Convergência da quadratura de extensão | Refinar nós de uma curva conhecida | Solução analítica ou referência de alta resolução; erro versus número de nós |
| Bordas em filtragem espectral | Comparar periodicidade com padding explícito | Mesma entrada e recorte; erro na borda e no interior |
| Controles Bochner–Riesz em imagens | Comparar ordens e cortes | Identidade, passa-baixa e controles a MSE casado; não concluir por aparência |
| Análise de pequenas funções lógicas | Comparar espectro e diferenças por bit | Enumeração direta e funções de paridade conhecidas; custo de memória explícito |
| Agregação de vídeos | Combinar probabilidades de frames por grupo | Métricas por vídeo e bootstrap por grupo; splits sem vazamento |
| Tomografia | Definir phantom e operador de projeção | Radon de referência, erro de reconstrução e controle de vistas |

Essas linhas são propostas de engenharia/pesquisa, não resultados atribuídos
aos preprints. Não anunciar ganho, novidade matemática ou aceleração sem medir.
Uma consulta por informações ou ideias não autoriza treinamento, downloads de
checkpoints ou implementação de todas as propostas.

## Quando a solicitação incluir implementação

- Preserve a API existente e checkpoints do usuário; CPU é obrigatória.
- Documente configuração, limites de memória e tempo, e domínio de validade.
- Adicione baseline, teste significativo, resultado mensurável e exemplo pequeno.
- Registre seed, configurações, versões, hardware, tempo e hashes das entradas.
- Preserve ordem de classes, probabilidades normalizadas e separação por grupo.
- SAT exige testemunha validada; UNSAT exige prova ou solver certificado;
  timeout é UNKNOWN.
- Execute a suíte abaixo após alterações de código e relate o resultado real.

## Comandos de verificação

Execute na **raiz do projeto**, não dentro da pasta `tests`:

```powershell
Set-Location 'E:\bc_niteroi_rj\fgcl-math\fgcl'
python -m unittest discover -s tests -v
python -m examples.library_smoke --seed 42 --out results/library.json
```

Se o interpretador configurado pelo usuário for `python3`, substitua `python`
por `python3` nos dois comandos. Leia o relatório gerado antes de interpretar
suas métricas. Quantidade de testes, versões e tempos podem mudar; obtenha-os
da execução atual.
