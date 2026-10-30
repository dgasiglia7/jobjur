"""Coletores de vagas, um módulo por site.

Testados em 2026-10-30. Indeed, Glassdoor e Jusbrasil ficaram de fora porque bloqueiam acesso
automatizado (verificação anti-robô).
"""

from . import catho, gupy, infojobs, linkedin, vagas_com
from .base import Cliente, Local, Vaga

FONTES = {m.NOME: m for m in (gupy, linkedin, vagas_com, catho, infojobs)}

__all__ = ["FONTES", "Cliente", "Local", "Vaga"]
