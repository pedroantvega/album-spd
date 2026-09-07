# -*- coding: utf-8 -*-
"""
imagenes.py — Recorta el fondo de relleno de las fotos de SPD y las deja
listas para maquetar (cacheadas en una carpeta temporal).
"""
import os
import numpy as np
from PIL import Image


def autocrop(ruta_entrada, ruta_salida, trim=3, umbral=45):
    im = Image.open(ruta_entrada).convert('RGB')
    arr = np.array(im).astype(int)
    bg = arr[0, 0]
    diff = np.abs(arr - bg).sum(axis=2)
    mask = diff > umbral
    ys, xs = np.where(mask)
    if len(xs) == 0:
        im.save(ruta_salida)
        return im.size
    x0, x1 = xs.min() + trim, xs.max() - trim
    y0, y1 = ys.min() + trim, ys.max() - trim
    if x1 <= x0 or y1 <= y0:
        im.save(ruta_salida)
        return im.size
    cropped = im.crop((x0, y0, x1, y1))
    cropped.save(ruta_salida, quality=92)
    return cropped.size


def preparar_imagen(ruta_original, carpeta_cache, rotar_90=False):
    """Recorta (si hace falta) y opcionalmente rota 90°. Devuelve ruta final."""
    os.makedirs(carpeta_cache, exist_ok=True)
    nombre = os.path.basename(ruta_original)
    ruta_crop = os.path.join(carpeta_cache, nombre)
    if not os.path.exists(ruta_crop):
        try:
            autocrop(ruta_original, ruta_crop)
        except Exception:
            Image.open(ruta_original).convert('RGB').save(ruta_crop)

    if rotar_90:
        nombre_rot = 'rot_' + nombre
        ruta_rot = os.path.join(carpeta_cache, nombre_rot)
        if not os.path.exists(ruta_rot):
            im = Image.open(ruta_crop)
            im.rotate(-90, expand=True).save(ruta_rot, quality=92)
        return ruta_rot

    return ruta_crop
