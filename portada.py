# -*- coding: utf-8 -*-
"""
portada.py — Genera la portada/separador de un año: año grande y grueso
(centrado), 2 acontecimientos mundiales + 2 de España en post-its de
colores, y dos sellos ladeados (con valor facial y un icono de tipo de
acontecimiento personal) con las fotos de Pedro.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

PAGE_W, PAGE_H = A4

_AQUI = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR = os.path.join(_AQUI, 'fonts_calig')

FUENTE_ANIO = 'PermanentMarker'
FUENTE_TEXTO = 'Kalam-Regular'
FUENTE_TEXTO_NEGRITA = 'Kalam-Bold'

IMG_PAREJA = os.path.join(_AQUI, 'imagen_pareja.png')
IMG_PEDRO = os.path.join(_AQUI, 'imagen_pedro.png')
CARPETA_IMAGENES_PORTADA = os.path.join(_AQUI, 'imagenes_portada')


def _resolver_imagen(nombre_archivo, ruta_defecto):
    """Si datos['imagen_N'] apunta a un archivo real dentro de
    imagenes_portada/, se usa esa; si no, la imagen fija de siempre."""
    if nombre_archivo:
        ruta = os.path.join(CARPETA_IMAGENES_PORTADA, nombre_archivo)
        if os.path.isfile(ruta):
            return ruta
    return ruta_defecto

TIPOS_PERSONALES = ['ninguno', 'boda', 'nacimiento', 'fallecimiento', 'viaje', 'compra']

_registrado = False


def _registrar_fuentes():
    global _registrado, FUENTE_ANIO, FUENTE_TEXTO, FUENTE_TEXTO_NEGRITA
    if _registrado:
        return
    try:
        pdfmetrics.registerFont(TTFont(FUENTE_ANIO, os.path.join(_FONT_DIR, 'PermanentMarker.ttf')))
        pdfmetrics.registerFont(TTFont(FUENTE_TEXTO, os.path.join(_FONT_DIR, 'Kalam-Regular.ttf')))
        pdfmetrics.registerFont(TTFont(FUENTE_TEXTO_NEGRITA, os.path.join(_FONT_DIR, 'Kalam-Bold.ttf')))
        _registrado = True
    except Exception as e:
        print(f'Aviso: no se pudieron cargar las fuentes caligráficas ({e}); '
              f'la portada usará una fuente estándar.')
        FUENTE_ANIO = 'Helvetica-Bold'
        FUENTE_TEXTO = 'Helvetica'
        FUENTE_TEXTO_NEGRITA = 'Helvetica-Bold'
        # No marcamos _registrado=True aquí a propósito: si el fallo fue porque
        # los archivos de fuente aún no estaban disponibles, el siguiente intento
        # (siguiente generación de portada) volverá a intentar cargarlos en vez
        # de quedarse bloqueado para siempre en la fuente de reserva.


COLOR_TEXTO = '#2b241c'
COLOR_TEXTO_SUAVE = '#3a3226'
COLOR_LINEA = '#a89f8c'
COLOR_SOMBRA = '#cbc6b9'

COLOR_POSTIT_MUNDO = '#bfe3f0'
COLOR_POSTIT_MUNDO_BORDE = '#5a9bb0'
COLOR_POSTIT_ESPANA = '#fbdf8f'
COLOR_POSTIT_ESPANA_BORDE = '#c98a2b'
COLOR_SELLO_FONDO = '#f6ecd9'


def _anio_centrado(c, texto, ancho_objetivo_pt, y_centro):
    """Año centrado de verdad (Permanent Marker es recta y ya gruesa,
    no hace falta truco de contorno)."""
    base_size = 300
    ancho_base = pdfmetrics.stringWidth(texto, FUENTE_ANIO, base_size)
    tam = base_size * ancho_objetivo_pt / ancho_base
    c.setFont(FUENTE_ANIO, tam)
    c.setFillColor(colors.HexColor(COLOR_TEXTO))
    c.drawCentredString(PAGE_W / 2, y_centro, texto)
    return tam


def _divisor(c, y):
    c.setStrokeColor(colors.HexColor(COLOR_LINEA))
    c.setLineWidth(1)
    c.line(50 * mm, y, PAGE_W / 2 - 10 * mm, y)
    c.circle(PAGE_W / 2, y, 2.5, stroke=1, fill=1)
    c.line(PAGE_W / 2 + 10 * mm, y, PAGE_W - 50 * mm, y)


# --------------------------------------------------------------- iconos
def _icono(c, cx, cy, r, tipo):
    color = colors.HexColor(COLOR_TEXTO)
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.1)
    if tipo == 'boda':
        c.circle(cx - r * 0.35, cy, r * 0.55, stroke=1, fill=0)
        c.circle(cx + r * 0.35, cy, r * 0.55, stroke=1, fill=0)
    elif tipo == 'nacimiento':
        # carita de bebé: cabeza + ojos + boca
        c.setLineWidth(1.2)
        c.circle(cx, cy, r * 0.75, stroke=1, fill=0)
        c.setLineWidth(0)
        c.circle(cx - r * 0.28, cy + r * 0.05, r * 0.09, stroke=0, fill=1)
        c.circle(cx + r * 0.28, cy + r * 0.05, r * 0.09, stroke=0, fill=1)
        c.setLineWidth(1.1)
        p = c.beginPath()
        p.moveTo(cx - r * 0.28, cy - r * 0.22)
        p.curveTo(cx - r * 0.1, cy - r * 0.42, cx + r * 0.1, cy - r * 0.42, cx + r * 0.28, cy - r * 0.22)
        c.drawPath(p, stroke=1, fill=0)
        p2 = c.beginPath()
        p2.moveTo(cx - r * 0.12, cy + r * 0.78)
        p2.curveTo(cx - r * 0.05, cy + r, cx + r * 0.05, cy + r, cx + r * 0.12, cy + r * 0.78)
        c.drawPath(p2, stroke=1, fill=0)
    elif tipo == 'fallecimiento':
        # lazo de luto
        c.setLineWidth(0)
        p = c.beginPath()
        p.moveTo(cx, cy + r)
        p.curveTo(cx - r * 0.55, cy + r * 0.75, cx - r * 0.55, cy + r * 0.15, cx - r * 0.15, cy)
        p.lineTo(cx - r * 0.9, cy - r)
        p.lineTo(cx - r * 0.45, cy - r * 0.78)
        p.lineTo(cx, cy - r * 0.1)
        p.lineTo(cx + r * 0.45, cy - r * 0.78)
        p.lineTo(cx + r * 0.9, cy - r)
        p.lineTo(cx + r * 0.15, cy)
        p.curveTo(cx + r * 0.55, cy + r * 0.15, cx + r * 0.55, cy + r * 0.75, cx, cy + r)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    elif tipo == 'viaje':
        p = c.beginPath()
        p.moveTo(cx - r, cy - r * 0.3)
        p.lineTo(cx + r, cy)
        p.lineTo(cx - r, cy + r * 0.3)
        p.lineTo(cx - r * 0.4, cy)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
    elif tipo == 'compra':
        # casita: tejado + cuerpo + puerta
        p = c.beginPath()
        p.moveTo(cx - r, cy - r * 0.15)
        p.lineTo(cx, cy + r)
        p.lineTo(cx + r, cy - r * 0.15)
        c.drawPath(p, stroke=1, fill=0)
        c.rect(cx - r * 0.7, cy - r, r * 1.4, r * 0.85, stroke=1, fill=0)
        c.rect(cx - r * 0.18, cy - r, r * 0.36, r * 0.5, stroke=0, fill=1)


def _perforado(c, x, y, w, h, paso=3.6 * mm, radio=1.15 * mm):
    """Simula los agujeros de perforación de un sello de verdad: pequeños
    círculos sin tinta (se ve el papel/cartulina) a lo largo del borde."""
    c.setFillColor(colors.white)
    n_h = max(2, round(w / paso))
    n_v = max(2, round(h / paso))
    for i in range(n_h + 1):
        px = x + i * (w / n_h)
        c.circle(px, y, radio, stroke=0, fill=1)
        c.circle(px, y + h, radio, stroke=0, fill=1)
    for j in range(n_v + 1):
        py = y + j * (h / n_v)
        c.circle(x, py, radio, stroke=0, fill=1)
        c.circle(x + w, py, radio, stroke=0, fill=1)


def _dibujar_sello(c, cx, cy, w, h, ruta_imagen, angulo, leyenda=None, tipo_personal=None, valor_facial='1'):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angulo)
    x, y = -w / 2, -h / 2

    c.setFillColor(colors.HexColor(COLOR_SOMBRA))
    c.roundRect(x + 1.8 * mm, y - 1.8 * mm, w, h, 3, stroke=0, fill=1)

    c.setFillColor(colors.HexColor(COLOR_SELLO_FONDO))
    c.setStrokeColor(colors.HexColor(COLOR_LINEA))
    c.setLineWidth(1.3)
    c.roundRect(x, y, w, h, 3, stroke=1, fill=1)
    _perforado(c, x, y, w, h)
    inset = 4.5
    c.setLineWidth(0.7)
    c.rect(x + inset, y + inset, w - 2 * inset, h - 2 * inset, stroke=1, fill=0)

    banda_leyenda = 11 * mm if leyenda else 0
    area_img_h = h - 2 * inset - banda_leyenda

    if ruta_imagen and os.path.exists(ruta_imagen):
        with Image.open(ruta_imagen) as im:
            iw, ih = im.size
        margen = 9
        cw = w - 2 * margen
        ch = area_img_h - margen
        escala = min(cw / iw, ch / ih)
        dw, dh = iw * escala, ih * escala
        dx = -dw / 2
        dy = y + inset + banda_leyenda + (area_img_h - margen - dh) / 2 + margen / 2
        c.drawImage(ruta_imagen, dx, dy, width=dw, height=dh,
                     preserveAspectRatio=True, mask='auto')

    # valor facial, arriba a la derecha, como en un sello real (centrado)
    # se dibuja DESPUÉS de la imagen para que quede siempre por delante
    x_centro_valor = x + w - inset - 3 - 12
    c.setFont(FUENTE_TEXTO_NEGRITA, 8)
    c.setFillColor(colors.HexColor(COLOR_TEXTO))
    c.drawCentredString(x_centro_valor, y + h - inset - 9, valor_facial)
    c.setFont(FUENTE_TEXTO, 5.2)
    c.drawCentredString(x_centro_valor, y + h - inset - 15, 'RECUERDO')

    if leyenda:
        icono_w = 9 * mm if (tipo_personal and tipo_personal != 'ninguno') else 0
        estilo = ParagraphStyle('Leyenda', fontName=FUENTE_TEXTO_NEGRITA, fontSize=8.3,
                                 leading=9.6, alignment=TA_CENTER, textColor=colors.HexColor(COLOR_TEXTO))
        p = Paragraph(leyenda, estilo)
        ancho_txt = w - 2 * inset - 4 - icono_w
        tw, th = p.wrap(ancho_txt, banda_leyenda)
        x_txt = x + inset + 2 + icono_w
        p.drawOn(c, x_txt + (ancho_txt - tw) / 2 if tw < ancho_txt else x_txt,
                 y + inset + (banda_leyenda - th) / 2)
        if icono_w:
            _icono(c, x + inset + icono_w / 2 + 1, y + inset + banda_leyenda / 2, 3.4 * mm, tipo_personal)

    c.restoreState()


def _postit(c, cx, cy, w, h, angulo, color_fondo, color_borde, titulo, items):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angulo)
    x, y = -w / 2, -h / 2

    c.setFillColor(colors.HexColor(COLOR_SOMBRA))
    c.rect(x + 1.8 * mm, y - 1.8 * mm, w, h, stroke=0, fill=1)

    c.setFillColor(colors.HexColor(color_fondo))
    c.setStrokeColor(colors.HexColor(color_borde))
    c.setLineWidth(1.2)
    c.rect(x, y, w, h, stroke=1, fill=1)

    estilo_t = ParagraphStyle('PostitTitulo', fontName=FUENTE_TEXTO_NEGRITA, fontSize=13,
                               leading=15, alignment=TA_LEFT, textColor=colors.HexColor(color_borde))
    estilo_i = ParagraphStyle('PostitItem', fontName=FUENTE_TEXTO, fontSize=9.8,
                               leading=12.6, alignment=TA_LEFT, textColor=colors.HexColor(COLOR_TEXTO_SUAVE),
                               leftIndent=9, bulletIndent=0)
    pad = 5.5 * mm
    yy = y + h - pad
    p = Paragraph(titulo, estilo_t)
    tw, th = p.wrap(w - 2 * pad, 20 * mm)
    p.drawOn(c, x + pad, yy - th)
    yy -= th + 3
    for it in items:
        if not it:
            continue
        pi = Paragraph(it, estilo_i, bulletText='•')
        tw, th = pi.wrap(w - 2 * pad, 40 * mm)
        pi.drawOn(c, x + pad, yy - th)
        yy -= th + 2
    c.restoreState()


def _matasellos(c, cx, cy, r, anio, angulo=-3, medio_largo_lineas=None):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angulo)
    color = colors.HexColor(COLOR_TEXTO)
    c.setStrokeColor(color)
    c.setLineWidth(1.1)
    c.circle(0, 0, r, stroke=1, fill=0)
    c.circle(0, 0, r - 3.2 * mm, stroke=1, fill=0)
    c.setLineWidth(0.7)
    import math
    for i in range(24):
        ang = math.pi * 2 * i / 24
        x1 = (r - 3.2 * mm) * math.cos(ang)
        y1 = (r - 3.2 * mm) * math.sin(ang)
        x2 = r * math.cos(ang)
        y2 = r * math.sin(ang)
        c.line(x1, y1, x2, y2)

    estilo_curvo = ParagraphStyle('Mata', fontName=FUENTE_TEXTO_NEGRITA, fontSize=8.2,
                                   leading=10, alignment=TA_CENTER, textColor=color)
    p = Paragraph('PRIMER DÍA DE CIRCULACIÓN', estilo_curvo)
    tw, th = p.wrap(2 * (r - 6 * mm), 12 * mm)
    p.drawOn(c, -tw / 2, 4 * mm)

    c.setFont(FUENTE_ANIO, r * 0.5)
    c.setFillColor(color)
    c.drawCentredString(0, -r * 0.42, str(anio))

    # líneas de cancelación: por debajo, lejos ya del texto de las notas
    largo = medio_largo_lineas or (r - 5 * mm)
    c.setLineWidth(1.3)
    c.line(-largo, -9 * mm, largo, -9 * mm)
    c.line(-largo, -13 * mm, largo, -13 * mm)
    c.restoreState()


def _sello_fdc(c, cx, cy, w, h, ruta_imagen):
    """Sello pequeño y sencillo (sin valor facial ni leyenda) para el
    FDC destacado del año."""
    x, y = cx - w / 2, cy - h / 2
    c.setFillColor(colors.HexColor(COLOR_SOMBRA))
    c.roundRect(x + 1.4 * mm, y - 1.4 * mm, w, h, 2.5, stroke=0, fill=1)
    c.setFillColor(colors.HexColor(COLOR_SELLO_FONDO))
    c.setStrokeColor(colors.HexColor(COLOR_LINEA))
    c.setLineWidth(1.1)
    c.roundRect(x, y, w, h, 2.5, stroke=1, fill=1)
    _perforado(c, x, y, w, h, paso=3.2 * mm, radio=0.95 * mm)
    inset = 3.5
    c.setLineWidth(0.6)
    c.rect(x + inset, y + inset, w - 2 * inset, h - 2 * inset, stroke=1, fill=0)
    if ruta_imagen and os.path.exists(ruta_imagen):
        with Image.open(ruta_imagen) as im:
            iw, ih = im.size
        margen = 6
        cw, ch = w - 2 * margen, h - 2 * margen
        escala = min(cw / iw, ch / ih)
        dw, dh = iw * escala, ih * escala
        c.drawImage(ruta_imagen, cx - dw / 2, cy - dh / 2, width=dw, height=dh,
                     preserveAspectRatio=True, mask='auto')


def _imagen_sobre_limpia(c, cx, cy_top, h_max, ruta_imagen):
    """Imagen del SPD destacado, limpia (sin marco de sello: es un
    sobre, no un sello) con una sombra suave. Devuelve el alto usado."""
    if not (ruta_imagen and os.path.exists(ruta_imagen)):
        return 0
    with Image.open(ruta_imagen) as im:
        iw, ih = im.size
    dh = h_max
    dw = dh * iw / ih
    dx = cx - dw / 2
    dy = cy_top - dh
    c.setFillColor(colors.HexColor(COLOR_SOMBRA))
    c.rect(dx + 1.6 * mm, dy - 1.6 * mm, dw, dh, stroke=0, fill=1)
    c.drawImage(ruta_imagen, dx, dy, width=dw, height=dh,
                preserveAspectRatio=True, mask='auto')
    c.setStrokeColor(colors.HexColor(COLOR_LINEA))
    c.setLineWidth(0.7)
    c.rect(dx, dy, dw, dh, stroke=1, fill=0)
    return dh


def construir_portada(anio, datos, ruta_salida):
    _registrar_fuentes()
    c = canvas.Canvas(ruta_salida, pagesize=A4)

    # --- Año, centrado, un poco más arriba ---
    ancho_objetivo = PAGE_W - 2 * 20 * mm
    y_anio = PAGE_H - 72 * mm
    _anio_centrado(c, str(anio), ancho_objetivo, y_anio)

    # --- Sobre de Primer Día destacado del año, justo debajo del año ---
    fdc_texto = datos.get('fdc_destacado')
    img_fdc = _resolver_imagen(datos.get('imagen_fdc'), None)
    y_cursor = y_anio - 14 * mm
    if fdc_texto:
        estilo_fdc_etq = ParagraphStyle('FdcEtq', fontName=FUENTE_TEXTO, fontSize=7,
                                         leading=8.4, alignment=TA_CENTER,
                                         textColor=colors.HexColor(COLOR_TEXTO_SUAVE))
        estilo_fdc_txt = ParagraphStyle('FdcTxt', fontName=FUENTE_TEXTO_NEGRITA, fontSize=9.5,
                                         leading=11.5, alignment=TA_CENTER,
                                         textColor=colors.HexColor(COLOR_TEXTO))
        ancho_txt_fdc = PAGE_W - 2 * 30 * mm
        p_etq = Paragraph('SOBRE DESTACADO DEL AÑO', estilo_fdc_etq)
        p_txt = Paragraph(fdc_texto, estilo_fdc_txt)
        tw_e, th_e = p_etq.wrap(ancho_txt_fdc, 10 * mm)
        tw_t, th_t = p_txt.wrap(ancho_txt_fdc, 20 * mm)
        p_etq.drawOn(c, (PAGE_W - tw_e) / 2 if tw_e < ancho_txt_fdc else (PAGE_W - ancho_txt_fdc) / 2,
                     y_cursor - th_e)
        p_txt.drawOn(c, (PAGE_W - ancho_txt_fdc) / 2, y_cursor - th_e - 2 - th_t)
        y_cursor -= th_e + 2 + th_t + 6 * mm

        alto_img = _imagen_sobre_limpia(c, PAGE_W / 2, y_cursor, 30 * mm, img_fdc)
        y_cursor -= alto_img + 10 * mm
    else:
        y_cursor -= 4 * mm

    y_div = y_cursor
    _divisor(c, y_div)
    y_tras_fdc = y_div - 15 * mm

    # --- Dos sellos ladeados (con las fotos de Pedro) ---
    h_sello = 42 * mm
    w_pareja = h_sello * 1.5
    w_pedro = h_sello * 0.68
    gap = 14 * mm
    total_w = w_pareja + w_pedro + gap
    x0 = (PAGE_W - total_w) / 2
    y_sellos_centro = y_tras_fdc - h_sello / 2

    tipo1 = datos.get('personal_1_tipo') or 'ninguno'
    tipo2 = datos.get('personal_2_tipo') or 'ninguno'
    img1 = _resolver_imagen(datos.get('imagen_1'), IMG_PAREJA)
    img2 = _resolver_imagen(datos.get('imagen_2'), IMG_PEDRO)

    _dibujar_sello(c, x0 + w_pareja / 2, y_sellos_centro, w_pareja, h_sello,
                    img1, -5, datos.get('personal_1') or None, tipo1, valor_facial='1')
    _dibujar_sello(c, x0 + w_pareja + gap + w_pedro / 2, y_sellos_centro, w_pedro, h_sello,
                    img2, 7, datos.get('personal_2') or None, tipo2, valor_facial='2')

    # --- Dos post-its: Mundo (azul) y España (dorado) ---
    y_postits_centro = y_sellos_centro - h_sello / 2 - 34 * mm
    w_postit = 78 * mm
    h_postit = 46 * mm
    gap_p = 18 * mm
    x0p = (PAGE_W - (2 * w_postit + gap_p)) / 2

    _postit(c, x0p + w_postit / 2, y_postits_centro, w_postit, h_postit, -3,
            COLOR_POSTIT_MUNDO, COLOR_POSTIT_MUNDO_BORDE, 'EN EL MUNDO',
            [datos.get('mundial_1'), datos.get('mundial_2')])
    _postit(c, x0p + w_postit + gap_p + w_postit / 2, y_postits_centro, w_postit, h_postit, 4,
            COLOR_POSTIT_ESPANA, COLOR_POSTIT_ESPANA_BORDE, 'EN ESPAÑA',
            [datos.get('espana_1'), datos.get('espana_2')])

    # --- Matasellos superpuesto, transparente, tocando las esquinas de las notas ---
    medio_ancho = (2 * w_postit + gap_p) / 2 - 4 * mm
    y_matasellos = y_postits_centro - h_postit * 0.62
    _matasellos(c, PAGE_W / 2, y_matasellos, 20 * mm, anio,
                angulo=-2, medio_largo_lineas=medio_ancho)

    c.save()
