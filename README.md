# jobjur

Agente que procura vagas de Direito nos principais sites de emprego do Brasil e ranqueia cada vaga pela compatibilidade com o currículo do candidato.

## Plano

1. **Ler o currículo** (PDF) e extrair o perfil profissional. ✅ `jobjur/perfil.py`
2. **Mapear as fontes** de vagas e testar quais permitem coleta automática.
3. **Buscar e ranquear** diariamente, removendo vagas repetidas.
4. **Entregar** por uma página com upload do currículo e um resumo diário por e-mail.

## Uso

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...   # ou: ant auth login
python -m jobjur.perfil dados/curriculo.pdf dados/perfil.json
```

A pasta `dados/` fica fora do git, para que currículos e perfis não sejam publicados.
