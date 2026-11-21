from __future__ import annotations


class ErroDeColeta(Exception):
    pass


class FonteIndisponivel(ErroDeColeta):
    pass


class LimiteDeRequisicoesExcedido(ErroDeColeta):
    pass


class RespostaInvalida(ErroDeColeta):
    pass
