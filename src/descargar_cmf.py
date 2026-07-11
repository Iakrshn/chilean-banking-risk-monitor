"""
descargar_cmf.py
----------------
Script para descargar automáticamente todos los informes de morosidad
90 días del sistema bancario chileno desde la CMF.

Fuente: https://www.cmfchile.cl/portal/estadisticas/617/w3-propertyvalue-28914.html

Uso:
    python descargar_cmf.py

Los archivos se guardan en: data/raw/cmf_morosidad/
"""

import logging
import time
import requests
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


def _infer_cmf_fecha(texto_completo: str) -> tuple[str, str] | None:
    meses_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }

    texto_completo = texto_completo.lower()
    for nombre_mes, num_mes in meses_map.items():
        if nombre_mes in texto_completo:
            match_anio = re.search(r'20\d{2}', texto_completo)
            if match_anio:
                return match_anio.group(0), num_mes

    match_simple = re.search(r'(20\d{2})[/-](\d{2})', texto_completo)
    if match_simple:
        return match_simple.group(1), match_simple.group(2)

    return None


# ── Dependencias opcionales (para parsear HTML) ───────────────────────────────
try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False
    print('BeautifulSoup no instalado. Instálalo con: pip install beautifulsoup4')

# ── Configuración ─────────────────────────────────────────────────────────────
URL_CMF = 'https://www.cmfchile.cl/portal/estadisticas/617/w3-propertyvalue-28914.html'
BASE_URL = 'https://www.cmfchile.cl/'
DESTINO  = Path('data') / 'raw' / 'cmf_morosidad'
PAUSA    = 1.5   # segundos entre descargas (ser respetuoso con el servidor)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; investigacion-academica/1.0)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def obtener_links_cmf(url: str) -> list[dict]:
    """
    Hace scraping de la página CMF y extrae todos los links de descarga Excel.
    """
    print(f'Obteniendo lista de informes desde CMF...')
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    links = []
    # 1. Diccionario para meses
    meses_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }

    for a in soup.find_all('a', href=True):
        href = a['href']
        if '_recurso_1.xlsx' in href and 'articles-' in href:
            texto = a.get_text(strip=True)
            padre = a.find_parent('p') or a.find_parent('div') or a.find_parent('li')
            contexto = a.find_parent('tr') or padre 
            texto_completo = (contexto.get_text() if contexto else texto).lower()

            anio, mes = None, None

            for nombre_mes, num_mes in meses_map.items():
                if nombre_mes in texto_completo:
                    match_anio = re.search(r'20\d{2}', texto_completo)
                    if match_anio:
                        anio = match_anio.group(0)
                        mes = num_mes
                        break

            if not anio:
                match_simple = re.search(r'(20\d{2})[/-](\d{2})', texto_completo)
                if match_simple:
                    anio = match_simple.group(1)
                    mes = match_simple.group(2)

            if not anio or not mes:
                logger.warning('No se pudo inferir fecha para el link CMF: %s', texto_completo)
                continue

            url_completa = urljoin(BASE_URL, href)
            links.append({
                'nombre' : f'{anio}-{mes}',
                'url'    : url_completa,
                'anio'   : anio,
                'mes'    : mes,
            })
            # ------------------------------------

    # Eliminar duplicados por URL
    vistos = set()
    links_unicos = []
    for link in links:
        if link['url'] not in vistos:
            vistos.add(link['url'])
            links_unicos.append(link)

    print(f'Encontrados {len(links_unicos)} informes de morosidad')
    return links_unicos


def descargar_archivo(url: str, destino: Path, nombre: str) -> bool:
    """
    Descarga un archivo Excel desde la CMF.

    Retorna True si se descargó correctamente, False si ya existía o hubo error.
    """
    nombre_archivo = f'morosidad_{nombre}.xlsx'
    ruta_destino   = destino / nombre_archivo

    # Saltar si ya existe
    if ruta_destino.exists():
        print(f'Ya existe: {nombre_archivo}')
        return False

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()

        with open(ruta_destino, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        tamaño = ruta_destino.stat().st_size / 1024
        print(f' {nombre_archivo} ({tamaño:.0f} KB)')
        return True

    except Exception as e:
        print(f'Error en {nombre_archivo}: {e}')
        # Eliminar archivo parcial si quedó
        if ruta_destino.exists():
            ruta_destino.unlink()
        return False


def main():
    if not BS4_OK:
        print('\nInstala primero: pip install beautifulsoup4 requests')
        return

    # Crear directorio de destino
    DESTINO.mkdir(parents=True, exist_ok=True)
    print(f'Directorio de descarga: {DESTINO.resolve()}\n')

    # Obtener todos los links
    links = obtener_links_cmf(URL_CMF)

    if not links:
        print('No se encontraron links. Puede que el sitio CMF haya cambiado su estructura.')
        return

    # Ordenar cronológicamente
    links = sorted(links, key=lambda x: x['nombre'])

    # Descargar
    print(f'\nDescargando {len(links)} informes...\n')
    descargados = 0
    omitidos    = 0
    errores     = 0

    for i, link in enumerate(links, 1):
        print(f'[{i:>3}/{len(links)}]', end=' ')
        resultado = descargar_archivo(link['url'], DESTINO, link['nombre'])

        if resultado is True:
            descargados += 1
        elif resultado is False and (DESTINO / f"morosidad_{link['nombre']}.xlsx").exists():
            omitidos += 1
        else:
            errores += 1

        # Pausa para no sobrecargar el servidor de la CMF
        if resultado:
            time.sleep(PAUSA)

    # Resumen
    print('\n' + '═' * 55)
    print('  RESUMEN DE DESCARGA')
    print('═' * 55)
    print(f'Descargados nuevos : {descargados}')
    print(f'Ya existían        : {omitidos}')
    print(f'Errores            : {errores}')
    print(f'Total en carpeta     : {len(list(DESTINO.glob("*.xlsx")))} archivos')
    print(f'Ruta                 : {DESTINO.resolve()}')
    print('═' * 55)

    if descargados > 0 or omitidos > 0:
        print('\n Datos listos. Ahora puedes ejecutar el Notebook 01.')


if __name__ == '__main__':
    main()
