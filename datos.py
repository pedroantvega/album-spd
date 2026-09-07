# -*- coding: utf-8 -*-
"""
datos.py — Carga y prepara los datos del catálogo para un año concreto.
"""
import os
import re
import pandas as pd
from PIL import Image

# --- Clasificación de tamaños -------------------------------------------------
# Basado en los ratios medidos sobre ejemplos reales:
#   P (pequeño)  ~1.55 - 1.68
#   M (mediano)  ~1.35 - 1.48   -> va en plantilla "no-pequeño"
#   G (grande)   ~1.25 - 1.35   -> va en plantilla "no-pequeño"
# Fuera de esos rangos = ambiguo -> se marca para revisión manual.

RATIO_P = (1.52, 1.95)   # sobres "normales" (varía algo según el escaneo/época)
RATIO_MG = (1.20, 1.50)  # M y G comparten plantilla "no pequeño"
# Nota: hay un pequeño solape teórico en 1.50-1.52; en la práctica los M/G
# tagueados en el nombre de archivo casi nunca caen ahí, así que el hueco es seguro.


def detectar_tamano_por_nombre(nombre_archivo):
    """Busca -P-, -M-, -G- (o variantes) en el nombre de archivo."""
    base = nombre_archivo.upper()
    if re.search(r'[-_](P)[-_]', base) or 'SPD-P-' in base:
        return 'P'
    if re.search(r'[-_](M)[-_]', base) or 'SPD-M-' in base:
        return 'MG'
    if re.search(r'[-_](G)[-_]', base) or 'SPD-G-' in base or 'GDE' in base:
        return 'MG'
    return None


def detectar_tamano_por_ratio(ratio):
    if RATIO_P[0] <= ratio <= RATIO_P[1]:
        return 'P'
    if RATIO_MG[0] <= ratio <= RATIO_MG[1]:
        return 'MG'
    return 'REVISAR'


def clasificar_tamano(nombre_archivo, ratio, fecha_iso=None, serie=None):
    # 1) Prioridad máxima: tabla de referencia de catálogos oficiales (dato real)
    if fecha_iso:
        import referencia_tamanos
        ref = referencia_tamanos.buscar(fecha_iso, serie)
        if ref:
            if ref['categoria'] == 'extra_grande':
                return 'EXTRA', f"catálogo oficial: {ref['ancho_mm']}x{ref['alto_mm']}mm", ref
            return 'MG', f"catálogo oficial: {ref['ancho_mm']}x{ref['alto_mm']}mm", ref
    # 2) Nombre de archivo (P/M/G)
    por_nombre = detectar_tamano_por_nombre(nombre_archivo)
    if por_nombre:
        return por_nombre, 'nombre de archivo', None
    # 3) Proporción de la foto (menos fiable)
    por_ratio = detectar_tamano_por_ratio(ratio)
    return por_ratio, f'proporción {ratio:.2f} (estimado)', None


MESES_ES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05',
    'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09',
    'octubre': '10', 'noviembre': '11', 'diciembre': '12',
}


def fecha_corta(fecha_texto):
    """'06 septiembre 1965' -> '06/09/1965'. Si no reconoce el formato, la deja igual."""
    if not isinstance(fecha_texto, str):
        return str(fecha_texto)
    partes = fecha_texto.strip().split()
    if len(partes) == 3 and partes[1].lower() in MESES_ES:
        dia = partes[0].zfill(2)
        mes = MESES_ES[partes[1].lower()]
        anio = partes[2]
        return f'{dia}/{mes}/{anio}'
    return fecha_texto


# Mojibake típico: bytes de Windows-1252 (0x80-0x9F) que quedaron como
# caracteres de control C1 sueltos en vez de convertirse a su símbolo real.
_CP1252_C1 = {
    0x85: '…', 0x91: '\u2018', 0x92: '\u2019', 0x93: '\u201C', 0x94: '\u201D',
    0x96: '-', 0x97: '-', 0x95: '•', 0x82: ',', 0x84: '"', 0x8B: '\u2039',
    0x9B: '\u203A', 0x88: '^', 0x99: '\u2122',
}


def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    return texto.translate(_CP1252_C1)


def resumen_en_lineas(descripcion, n_lineas=1, chars_por_linea=58):
    """Divide el arranque de la descripción en 1 o 2 líneas cortas,
    terminando siempre con la nota de "ver descripción completa"."""
    if not isinstance(descripcion, str) or not descripcion.strip():
        return []
    texto = descripcion.strip()
    primera_frase = re.split(r'(?<=[.:])\s', texto)[0].strip()
    max_total = chars_por_linea * n_lineas
    if len(primera_frase) > max_total:
        primera_frase = primera_frase[:max_total - 1].rsplit(' ', 1)[0] + '…'
    import textwrap
    lineas = textwrap.wrap(primera_frase, width=chars_por_linea) or ['']
    lineas = lineas[:n_lineas]
    lineas[-1] = lineas[-1] + '  (ver descripción completa al final del año)'
    return lineas


