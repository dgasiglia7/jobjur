"""Coletores de vagas, um módulo por site.

Testados em 2026-10-30. Trabalha Brasil não mostra descrição nem senioridade na listagem;
os detalhes ficam na página da vaga. Indeed, Glassdoor e Jusbrasil ficaram de fora porque bloqueiam acesso
automatizado (verificação anti-robô).
"""

from . import (bne, catho, empregare, empregos_com, empregos_rj, gupy, infojobs, linkedin, riovagas, talent,
               trabalha_brasil, vagas_com)
from .base import Cliente, Local, Vaga

FONTES = {m.NOME: m for m in (gupy, linkedin, vagas_com, catho, infojobs, empregos_com, bne, trabalha_brasil,
                                 empregare, talent, riovagas, empregos_rj)}

__all__ = ["FONTES", "Cliente", "Local", "Vaga"]
