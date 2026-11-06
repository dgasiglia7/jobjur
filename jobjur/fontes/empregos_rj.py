"""Empregos RJ (empregosrj.com): blog de vagas do Rio de Janeiro."""

from . import wordpress
from .base import Cliente, Local, Vaga

NOME = "Empregos RJ"


def buscar(cliente: Cliente, termo: str, local: Local | None = None) -> list[Vaga]:
    if not local or local.uf.upper() != "RJ":
        return []  # só tem vagas do Rio
    return wordpress.buscar(cliente, "https://www.empregosrj.com", NOME, termo)
