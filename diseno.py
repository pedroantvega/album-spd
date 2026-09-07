# -*- coding: utf-8 -*-
"""
diseno.py — Constantes de maquetación compartidas.
"""
from reportlab.lib.units import mm

TITULO_ALBUM = 'Álbum de sobres de primer día de Pedro Antonio Vega Polo'

# Márgenes / marco
FRAME_MARGIN = 6 * mm       # separación del marco grueso al borde del papel
FRAME_WIDTH = 2.2           # grosor de línea del marco (puntos)
CONTENT_MARGIN = 12 * mm    # separación del contenido al marco
INDICE_MARGIN = 8 * mm      # el índice usa un margen más ajustado para ganar ancho de tabla

# Cabecera / pie
HEADER_H = 12 * mm
FOOTER_H = 8 * mm

# Caja "pequeño"
BOX_P_W = 170 * mm
BOX_P_H = 105 * mm
CAPTION_H_1L = 24 * mm   # pie con 1 línea de resumen
CAPTION_H_2L = 27 * mm   # pie con 2 líneas de resumen
GAP_ENTRIES = 3 * mm

# Escala de imagen dentro de su caja (100 = ajustada sin recortar;
# valores >100 la agrandan un poco, recortando lo que sobresalga)
ESCALA_IMAGEN_DEFECTO = 100

# Caja "mediano/grande" (rotada 90°, ocupa casi toda la página)
BOX_MG_LONG = 235 * mm   # a lo largo de la altura de página, tras rotar
BOX_MG_SHORT = 165 * mm  # a lo ancho de página, tras rotar

CORNER_MARK = 8 * mm
CORNER_COLOR = '#999999'

COLOR_TEXT = '#111111'
COLOR_TEXT_SOFT = '#444444'
COLOR_FRAME = '#000000'
