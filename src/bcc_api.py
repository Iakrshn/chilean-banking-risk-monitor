"""
bcc_api.py
----------
Cliente Python para la API REST de la Base de Datos Estadísticos (BDE)
del Banco Central de Chile.

Documentación oficial: https://si3.bcentral.cl/Siete/ES/Siete/API

Registro gratuito en: https://si3.bcentral.cl/Siete/ES/Siete/API
"""

import logging
import os
import time
import requests
import pandas as pd
from datetime import datetime
from requests.adapters import HTTPAdapter
from typing import List, Optional
from urllib3.util.retry import Retry


# ── Catálogo de series más útiles para análisis de riesgo financiero ──────────

CATALOGO_SERIES = {
    # Política monetaria
    'tpm_mensual'        : 'F022.TPM.TIN.D001.NO.Z.M',
    'tpm_diaria'         : 'F022.TPM.TIN.D001.NO.Z.D',
    # Actividad económica
    'imacec_mensual'     : 'F032.IMC.IND.Z.Z.2018.Z.M',
    'pib_trimestral'     : 'F032.PIB.IND.Z.Z.2018.Z.Q',
    # Crédito bancario
    'colocaciones_total' : 'F022.COL.TOT.Z.Z.CLP.M',
    'colocaciones_com'   : 'F022.COL.COM.Z.Z.CLP.M',   # comerciales
    'colocaciones_cons'  : 'F022.COL.CON.Z.Z.CLP.M',   # consumo
    'colocaciones_viv'   : 'F022.COL.VIV.Z.Z.CLP.M',   # vivienda
    # Precios
    'ipc_mensual'        : 'F074.IPC.IND.Z.Z.Z.Z.M',
    # Tipo de cambio
    'usd_obs_diario'     : 'F073.TCO.PRE.Z.D',
    'usd_obs_mensual'    : 'F073.TCO.PRE.Z.M',
    # Tasas de mercado
    'tasa_captacion_90d' : 'F022.TAC.TAS.D090.NO.Z.M',
}

logger = logging.getLogger(__name__)


def _resolve_codigo(nombre_o_codigo: str) -> str:
    return CATALOGO_SERIES.get(nombre_o_codigo, nombre_o_codigo)


def _nombre_a_columna(nombre_o_codigo: str) -> str:
    if nombre_o_codigo in CATALOGO_SERIES:
        return nombre_o_codigo
    if '.' in nombre_o_codigo:
        return nombre_o_codigo.replace('.', '_')
    return nombre_o_codigo


def _parse_series_obs(obs: list) -> pd.DataFrame:
    df = pd.DataFrame(obs, columns=['fecha_str', 'valor', 'estado'])
    df = df[df['estado'] == 'OK'].copy()
    df['fecha'] = pd.to_datetime(df['fecha_str'], format='%d-%m-%Y')
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    return df[['fecha', 'valor']].dropna().reset_index(drop=True)


def _build_retry_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'],
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


__all__ = [
    'BancoCentralAPI',
    'CATALOGO_SERIES',
    'calcular_correlacion_rezago',
    'calcular_hhi',
    'estadisticas_por_ciclo',
]


