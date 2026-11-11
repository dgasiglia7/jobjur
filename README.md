# jobjur

Agente que procura vagas de Direito nos principais sites de emprego do Brasil e ranqueia cada vaga pela compatibilidade com o currículo do candidato.

## Plano

1. **Ler o currículo** (PDF) e extrair o perfil profissional. ✅ `jobjur/perfil.py`
2. **Mapear as fontes** de vagas e testar quais permitem coleta automática. ✅ `jobjur/fontes/`
3. **Buscar e ranquear** diariamente, removendo vagas repetidas. ✅ `jobjur/buscar.py`
4. **Entregar** por uma página com upload do currículo e um resumo diário por e-mail.

## Uso

```bash
pip install -r requirements.txt
export JOBJUR_API_KEY=...   # ou ANTHROPIC_API_KEY, ou: ant auth login
python -m jobjur.perfil dados/curriculo.pdf dados/perfil.json
python -m jobjur.buscar dados/perfil.json
```

A busca gera `dados/vagas-AAAA-MM-DD-HHhMM.md`, (relatório com as vagas de nota 60 ou mais, com data e hora de Brasília no nome e no cabeçalho) e o `.json` com
todas as vagas jurídicas encontradas. Vagas que não apareceram em buscas anteriores ganham 🆕.

Opções úteis: `--termos "advogado,compliance"`, `--fontes "Gupy,LinkedIn"`, `--nota-minima 70` e
`--sem-claude` (usa só a nota por regras, sem chamar a API).

## Fontes

| Site | Situação | Observação |
|---|---|---|
| Gupy | ✅ coleta | Portal que reúne vagas de empresas e escritórios que usam a Gupy |
| LinkedIn | ✅ coleta | Listagem pública, sem login; só título, empresa, local e data |
| Vagas.com | ✅ coleta | Só a primeira página (cerca de 30 vagas por busca) |
| Catho | ✅ coleta | Título, empresa, cidade e salário |
| InfoJobs | ✅ coleta | Filtro de cidade nem sempre funciona; o ranking compensa |
| Empregos.com.br | ✅ coleta | Título, empresa, cidade, data e descrição |
| BNE | ✅ coleta | Sem data na listagem; às vezes recusa buscas seguidas (403) |
| Trabalha Brasil | ✅ coleta | Títulos genéricos ("Advogado"), sem descrição na listagem |
| Empregare | ✅ coleta | Portal e ATS de várias empresas; busca no Brasil todo (o site não filtra cidade) |
| Talent.com | ✅ coleta | Agregador que reúne anúncios de outros sites e páginas de carreira; a data é a da última atualização |
| RIOVAGAS | ✅ coleta | Blog de vagas do Rio (lido pela API do WordPress, só anúncios dos últimos 30 dias); muitas vagas de nível inicial |
| Seguradoras | ✅ coleta | Páginas de carreira de Tokio Marine, Porto, Grupo MAG, Caixa Vida e Previdência, Brasilprev, Brasilseg, Itaú, Zurich, Prudential e Icatu; só vagas da área jurídica. Bradesco, Mapfre, IRB, Allianz, SulAmérica, Sompo e AXA não puderam ser lidas |
| Empresas | ✅ coleta | Páginas de carreira de Asaas e Grupo Suno (Gupy), de iFood e QuintoAndar (Greenhouse) e da CloudWalk (página própria); só vagas da área jurídica. A Revolut não pôde ser lida (verificação anti-robô); as vagas dela costumam aparecer no LinkedIn |
| Tecnologia | ✅ coleta | Páginas de carreira de Amazon, Microsoft, Google, IBM, Oracle, Salesforce, Dell, Nubank, PicPay, Stone, PagBank, VTEX, EBANX, Globo, Creditas, Grupo Positivo e Wildlife Studios; só vagas da área jurídica no Brasil. Mercado Livre, Meta, Uber, Apple, SAP, TOTVS e Magazine Luiza não puderam ser lidas |
| Telecom | ✅ coleta | Páginas de carreira de Vivo, Claro, TIM, V.tal, Algar Telecom, Brisanet, Giga+, Vero, Nio, Unifique, Sky, Nokia e American Tower; só vagas da área jurídica. Oi, Ericsson, Huawei, IHS Towers, Desktop e Ligga não puderam ser lidas |
| Indeed | ❌ bloqueado | Verificação anti-robô exige login; há conector oficial do Indeed para usar nas conversas com o Claude |
| Glassdoor | ❌ bloqueado | Responde 403 |
| Jusbrasil | ❌ sem vagas | A página de vagas agora leva para notícias |
| Jooble, Careerjet, SimplyHired, Adzuna, Jobbol, WhatJobs, Netvagas | ❌ bloqueado | Verificação anti-robô (testado em 06/11/2026) |
| Sólides Vagas, emprego.net | ❌ fora | A lista de vagas só carrega no navegador |


## Ranking

Cada vaga recebe uma nota de 0 a 100. A nota por regras considera área do Direito, senioridade,
localização (cidade do candidato ou remoto) e data de publicação, e descarta vagas que não são
jurídicas. Com `JOBJUR_API_KEY` definida (ou `ANTHROPIC_API_KEY`), as 75 melhores vagas são reavaliadas pelo Claude, que dá
a nota final e explica em uma frase o que combina e o que não combina.

## Testes

```bash
python -m pytest
```

A chave usa o nome `JOBJUR_API_KEY` para que o Claude Code, se rodar no mesmo ambiente, não a use no
lugar da assinatura.

A pasta `dados/` fica fora do git, para que currículos e perfis não sejam publicados.

## Painel online (GitHub Pages)

`docs/` é um site estático com o painel de vagas: cada vaga tem os botões Pendente, Currículo enviado, Cadastrada e Descartada, e um campo de anotações.

- `docs/vagas.json`: as vagas. A busca acrescenta as novas com nota a partir de 65 (`python -m jobjur.buscar ... --painel docs/vagas.json`) e nunca altera as que já estão lá. Vagas revisadas à mão têm `revisada: true`; as da busca automática aparecem com a etiqueta "automática".
- `docs/status.json`: o que ela marcou. Só o painel grava esse arquivo, pela API do GitHub, com um token fine-grained (Contents: Read and write, só no repositório jobjur) guardado no navegador. Sem token o painel abre só para leitura.
- `python -m jobjur.painel verificar`: abre cada vaga ainda pendente e marca `encerrada: true` em `docs/vagas.json` quando o site mostra que ela fechou ou foi congelada (status da Gupy, aviso de vaga encerrada, página removida). Se o site reabrir a vaga, ela volta para `encerrada: false` e para Pendente no painel. Na dúvida, não mexe. No painel ela aparece como "Encerrado", e a pessoa também pode marcar à mão.
- `.github/workflows/painel.yml`: busca todo dia às 07:00 de Brasília (ou pelo botão "Run workflow"), grava as vagas novas e publica o site.

Para ativar:
1. Settings > Pages > Source: **GitHub Actions**.
2. Settings > Secrets and variables > Actions > New repository secret `JOBJUR_PERFIL` com o conteúdo do `perfil.json`.
3. Actions > "Busca diária e painel" > Run workflow.
