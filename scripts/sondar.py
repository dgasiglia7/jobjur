import logging, time
from jobjur.fontes import transporte
from jobjur.fontes.base import Cliente
logging.basicConfig(level=logging.WARNING)
t = time.time()
vagas = transporte.coletar(Cliente(pausa=0))
print("TOTAL", len(vagas), "em", round(time.time() - t), "s")
for v in vagas:
    print("VAGA", v.empresa, "|", v.titulo, "|", v.local, "|", v.url)
