# Biblioteca FGCL 0.3

Aplicação de roteamento disponível: `python -m fgcl.route_app --port 8765`.
Consulte [ROUTING.md](ROUTING.md) para CVRP/VRPTW, fórmulas, fontes e exemplos.

**FGCL — Fourier, Geometry, Computation & Logic.** Biblioteca Python para
análise espectral, computação geométrica e exploração de funções lógicas,
com experimentos numéricos reproduzíveis.

Instalação local: `python -m pip install -e .`. Python >=3.10, NumPy >=1.24,<3.
Pillow é necessário para ler imagens do benchmark (`.[images]`). SciPy acelera
a DCT quando instalado; DCT e AUC agora também funcionam sem SciPy. PyTorch e
Captum continuam opcionais. Nenhuma API nova baixa dados ou treina modelos.

## Extensão finita de Fourier

```python
import numpy as np
from fgcl import FourierExtension

theta = np.linspace(0, 2*np.pi, 64, endpoint=False)
nodes = np.column_stack((np.cos(theta), np.sin(theta)))
targets = np.array([[0., 0.], [1., 0.], [0., 1.]])
operator = FourierExtension(nodes, targets, weights=np.full(64, 2*np.pi/64),
                            block_size=16)
field = operator.apply(np.ones(64))
backprojected = operator.adjoint(field)
```

`nodes`: [N,d], `targets`: [M,d], pesos positivos [N]; sem pesos usa q=1,
não q=1/N. Convenção: `E f(x)=sum q_j f_j exp(2πi x·xi_j)`.
`adjoint` é o adjunto **euclidiano** dessa matriz, incluindo q, não uma inversa
nem adjunto em produto interno ponderado. Para quadratura de superfície, o
chamador define os nós, pesos e sua precisão.

Custo O(MNd), memória temporária O(block_size*N), além dos arrays de entrada e
saída. O bloco limita somente a matriz temporária, não toda a memória do processo.
Aplicável a campos de ondas e amostragem espectral irregular em 1D/2D/3D.
Limites: não há NUFFT, solver inverso, certificação geométrica ou controle
automático do erro de quadratura. Baselines: matriz exponencial direta e
`numpy.fft.ifft` em nós compatíveis; erros medidos nos testes e exemplo.

## Bochner–Riesz em grades

```python
from fgcl import bochner_riesz_filter, bochner_riesz_mask

signal = np.cos(2*np.pi*np.arange(64)/16)
filtered = bochner_riesz_filter(signal, cutoff=.2, order=1.)
image = np.ones((32, 48, 3))
filtered_image = bochner_riesz_filter(image, axes=(0, 1))
volume = np.ones((16, 20, 24))
filtered_volume = bochner_riesz_filter(volume, spacing=(1., 1., 2.))
```

Máscara `max(1-|xi|²/cutoff²,0)^order`, frequências em ciclos por unidade de
`spacing`; corte default .25, ordem default 1, espaçamento default 1.
Ordem zero é o indicador da **bola aberta**, excluindo a fronteira.
`spacing` escalar ou um valor por eixo transformado, na ordem de `axes`.
`axes=None` transforma todos os eixos; imagens HWC precisam de `(0,1)`.
Não há clipping ou normalização de intensidades, e sinais complexos são aceitos.

Custo FFT O(P log P), memória O(P); volume grande exige dimensionamento pelo
chamador. Baselines: identidade, resposta analítica a modo de Fourier e corte
brusco (`order=0`). Saídas: array filtrado, MSE com referência quando disponível.
Periodicidade pode criar artefatos nas bordas; tratar padding externamente.
Não constitui estimativa contínua de Bochner–Riesz ou ganho perceptual comprovado.
O filtro é independente do benchmark: não foi inserido implicitamente entre
as variantes com comparação a distorção casada.

## Fourier booleano

```python
from fgcl import walsh_transform, boolean_spectrum

# f(x)=(-1)^(x0+x2); índice inteiro codifica bits a partir do menos significativo.
truth = np.array([(-1)**((x & 5).bit_count()) for x in range(16)])
report = boolean_spectrum(truth)
restored = walsh_transform(report['coefficients'], inverse=True)
```

Transformada direta Hf/N, inversa Hf. `N=2^d`, inclusive d=0, entrada finita
real ou complexa. Parseval: soma |f_hat|² = média |f|². Retorna coeficientes,
energia por grau de Hamming, média, energia total e influências por coordenada.
Influência = média |f(x)-f(x xor 2^i)|²/4; só coincide com a probabilidade usual
de mudança para funções em {-1,+1}. Para {0,1}, converter antes se desejar essa
interpretação. Baselines: matriz de caracteres direta, diferenças de bits e
paridade conhecida. Transformada O(N log N), memória O(N); espectro por grau
tem custo adicional O(Nd). Tabela completa é exponencial em d. Limite default
`max_size=2^20` é configurável; não deve ser aumentado sem estimar memória.
Útil em pequenas funções lógicas, sensibilidade e descritores, não solver SAT.

## Execuções rastreáveis

```python
from fgcl.reproducibility import experiment_record

seed = 42
rng = np.random.default_rng(seed)
x = rng.normal(size=32)
with experiment_record('results/run.json', seed=seed,
                       config={'cutoff': .25}, inputs={'signal': x},
                       sources=['oai-br-2026']) as metrics:
    y = bochner_riesz_filter(x)
    metrics['mse_vs_identity'] = float(np.mean((x-y)**2))
```

Registra seed, config, versões FGCL/NumPy/Python, plataforma/processador,
backend CPU, início UTC, tempo e SHA-256 de dtype/shape/bytes de cada array.
Não fixa geradores globais. Config e métricas devem ser JSON finito; converter
escalares/arrays NumPy com `float`/`tolist`. Exceções são propagadas e registradas.
Use um caminho exclusivo por execução concorrente. Não faz snapshot de ambiente,
checkpoint, BLAS ou documentos; hashes de arrays não substituem esses controles.
Esse registro é opt-in e não muda relatórios das APIs históricas.

## Exemplo e verificação

```powershell
python -m examples.library_smoke --seed 42 --out results/library.json
python -m unittest discover -s tests -v
```

O exemplo mede MSE contra identidade em sinal sintético, erro contra IFFT e
erros de Parseval/inversão Walsh. Seus números são checks numéricos, não
evidência de desempenho em dados reais. Reexecute com outros tamanhos,
resoluções e configurações antes de concluir sobre estabilidade.

[Fontes e avaliação seletiva](SOURCES.md). APIs v0.1/v0.2 permanecem disponíveis;
consulte também [README_v0.2.md](../README_v0.2.md).
