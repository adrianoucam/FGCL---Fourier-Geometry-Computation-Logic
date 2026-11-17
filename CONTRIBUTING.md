# Contribuindo com o FGCL

Leia `AGENTS.md`, `docs/LIBRARY.md` e `docs/SOURCES.md` antes de propor mudanças.
Use uma branch própria e descreva o problema e o comportamento esperado.

Cada novo método deve incluir:

1. Configuração e contrato de entrada/saída documentados.
2. Origem das fórmulas, referências e seção realmente consultada.
3. Separação entre identidade matemática, discretização e hipótese aplicada.
4. Baseline, teste significativo, resultado mensurável e exemplo reproduzível.
5. Limites de domínio, memória, tempo e precisão, com execução em CPU.

Não adicione checkpoints ou datasets ao repositório. Preserve a ordem original
de classes e não introduza treinamento ou downloads implícitos. Documente splits
por vídeo/identidade. Métodos opcionais devem continuar opcionais.

Na raiz do checkout:

```bash
python -m pip install -e ".[images]"
python -m unittest discover -s tests -v
python -m examples.library_smoke --seed 42 --out results/library.json
```

No PR, descreva a mudança, a validação realmente executada e as limitações.
Resultados negativos também devem ser registrados. Não confunda execução local
dos testes com sucesso do workflow remoto. O licenciamento deve ser definido
pelo titular antes de aceitar contribuições com direitos de redistribuição.
