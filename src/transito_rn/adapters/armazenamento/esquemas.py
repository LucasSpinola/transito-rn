from __future__ import annotations

import pyarrow as pa

TRAFEGO = pa.schema(
    [
        pa.field("segmento", pa.string(), nullable=False),
        pa.field("lote", pa.string(), nullable=True),
        pa.field("coletado_em", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("velocidade_atual_kmh", pa.float64(), nullable=False),
        pa.field("velocidade_livre_kmh", pa.float64(), nullable=False),
        pa.field("tempo_atual_s", pa.float64(), nullable=False),
        pa.field("tempo_livre_s", pa.float64(), nullable=False),
        pa.field("comprimento_m", pa.float64(), nullable=False),
        pa.field("confianca", pa.float64(), nullable=False),
        pa.field("via_fechada", pa.bool_(), nullable=False),
        pa.field("frc", pa.string(), nullable=True),
    ]
)

CLIMA = pa.schema(
    [
        pa.field("coletado_em", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("chuva_mm", pa.float64(), nullable=False),
        pa.field("temperatura_c", pa.float64(), nullable=False),
        pa.field("vento_kmh", pa.float64(), nullable=False),
    ]
)
