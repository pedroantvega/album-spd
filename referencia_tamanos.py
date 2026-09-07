# -*- coding: utf-8 -*-
"""
referencia_tamanos.py — Consulta la tabla de tamaños reales de sobre
extraída de los catálogos oficiales FESOFI (2000-2025) y del catálogo
1975-1999 ("Medidas del sobre"/"Tamaño del sobre").

Si una fecha de emisión aparece en esta tabla, sabemos su tamaño real
con certeza (en vez de adivinar por el nombre de archivo o la proporción
de la foto). Si no aparece, se asume tamaño "normal" (la plantilla
pequeña de siempre).
"""
import csv
import os
import re

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RUTA_CSV = os.path.join(_AQUI, 'referencia_tamanos.csv')

_tabla = None  # dict: fecha_iso -> lista de entradas


def _cargar():
    global _tabla
    if _tabla is not None:
        return _tabla
    _tabla = {}
    if not os.path.isfile(_RUTA_CSV):
        return _tabla
    with open(_RUTA_CSV, encoding='utf-8') as f:
        for fila in csv.DictReader(f):
            _tabla.setdefault(fila['fecha_iso'], []).append(fila)
    return _tabla


def _normalizar(txt):
    return re.sub(r'[^a-z0-9]+', ' ', txt.lower()).strip()


def buscar(fecha_iso, serie_texto):
    """Devuelve dict {ancho_mm, alto_mm, categoria} si la fecha (y a ser
    posible la serie) están en la tabla de referencia; si no, None."""
    tabla = _cargar()
    candidatos = tabla.get(fecha_iso)
    if not candidatos:
        return None
    if len(candidatos) == 1:
        c = candidatos[0]
        return {'ancho_mm': int(c['ancho_mm']), 'alto_mm': int(c['alto_mm']), 'categoria': c['categoria']}
    # Varias entradas ese mismo día: afinar por coincidencia de texto en la serie.
    serie_norm = _normalizar(serie_texto or '')
    for c in candidatos:
        palabras_ref = _normalizar(c['serie']).split()
        if any(len(p) > 4 and p in serie_norm for p in palabras_ref):
            return {'ancho_mm': int(c['ancho_mm']), 'alto_mm': int(c['alto_mm']), 'categoria': c['categoria']}
    # Sin coincidencia clara: devolvemos la primera como mejor estimación,
    # pero marcada para que se pueda avisar si hace falta.
    c = candidatos[0]
    return {'ancho_mm': int(c['ancho_mm']), 'alto_mm': int(c['alto_mm']), 'categoria': c['categoria'], 'ambiguo': True}
