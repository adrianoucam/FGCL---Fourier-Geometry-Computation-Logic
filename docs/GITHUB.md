# Publicação no GitHub

Destino solicitado: conta `adrianoucam`, repositório público. Nome proposto:
`fgcl`. A existência de um arquivo local não significa que o repositório já
tenha sido criado ou publicado; verifique a URL após a operação remota.

## Conteúdo preparado

- README em português com funcionamento, fórmulas, referências e exemplos.
- Código do pacote, testes, exemplos e documentação de fontes.
- `.gitignore` para resultados locais, ambientes, datasets e checkpoints.
- Workflow GitHub Actions de testes em Windows e Linux, Python 3.10 e 3.12.

O workflow só terá resultado remoto depois de ser enviado e executado no GitHub.
A licença ainda depende de escolha do titular; não foi atribuída uma licença
automaticamente. Um repositório público sem licença não equivale a software
com licença aberta.

## Publicação manual, se a conexão automática não estiver disponível

Crie um repositório público chamado `fgcl` na conta desejada, vazio, sem README
gerado automaticamente. Se já existir um repositório com conteúdo, inspecione-o
antes de configurar o remoto. Não use `push --force` para substituir conteúdo.

Na raiz local, quando ainda não houver repositório Git:

```bash
git init -b main
git add .
git status --short
git diff --cached --stat
# Revise os arquivos selecionados antes de criar o commit.
git commit -m "Prepare FGCL 0.3 library and scientific documentation"
git remote add origin https://github.com/adrianoucam/fgcl.git
git push -u origin main
```

Se Git pedir identidade, configure seu nome/e-mail de autoria conforme suas
preferências; não invente uma identidade. A autenticação do GitHub deve usar o
fluxo oficial de credenciais; não salve tokens em arquivos do projeto.

## Verificação após publicar

1. Abra a página do repositório e confira README, fórmulas e links relativos.
2. Confira a aba Actions e relate falhas reais antes de divulgar aprovação.
3. Faça instalação e execução a partir de um checkout limpo.
4. Escolha uma licença antes de anunciar permissões de uso e redistribuição.
5. Para versões futuras, use tags e changelog após validar o conteúdo.

O ZIP local em `dist` serve para transporte e não é enviado pelo `.gitignore`.
Não publique resultados locais contendo caminhos, dados ou modelos do usuário.
