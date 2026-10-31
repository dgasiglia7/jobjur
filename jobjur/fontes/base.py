"""Tipos e utilitários comuns aos coletores de vagas."""

import re
import time
import unicodedata
from dataclasses import asdict, dataclass, field

import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
PAUSA_SEGUNDOS = 1.5  # intervalo entre requisições ao mesmo site, para não sobrecarregá-lo

UFS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}


@dataclass
class Local:
    cidade: str
    uf: str

    @property
    def estado(self) -> str:
        return UFS.get(self.uf.upper(), self.uf)


@dataclass
class Vaga:
    fonte: str
    titulo: str
    url: str
    empresa: str = ""
    local: str = ""
    publicada: str = ""  # data ISO (AAAA-MM-DD) quando o site informa
    descricao: str = ""
    salario: str = ""
    modalidade: str = ""  # presencial, híbrido ou remoto, quando o site informa
    extras: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def slug(texto: str, sem_preposicoes: bool = False) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    palavras = re.findall(r"[a-z0-9]+", texto)
    if sem_preposicoes:
        palavras = [p for p in palavras if p not in {"de", "da", "do", "das", "dos"}]
    return "-".join(palavras)


def limpar(texto: str | None) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


class Cliente:
    """Cliente HTTP com cabeçalhos de navegador e pausa entre requisições."""

    def __init__(self, pausa: float = PAUSA_SEGUNDOS):
        self.pausa = pausa
        self._ultima = 0.0
        self._http = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"},
            follow_redirects=True,
            timeout=30,
        )

    def get(self, url: str, **params) -> str:
        espera = self._ultima + self.pausa - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        resposta = self._http.get(url, params=params or None)
        self._ultima = time.monotonic()
        resposta.raise_for_status()
        return resposta.text