class BancoCentralAPI:
    """
    Cliente para la API BDE del Banco Central de Chile.

    Uso:
    ----
    >>> api = BancoCentralAPI()  # lee BCC_USER y BCC_PASS desde .env
    >>> df_tpm = api.get_serie('tpm_mensual', '2015-01-01')
    >>> df_multi = api.get_multiples(['tpm_mensual', 'imacec_mensual'], '2015-01-01')
    """

    BASE_URL = 'https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx'

    def __init__(self, usuario: Optional[str] = None, password: Optional[str] = None):
        self.usuario  = usuario  or os.getenv('BCC_USER', '')
        self.password = password or os.getenv('BCC_PASS', '')
        if not self.usuario or not self.password:
            raise ValueError(
                'Credenciales BDE no encontradas.\n'
                'Regístrate en https://si3.bcentral.cl/Siete/ES/Siete/API\n'
                'Luego crea un archivo .env con:\n'
                '  BCC_USER=tu@email.com\n'
                '  BCC_PASS=tu_contraseña'
            )

        self.session = _build_retry_session()

    def _request(self, codigo: str, fecha_ini: str, fecha_fin: str) -> dict:
        """Ejecuta la llamada a la API y retorna el JSON."""
        params = {
            'user'       : self.usuario,
            'pass'       : self.password,
            'function'   : 'GetSeries',
            'timeseries' : codigo,
            'firstdate'  : fecha_ini,
            'lastdate'   : fecha_fin,
        }
        resp = self.session.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get('Codigo') != 0:
            raise ValueError(f"Error API BCC [{codigo}]: {data.get('Descripcion')}")
        return data

    def get_serie(
        self,
        nombre_o_codigo: str,
        fecha_ini: str = '2015-01-01',
        fecha_fin: Optional[str] = None,
        frecuencia: str = 'M',
    ) -> pd.DataFrame:
        """
        Descarga una serie estadística del BDE.

        Parámetros
        ----------
        nombre_o_codigo : nombre del catálogo (ej: 'tpm_mensual') o código BDE directo
        fecha_ini       : inicio del período 'YYYY-MM-DD'
        fecha_fin       : término del período (default: hoy)
        frecuencia      : 'D' diaria | 'M' mensual | 'Q' trimestral

        Retorna
        -------
        pd.DataFrame con columnas ['fecha', 'valor']
        """
        if fecha_fin is None:
            fecha_fin = datetime.today().strftime('%Y-%m-%d')

        # Resolver nombre → código BDE
        codigo = _resolve_codigo(nombre_o_codigo)

        data = self._request(codigo, fecha_ini, fecha_fin)
        obs  = data['Series']['Obs']
        df   = _parse_series_obs(obs)

        # Resamplear a frecuencia deseada
        freq_map = {'D': None, 'M': 'ME', 'Q': 'QE'}
        if freq_map.get(frecuencia):
            df = (df.set_index('fecha')
                    .resample(freq_map[frecuencia]).last()
                    .reset_index())

        return df

    def get_multiples(
        self,
        nombres: List[str],
        fecha_ini: str = '2015-01-01',
        fecha_fin: Optional[str] = None,
        pausa: float = 0.5,
    ) -> pd.DataFrame:
        """
        Descarga múltiples series y las integra en un DataFrame mensual.

        Parámetros
        ----------
        nombres   : lista de nombres del catálogo o códigos BDE
        fecha_ini : inicio del período
        fecha_fin : término del período
        pausa     : segundos entre llamadas (respetar rate limit)

        Retorna
        -------
        pd.DataFrame con una columna por serie, indexado por fecha
        """
        dfs = {}
        for nombre in nombres:
            col = _nombre_a_columna(nombre)
            logger.info('Descargando %s...', nombre)
            try:
                df_s = self.get_serie(nombre, fecha_ini, fecha_fin)
                df_s = df_s.rename(columns={'valor': col})
                dfs[col] = df_s.set_index('fecha')
                logger.info('Descargada %s (%d obs)', nombre, len(df_s))
            except Exception:
                logger.exception('Error descargando %s', nombre)
            time.sleep(pausa)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs.values(), axis=1).reset_index()

    def listar_series(self, frecuencia: str = 'MONTHLY') -> pd.DataFrame:
        """
        Lista todas las series disponibles en el BDE para una frecuencia dada.
        Frecuencias: 'DAILY', 'MONTHLY', 'QUARTERLY', 'ANNUAL'
        """
        params = {
            'user'      : self.usuario,
            'pass'      : self.password,
            'function'  : 'SearchSeries',
            'frequency' : frecuencia,
        }
        resp = self.session.get(self.BASE_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data.get('SeriesInfos', []))


# ── Funciones de utilidad estadística ────────────────────────────────────────

def calcular_correlacion_rezago(
    serie_x: pd.Series,
    serie_y: pd.Series,
    max_lag: int = 24,
) -> pd.DataFrame:
    """
    Calcula la correlación de Pearson entre serie_x (rezagada) y serie_y
    para rezagos de 0 a max_lag meses.

    Útil para cuantificar el mecanismo de transmisión de la TPM.

    Retorna
    -------
    pd.DataFrame con columnas ['lag', 'pearson_r', 'p_valor', 'significativa']
    """
    from scipy.stats import pearsonr

    resultados = []
    for lag in range(0, max_lag + 1):
        x_lag = serie_x.shift(lag)
        df_tmp = pd.DataFrame({'x': x_lag, 'y': serie_y}).dropna()
        if len(df_tmp) < 10:
            continue
        r, p = pearsonr(df_tmp['x'], df_tmp['y'])
        resultados.append({
            'lag'          : lag,
            'pearson_r'    : r,
            'p_valor'      : p,
            'significativa': p < 0.05,
        })

    df_res = pd.DataFrame(resultados)
    if df_res.empty:
        logger.warning('No hay suficientes datos para calcular correlación de rezago.')
        return df_res

    idx_opt = df_res['pearson_r'].abs().idxmax()
    logger.info('Rezago óptimo: %s meses (r = %.4f, p = %.4f)',
                df_res.loc[idx_opt, 'lag'],
                df_res.loc[idx_opt, 'pearson_r'],
                df_res.loc[idx_opt, 'p_valor'])
    return df_res


def calcular_hhi(serie: pd.Series) -> float:
    """
    Índice Herfindahl-Hirschman para medir concentración.
    HHI = Σ(cuota_i²) × 10.000
    Rango: 0 (completamente disperso) → 10.000 (monopolio)
    """
    total = serie.sum()
    if total == 0:
        return 0.0
    cuotas = serie / total
    return float((cuotas ** 2).sum() * 10_000)


def estadisticas_por_ciclo(
    df: pd.DataFrame,
    col_valor: str,
    col_ciclo: str = 'ciclo',
) -> pd.DataFrame:
    """
    Calcula estadísticas descriptivas de una variable por ciclo macroeconómico.
    """
    return (
        df.groupby(col_ciclo)[col_valor]
        .agg(['mean', 'median', 'std', 'min', 'max', 'count'])
        .round(3)
        .rename(columns={
            'mean'  : 'Promedio',
            'median': 'Mediana',
            'std'   : 'Desv. Est.',
            'min'   : 'Mínimo',
            'max'   : 'Máximo',
            'count' : 'N',
        })
    )
