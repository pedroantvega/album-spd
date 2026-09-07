# -*- coding: utf-8 -*-
"""
generar_album.py — Genera el álbum de SPD de un año en PDF y DOCX.

Uso por línea de comandos:
    python generar_album.py --csv catalogo.csv --imagenes carpeta_imgs/ --anio 1965 --salida salida/

También se puede usar la ventana gráfica:
    python app_gui.py
"""
import argparse
import os
import sys

from datos import cargar_anio
import pdf_builder
import docx_builder
import portada as portada_mod
import acontecimientos as acontecimientos_mod


def generar(csv_path, imagenes_dir, anio, salida_dir, lineas_resumen=1, escala_imagen=100,
            acontecimientos=None, log_fn=print):
    """Genera el PDF y el DOCX de un año. Devuelve un dict con el resumen."""
    os.makedirs(salida_dir, exist_ok=True)
    cache_dir = os.path.join(salida_dir, f'_cache_{anio}')

    log_fn(f'Cargando datos de {anio}...')
    grupos = cargar_anio(csv_path, anio, imagenes_dir, cache_dir=cache_dir)
    if not grupos:
        log_fn(f'No se encontraron SPD para el año {anio}. Revisa el CSV/carpeta.')
        return None
    log_fn(f'  {len(grupos)} sobres de primer día encontrados.')

    sin_imagen = [g for g in grupos if not g['imagen_ruta']]
    if sin_imagen:
        log_fn(f'  Aviso: {len(sin_imagen)} sobre(s) sin imagen encontrada en la carpeta:')
        for g in sin_imagen:
            log_fn(f'    - Edifil {g["edifil"]}: se esperaba {g["imagen_nombre"]}')

    miniaturas = [g for g in grupos if g['es_miniatura']]
    if miniaturas:
        log_fn(f'  Aviso: {len(miniaturas)} sobre(s) solo tienen miniatura de baja resolución (saldrán borrosos):')
        for g in miniaturas:
            log_fn(f'    - Edifil {g["edifil"]} ({g["imagen_nombre"]})')

    ruta_pdf = os.path.join(salida_dir, f'album_spd_{anio}.pdf')
    log_fn('Generando PDF...')
    info = pdf_builder.construir_pdf(anio, grupos, cache_dir, ruta_pdf, log_fn=log_fn,
                                      lineas_resumen=lineas_resumen, escala_imagen=escala_imagen)
    log_fn(f'  PDF generado: {ruta_pdf}  ({info["total_paginas"]} páginas: '
           f'{info["pequenos"]} pequeños, {info["grandes"]} grandes, {info["pages_desc"]} pág. descripciones)')

    ruta_docx = os.path.join(salida_dir, f'album_spd_{anio}.docx')
    log_fn('Generando DOCX...')
    docx_builder.construir_docx(anio, grupos, cache_dir, ruta_docx,
                                 lineas_resumen=lineas_resumen, escala_imagen=escala_imagen)
    log_fn(f'  DOCX generado: {ruta_docx}')

    log_fn('Listo.')
    info['ruta_pdf'] = ruta_pdf
    info['ruta_docx'] = ruta_docx
    info['sin_imagen'] = len(sin_imagen)
    info['miniaturas'] = len(miniaturas)

    # --- Portada/separador del año (archivo aparte, para imprimir en crema) ---
    datos_acontecimientos = acontecimientos if acontecimientos is not None else acontecimientos_mod.obtener(anio)
    if any(datos_acontecimientos.values()):
        if acontecimientos is not None:
            acontecimientos_mod.guardar(anio, acontecimientos)
        ruta_portada = os.path.join(salida_dir, f'portada_{anio}.pdf')
        log_fn('Generando portada del año...')
        portada_mod.construir_portada(anio, datos_acontecimientos, ruta_portada)
        log_fn(f'  Portada generada: {ruta_portada}')
        info['ruta_portada'] = ruta_portada
    else:
        log_fn(f'  Aviso: no hay acontecimientos para {anio} en acontecimientos.csv; no se genera portada.')

    return info


def main():
    ap = argparse.ArgumentParser(description='Genera el álbum de SPD de un año.')
    ap.add_argument('--csv', required=True, help='Ruta al CSV del catálogo (España)')
    ap.add_argument('--imagenes', required=True, help='Carpeta con las imágenes SPD de ese año')
    ap.add_argument('--anio', required=True, type=int)
    ap.add_argument('--salida', default='salida', help='Carpeta de salida')
    ap.add_argument('--lineas-resumen', type=int, default=1, choices=[1, 2],
                     help='Líneas del resumen corto bajo cada sobre (1 o 2)')
    ap.add_argument('--escala-imagen', type=int, default=100,
                     help='Escala de la imagen dentro de su recuadro, en %% (100 = ajuste normal)')
    args = ap.parse_args()

    info = generar(args.csv, args.imagenes, args.anio, args.salida,
                    lineas_resumen=args.lineas_resumen, escala_imagen=args.escala_imagen, log_fn=print)
    if info is None:
        sys.exit(1)


if __name__ == '__main__':
    main()