MESES_ISO = {v: k for k, v in MESES_ES.items()}


def fecha_a_iso(fecha_texto):
    """'14/01/1965' (ya convertida por fecha_corta) -> '1965-01-14'."""
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', fecha_texto or '')
    if not m:
        return None
    dia, mes, anio = m.groups()
    return f'{anio}-{mes}-{dia}'


def resumen_texto(descripcion, max_chars=260):
    """Arranque de la descripción + nota final, SIN partir en líneas
    (el ajuste a la caja se hace en el momento de dibujar, según el
    ancho real disponible)."""
    if not isinstance(descripcion, str) or not descripcion.strip():
        return ''
    texto = descripcion.strip()
    primera_frase = re.split(r'(?<=[.:])\s', texto)[0].strip()
    if len(primera_frase) > max_chars:
        primera_frase = primera_frase[:max_chars - 1].rsplit(' ', 1)[0] + '…'
    return primera_frase + '  (ver descripción completa al final del año)'


def resumen_una_linea(descripcion, max_chars=58):
    if not isinstance(descripcion, str) or not descripcion.strip():
        return ''
    texto = descripcion.strip()
    primera = re.split(r'(?<=[.:])\s', texto)[0].strip()
    if len(primera) > max_chars:
        primera = primera[:max_chars - 1].rsplit(' ', 1)[0] + '…'
    return primera + '  (ver descripción completa al final del año)'


def cargar_anio(csv_path, anio, carpeta_imagenes, cache_dir=None):
    """Devuelve una lista de dicts, uno por SPD, con todos los datos + tamaño."""
    df = pd.read_csv(csv_path)
    sub = df[(df['Anio de Emision'] == anio) & (df['Imagenes SPD relacionadas'].notna())].copy()

    grupos = []
    for img_name, filas in sub.groupby('Imagenes SPD relacionadas', sort=False):
        primera = filas.iloc[0]
        edifil = ','.join(str(x) for x in filas['Numeracion Edifil'])
        serie = limpiar_texto(primera['Serie'] if pd.notna(primera['Serie']) else primera['Motivo o Tema'])
        fecha = fecha_corta(primera['Fecha de Emision'])
        descripciones = [limpiar_texto(str(d)) for d in filas['Descripcion'].dropna().unique()]

        # localizar imagen real en disco (probar nombre exacto, y variantes de miniatura)
        ruta = os.path.join(carpeta_imagenes, img_name)
        ruta_mini = os.path.join(carpeta_imagenes, img_name.replace('.jpg', '-114x130.jpg'))
        if os.path.exists(ruta):
            ruta_final = ruta
            es_miniatura = False
        elif os.path.exists(ruta_mini):
            ruta_final = ruta_mini
            es_miniatura = True
        else:
            ruta_final = None
            es_miniatura = False

        ratio = None
        if ruta_final:
            try:
                if cache_dir:
                    import imagenes as imgmod
                    ruta_crop = imgmod.preparar_imagen(ruta_final, cache_dir)
                else:
                    ruta_crop = ruta_final
                with Image.open(ruta_crop) as im:
                    ratio = im.size[0] / im.size[1]
            except Exception:
                ratio = None

        fecha_iso = fecha_a_iso(fecha)
        if ratio is not None:
            tamano, motivo_tamano, ref = clasificar_tamano(img_name, ratio, fecha_iso, str(serie))
        elif fecha_iso:
            import referencia_tamanos
            ref = referencia_tamanos.buscar(fecha_iso, str(serie))
            if ref:
                tamano = 'EXTRA' if ref['categoria'] == 'extra_grande' else 'MG'
                motivo_tamano = f"catálogo oficial: {ref['ancho_mm']}x{ref['alto_mm']}mm (sin foto)"
            else:
                tamano, motivo_tamano, ref = 'DESCONOCIDO', 'sin imagen', None
        else:
            tamano, motivo_tamano, ref = 'DESCONOCIDO', 'sin imagen', None

        grupos.append({
            'edifil': edifil,
            'serie': str(serie),
            'fecha': str(fecha),
            'imagen_nombre': img_name,
            'imagen_ruta': ruta_final,
            'es_miniatura': es_miniatura,
            'tamano': tamano,
            'motivo_tamano': motivo_tamano,
            'tamano_real_mm': (ref['ancho_mm'], ref['alto_mm']) if ref else None,
            'descripciones': descripciones,
        })

    return grupos
