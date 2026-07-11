import pytest
import pandas as pd
import requests_mock
from src.bcc_api import (
    BancoCentralAPI,
    _resolve_codigo,
    _nombre_a_columna,
    _parse_series_obs,
    _build_retry_session,
    calcular_correlacion_rezago,
    calcular_hhi,
    estadisticas_por_ciclo,
)


@pytest.fixture(autouse=True)
def enable_logging():
    import logging
    logging.basicConfig(level=logging.INFO)
    yield


def test_resolve_codigo_uses_catalogo_series():
    assert _resolve_codigo('tpm_mensual') == 'F022.TPM.TIN.D001.NO.Z.M'
    assert _resolve_codigo('unknown_code') == 'unknown_code'


def test_nombre_a_columna_from_code_name():
    assert _nombre_a_columna('tpm_mensual') == 'tpm_mensual'
    assert _nombre_a_columna('F022.TPM.TIN.D001.NO.Z.M') == 'F022_TPM_TIN_D001_NO_Z_M'
    assert _nombre_a_columna('series_sin_punto') == 'series_sin_punto'


def test_parse_series_obs_filters_ok_records():
    obs = [
        ('01-01-2020', '1.23', 'OK'),
        ('02-01-2020', 'bad', 'OK'),
        ('03-01-2020', '4.56', 'ERR'),
    ]
    df = _parse_series_obs(obs)
    assert list(df.columns) == ['fecha', 'valor']
    assert len(df) == 1
    assert df.iloc[0]['valor'] == 1.23


def test_build_retry_session_returns_session():
    session = _build_retry_session()
    assert hasattr(session, 'get')


def test_request_uses_api_endpoint(requests_mock):
    api = BancoCentralAPI(usuario='x', password='y')
    requests_mock.get(api.BASE_URL, json={'Codigo': 0, 'Series': {'Obs': []}})

    data = api._request('F022.TPM.TIN.D001.NO.Z.M', '2020-01-01', '2020-02-01')

    assert data['Codigo'] == 0
    assert data['Series']['Obs'] == []


def test_calcular_correlacion_rezago_empty():
    serie_x = pd.Series([], dtype=float)
    serie_y = pd.Series([], dtype=float)
    df = calcular_correlacion_rezago(serie_x, serie_y)
    assert df.empty


def test_calcular_hhi_returns_zero_on_empty_series():
    series = pd.Series([])
    assert calcular_hhi(series) == 0.0


def test_estadisticas_por_ciclo_computes_summary():
    df = pd.DataFrame({
        'ciclo': ['a', 'a', 'b'],
        'valor': [1, 2, 3],
    })
    out = estadisticas_por_ciclo(df, 'valor', 'ciclo')
    assert out.loc['a', 'Promedio'] == 1.5
    assert out.loc['b', 'N'] == 1


def test_get_serie_returns_dataframe(monkeypatch):
    api = BancoCentralAPI(usuario='x', password='y')
    response = {
        'Codigo': 0,
        'Series': {
            'Obs': [
                ('01-01-2020', '1.0', 'OK'),
                ('01-02-2020', '2.0', 'OK'),
            ]
        }
    }

    monkeypatch.setattr(api, '_request', lambda codigo, fecha_ini, fecha_fin: response)
    df = api.get_serie('tpm_mensual', '2020-01-01', '2020-02-01', frecuencia='D')

    assert list(df.columns) == ['fecha', 'valor']
    assert df['valor'].tolist() == [1.0, 2.0]
    assert df['fecha'].dt.strftime('%Y-%m-%d').tolist() == ['2020-01-01', '2020-02-01']


def test_get_multiples_concats_series(monkeypatch):
    api = BancoCentralAPI(usuario='x', password='y')

    def fake_get_serie(nombre, fecha_ini, fecha_fin):
        return pd.DataFrame({
            'fecha': pd.to_datetime(['2020-01-01', '2020-02-01']),
            'valor': [1.0, 2.0],
        })

    monkeypatch.setattr(api, 'get_serie', fake_get_serie)
    df = api.get_multiples(['tpm_mensual', 'imacec_mensual'], '2020-01-01', '2020-02-01', pausa=0)

    assert 'tpm_mensual' in df.columns
    assert 'imacec_mensual' in df.columns
    assert df.shape == (2, 3)
