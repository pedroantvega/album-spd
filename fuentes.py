# -*- coding: utf-8 -*-
"""
fuentes.py — Registra DejaVu Sans (cobertura Unicode amplia: comillas
angulares, símbolos, tildes, etc.) para no perder caracteres en el PDF.

Las fuentes van incluidas dentro de la propia aplicación (carpeta
"fonts/", junto a este archivo), así que funciona igual en Windows,
Mac y Linux sin depender de lo que haya instalado en el sistema.
"""
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_AQUI = os.path.dirname(os.path.abspath(__file__))
_CANDIDATOS = [
    os.path.join(_AQUI, 'fonts'),                          # incluida con la app (preferida)
    '/usr/share/fonts/truetype/dejavu/',                    # Linux con DejaVu instalado
    'C:\\Windows\\Fonts\\',                                 # Windows (si algún día se usa Verdana, etc.)
]

FUENTE_NORMAL = 'DejaVuSans'
FUENTE_NEGRITA = 'DejaVuSans-Bold'
FUENTE_CURSIVA = 'DejaVuSans-Oblique'

_registrado = False


def _buscar(nombre_archivo):
    for carpeta in _CANDIDATOS:
        ruta = os.path.join(carpeta, nombre_archivo)
        if os.path.isfile(ruta):
            return ruta
    return None


def registrar():
    global _registrado, FUENTE_NORMAL, FUENTE_NEGRITA, FUENTE_CURSIVA
    if _registrado:
        return

    ruta_normal = _buscar('DejaVuSans.ttf')
    ruta_negrita = _buscar('DejaVuSans-Bold.ttf')
    ruta_cursiva = _buscar('DejaVuSans-Oblique.ttf')

    if ruta_normal and ruta_negrita and ruta_cursiva:
        pdfmetrics.registerFont(TTFont(FUENTE_NORMAL, ruta_normal))
        pdfmetrics.registerFont(TTFont(FUENTE_NEGRITA, ruta_negrita))
        pdfmetrics.registerFont(TTFont(FUENTE_CURSIVA, ruta_cursiva))
    else:
        # No se encontraron los archivos de fuente en ningún sitio conocido.
        # Seguimos funcionando con las fuentes estándar de reportlab en vez
        # de bloquear la aplicación, aunque algunos caracteres especiales
        # (comillas «», símbolos poco comunes) puedan no verse bien.
        print('Aviso: no se encontraron las fuentes DejaVu Sans (carpeta "fonts/" '
              'junto a la aplicación). Se usará Helvetica; tildes y ñ funcionan '
              'igual, pero algún símbolo raro podría no mostrarse.')
        FUENTE_NORMAL = 'Helvetica'
        FUENTE_NEGRITA = 'Helvetica-Bold'
        FUENTE_CURSIVA = 'Helvetica-Oblique'

    _registrado = True


registrar()
