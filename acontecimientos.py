# -*- coding: utf-8 -*-
"""
acontecimientos.py — Lee/escribe acontecimientos.csv: por año, 2 hitos
mundiales, 2 de España, y hasta 2 personales (editables).
"""
import csv
import os

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RUTA_CSV = os.path.join(_AQUI, 'acontecimientos.csv')

CAMPOS = ['anio', 'mundial_1', 'mundial_2', 'espana_1', 'espana_2',
          'fdc_destacado', 'imagen_fdc',
          'personal_1', 'personal_1_tipo', 'personal_2', 'personal_2_tipo',
          'imagen_1', 'imagen_2']


def obtener(anio):
    """Devuelve un dict con los 6 campos de texto para ese año (vacíos si no hay fila)."""
    vacio = {c: '' for c in CAMPOS if c != 'anio'}
    if not os.path.isfile(_RUTA_CSV):
        return vacio
    with open(_RUTA_CSV, encoding='utf-8') as f:
        for fila in csv.DictReader(f):
            fila.pop(None, None)
            if fila.get('anio') == str(anio):
                return {c: (fila.get(c) or '').strip() for c in CAMPOS if c != 'anio'}
    return vacio


def guardar(anio, valores):
    """valores: dict con las claves de CAMPOS (menos 'anio') a guardar para ese año."""
    filas = []
    encontrado = False
    if os.path.isfile(_RUTA_CSV):
        with open(_RUTA_CSV, encoding='utf-8') as f:
            lector = csv.DictReader(f)
            campos = lector.fieldnames or CAMPOS
            for fila in lector:
                fila.pop(None, None)
                if fila.get('anio') == str(anio):
                    for k, v in valores.items():
                        fila[k] = v
                    encontrado = True
                filas.append(fila)
    else:
        campos = CAMPOS

    if not encontrado:
        nueva = {c: '' for c in campos}
        nueva['anio'] = str(anio)
        nueva.update(valores)
        filas.append(nueva)
        filas.sort(key=lambda f: int(f['anio']) if str(f.get('anio', '')).isdigit() else 9999)

    with open(_RUTA_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
