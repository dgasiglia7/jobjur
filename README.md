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

A busca gera `dados/vagas-AAAA-MM-DD.md` (relatório com as vagas de nota 60 ou mais) e o `.json` com
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
| Indeed | ❌ bloqueado | Verificação anti-robô exige login |
| Glassdoor | ❌ bloqueado | Responde 403 |
| Jusbrasil | ❌ bloqueado | Responde 403 |

Empregos.com.br, BNE e Trabalha Brasil também responderam e podem virar novas fontes.

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
