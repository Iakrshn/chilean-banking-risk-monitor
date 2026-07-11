import pytest
from src.descargar_cmf import _infer_cmf_fecha


def test_infer_cmf_fecha_from_month_name():
    texto = 'Informe morosidad marzo 2023 recurso 1.xlsx'
    assert _infer_cmf_fecha(texto) == ('2023', '03')


def test_infer_cmf_fecha_from_iso_string():
    texto = 'Archivo 2024-07 morosidad'
    assert _infer_cmf_fecha(texto) == ('2024', '07')


def test_infer_cmf_fecha_returns_none_when_missing():
    texto = 'Informe sin fecha visible'
    assert _infer_cmf_fecha(texto) is None
