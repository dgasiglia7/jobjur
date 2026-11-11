"""Coletores de vagas, um módulo por site.

Testados em 2026-10-30. Trabalha Brasil não mostra descrição nem senioridade na listagem;
os detalhes ficam na página da vaga. Indeed, Glassdoor e Jusbrasil ficaram de fora porque bloqueiam acesso
automatizado (verificação anti-robô).

Acrescentados em 2026-11-06: Empregare, Talent.com (agregador) e RIOVAGAS (só vagas do Rio).
Testados e deixados de fora: Jooble, Careerjet, SimplyHired, Adzuna, Jobbol, WhatJobs e Netvagas
(verificação anti-robô); Sólides Vagas e emprego.net (a lista só carrega no navegador); Empregos RJ
(quase nenhuma vaga recente); Trampos (só comunicação e TI).

Acrescentada em 2026-11-07: páginas de carreira das maiores seguradoras (ver seguradoras.py).
Acrescentada em 2026-11-10: páginas de carreira de Asaas, Grupo Suno, iFood, QuintoAndar e CloudWalk (ver empresas.py).
Acrescentada em 2026-11-11: páginas de carreira das maiores empresas de tecnologia (ver tecnologia.py).
"""

from . import (bne, catho, empregare, empresas, empregos_com, gupy, infojobs, linkedin, riovagas, seguradoras,
               talent, tecnologia, trabalha_brasil, vagas_com)
from .base import Cliente, Local, Vaga

FONTES = {m.NOME: m for m in (gupy, linkedin, vagas_com, catho, infojobs, empregos_com, bne, trabalha_brasil,
                                 empregare, talent, riovagas, seguradoras, empresas, tecnologia)}

__all__ = ["FONTES", "Cliente", "Local", "Vaga"]
