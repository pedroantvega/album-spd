# -*- coding: utf-8 -*-
"""
pdf_builder.py — Genera el PDF completo de un año del álbum.
"""
import math
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image

from diseno import *
from fuentes import FUENTE_NORMAL, FUENTE_NEGRITA, FUENTE_CURSIVA
import imagenes as imgmod

PAGE_W, PAGE_H = A4

style_desc_title = ParagraphStyle('DescTitle', fontName=FUENTE_NEGRITA, fontSize=9.5, leading=12,
                                   textColor=colors.HexColor(COLOR_TEXT), spaceAfter=1)
style_desc_body = ParagraphStyle('DescBody', fontName=FUENTE_NORMAL, fontSize=8.3, leading=10.6,
                                  textColor=colors.HexColor(COLOR_TEXT_SOFT), spaceAfter=6)
style_index_cell = ParagraphStyle('IdxCell', fontName=FUENTE_NORMAL, fontSize=8.3, leading=10)
style_index_serie = ParagraphStyle('IdxSerie', fontName=FUENTE_NEGRITA, fontSize=8.3, leading=10)
style_index_header = ParagraphStyle('IdxHead', fontName=FUENTE_NEGRITA, fontSize=8.5, textColor=colors.white)


# ---------------------------------------------------------------- marco / cabecera / pie
def draw_frame(c):
    c.setLineWidth(FRAME_WIDTH)
    c.setStrokeColor(colors.HexColor(COLOR_FRAME))
    c.rect(FRAME_MARGIN, FRAME_MARGIN, PAGE_W - 2 * FRAME_MARGIN, PAGE_H - 2 * FRAME_MARGIN)
    # línea fina interior, look "álbum clásico"
    inner = FRAME_MARGIN + 2.2 * mm
    c.setLineWidth(0.5)
    c.rect(inner, inner, PAGE_W - 2 * inner, PAGE_H - 2 * inner)


def draw_header(c):
    c.setFont(FUENTE_NEGRITA, 11)
    c.setFillColor(colors.HexColor(COLOR_TEXT))
    c.drawCentredString(PAGE_W / 2, PAGE_H - FRAME_MARGIN - 8 * mm, TITULO_ALBUM)
    y = PAGE_H - FRAME_MARGIN - 10.3 * mm
    c.setLineWidth(0.6)
    c.setStrokeColor(colors.HexColor('#bbbbbb'))
    c.line(FRAME_MARGIN + 8 * mm, y, PAGE_W - FRAME_MARGIN - 8 * mm, y)


def draw_footer(c, anio, pagina, total_paginas):
    c.setFont(FUENTE_NORMAL, 8.5)
    c.setFillColor(colors.HexColor(COLOR_TEXT_SOFT))
    texto = f'{anio}  —  Página {pagina} de {total_paginas}'
    c.drawCentredString(PAGE_W / 2, FRAME_MARGIN + 5 * mm, texto)


def nueva_pagina(c, anio, pagina, total_paginas):
    draw_frame(c)
    draw_header(c)
    draw_footer(c, anio, pagina, total_paginas)


# ---------------------------------------------------------------- entradas de sobres
def draw_corner_marks(c, x, y, w, h):
    c.setLineWidth(0.6)
    c.setStrokeColor(colors.HexColor(CORNER_COLOR))
    for (cx, cy) in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
        dx = CORNER_MARK if cx == x else -CORNER_MARK
        dy = CORNER_MARK if cy == y else -CORNER_MARK
        c.line(cx, cy, cx + dx, cy)
        c.line(cx, cy, cx, cy + dy)


def draw_imagen_en_caja(c, ruta, box_x, box_y, box_w, box_h, escala_pct=100):
    im = Image.open(ruta)
    iw, ih = im.size
    scale = min(box_w / iw, box_h / ih) * 0.98 * (escala_pct / 100.0)
    dw, dh = iw * scale, ih * scale
    dx = box_x + (box_w - dw) / 2
    dy = box_y + (box_h - dh) / 2
    c.saveState()
    p = c.beginPath()
    p.rect(box_x, box_y, box_w, box_h)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ruta, dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
    c.restoreState()


def envolver_texto(texto, fuente, tamano_fuente, ancho_max_pt):
    """Reparte 'texto' en líneas que llenan el ancho disponible de verdad
    (medido con la métrica real de la fuente), no por número de caracteres."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    palabras = texto.split()
    lineas = []
    actual = ''
    for palabra in palabras:
        candidato = (actual + ' ' + palabra).strip()
        if stringWidth(candidato, fuente, tamano_fuente) <= ancho_max_pt or not actual:
            actual = candidato
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def draw_caption(c, box_x, box_y, box_w, n, entry, n_lineas_resumen=1):
    c.setFont(FUENTE_NEGRITA, 9.5)
    c.setFillColor(colors.HexColor(COLOR_TEXT))
    c.drawString(box_x, box_y - 10, f"Nº {n}   Edifil {entry['edifil']}")
    c.setFont(FUENTE_NORMAL, 8.5)
    c.setFillColor(colors.HexColor(COLOR_TEXT_SOFT))
    c.drawString(box_x, box_y - 20, f"{entry['serie']}  —  {entry['fecha']}")

    texto = entry.get('resumen_texto') or ''
    if texto:
        tam_fuente = 7.6
        lineas = envolver_texto(texto, FUENTE_CURSIVA, tam_fuente, box_w)
        if len(lineas) > n_lineas_resumen:
            # Se pasa del hueco disponible: recorta con puntos suspensivos
            # en vez de partir la nota final a media palabra.
            lineas = lineas[:n_lineas_resumen]
            from reportlab.pdfbase.pdfmetrics import stringWidth
            while lineas and stringWidth(lineas[-1] + '…', FUENTE_CURSIVA, tam_fuente) > box_w:
                palabras = lineas[-1].split()
                if len(palabras) <= 1:
                    break
                lineas[-1] = ' '.join(palabras[:-1])
            lineas[-1] = lineas[-1].rstrip() + '…'

        c.setFont(FUENTE_CURSIVA, tam_fuente)
        c.setFillColor(colors.HexColor('#666666'))
        y = box_y - 29
        for linea in lineas:
            c.drawString(box_x, y, linea)
            y -= 3.6 * mm


def draw_pequeno_entry(c, top_y, n, entry, cache_dir, caption_h, escala_pct=100, lineas_resumen=1):
    box_x = (PAGE_W - BOX_P_W) / 2
    box_y = top_y - BOX_P_H
    draw_corner_marks(c, box_x, box_y, BOX_P_W, BOX_P_H)
    if entry['imagen_ruta']:
        ruta = imgmod.preparar_imagen(entry['imagen_ruta'], cache_dir)
        draw_imagen_en_caja(c, ruta, box_x, box_y, BOX_P_W, BOX_P_H, escala_pct=escala_pct)
    else:
        c.setFont(FUENTE_CURSIVA, 9)
        c.setFillColor(colors.HexColor('#aaaaaa'))
        c.drawCentredString(box_x + BOX_P_W / 2, box_y + BOX_P_H / 2, '(sin imagen disponible)')
    draw_caption(c, box_x, box_y, BOX_P_W, n, entry, n_lineas_resumen=lineas_resumen)
    return box_y - caption_h


def draw_grande_entry(c, n, entry, cache_dir, escala_pct=100):
    # Si conocemos el tamaño real (catálogo oficial), usamos esa medida
    # exacta para que las marcas de esquina coincidan con el sobre físico.
    if entry.get('tamano_real_mm'):
        ancho_real, alto_real = entry['tamano_real_mm']
    else:
        ancho_real, alto_real = BOX_MG_SHORT / mm, BOX_MG_LONG / mm
    box_w = ancho_real * mm
    box_h = alto_real * mm
    # el sobre se rota 90° para aprovechar el alto de la página
    box_x = (PAGE_W - box_h) / 2
    box_y = (PAGE_H - box_w) / 2 + 4 * mm
    draw_corner_marks(c, box_x, box_y, box_h, box_w)
    if entry['imagen_ruta']:
        ruta = imgmod.preparar_imagen(entry['imagen_ruta'], cache_dir, rotar_90=True)
        draw_imagen_en_caja(c, ruta, box_x, box_y, box_h, box_w, escala_pct=escala_pct)
    else:
        c.setFont(FUENTE_CURSIVA, 9)
        c.setFillColor(colors.HexColor('#aaaaaa'))
        c.drawCentredString(box_x + box_h / 2, box_y + box_w / 2, '(sin imagen disponible)')
    c.setFont(FUENTE_NEGRITA, 9.5)
    c.setFillColor(colors.HexColor(COLOR_TEXT))
    c.drawCentredString(PAGE_W / 2, box_y - 12,
                         f"Nº {n}   Edifil {entry['edifil']}  —  {ancho_real:.0f}×{alto_real:.0f}mm")
    c.setFont(FUENTE_NORMAL, 8.5)
    c.setFillColor(colors.HexColor(COLOR_TEXT_SOFT))
    c.drawCentredString(PAGE_W / 2, box_y - 22, f"{entry['serie']}  —  {entry['fecha']}")


def draw_extra_entry(c, n, entry):
    """Sobres 'extra grande' (p.ej. Pueblos con Encanto, 305x215mm o más):
    no intentamos maquetar la imagen, solo dejamos los datos en la página
    para que coloques el sobre real aparte."""
    ancho_real, alto_real = entry.get('tamano_real_mm') or (None, None)
    y = PAGE_H / 2 + 30 * mm
    c.setFont(FUENTE_NEGRITA, 16)
    c.setFillColor(colors.HexColor(COLOR_TEXT))
    c.drawCentredString(PAGE_W / 2, y, f"Nº {n}   Edifil {entry['edifil']}")
    y -= 10 * mm
    c.setFont(FUENTE_NORMAL, 12)
    c.setFillColor(colors.HexColor(COLOR_TEXT_SOFT))
    c.drawCentredString(PAGE_W / 2, y, f"{entry['serie']}")
    y -= 8 * mm
    c.drawCentredString(PAGE_W / 2, y, f"{entry['fecha']}")
    y -= 12 * mm
    if ancho_real:
        c.setFont(FUENTE_CURSIVA, 10)
        c.setFillColor(colors.HexColor('#777777'))
        c.drawCentredString(PAGE_W / 2, y, f"Sobre extra grande — {ancho_real:.0f}×{alto_real:.0f}mm")
        y -= 7 * mm
    c.drawCentredString(PAGE_W / 2, y, '(sin foto en esta página — sobre demasiado grande para la plantilla')
    y -= 5 * mm
    c.drawCentredString(PAGE_W / 2, y, 'estándar; colócalo aparte con estos datos como referencia)')


# ---------------------------------------------------------------- índice
def _construir_tabla_indice(anio, entradas_con_pagina, widths):
    from reportlab.platypus import Table, TableStyle

    header_style = ParagraphStyle('IdxHeadC', fontName=FUENTE_NEGRITA, fontSize=7.4,
                                   textColor=colors.white, leading=8.6)
    cell_style = ParagraphStyle('IdxCellC', fontName=FUENTE_NORMAL, fontSize=7.4, leading=8.8)
    cell_style_edifil_pequeno = ParagraphStyle('IdxCellEdifilSmall', fontName=FUENTE_NORMAL,
                                                fontSize=6.0, leading=7.2)
    cell_serie_style = ParagraphStyle('IdxCellSerieC', fontName=FUENTE_NEGRITA, fontSize=7.4, leading=8.8)

    encabezados = ['Nº', 'Edifil', 'Fecha', 'Serie / Emisión', 'Cant.', 'Valor<br/>Edifil', 'Total', 'Pág.', 'Tengo']
    datos_tabla = [[Paragraph(h, header_style) for h in encabezados]]
    for n, entry, pag in entradas_con_pagina:
        edifil_txt = str(entry['edifil'])
        cantidad = len(edifil_txt.split(','))
        # Si hay más de 3 números Edifil juntos, se reduce la letra de esa
        # celda para que quepan sin desbordar (en vez de partir en muchas líneas).
        estilo_edifil = cell_style_edifil_pequeno if cantidad >= 3 else cell_style
        datos_tabla.append([
            Paragraph(str(n), cell_style),
            Paragraph(edifil_txt, estilo_edifil),
            Paragraph(str(entry['fecha']), cell_style),
            Paragraph(str(entry['serie']), cell_serie_style),
            Paragraph(str(cantidad), cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(str(pag), cell_style),
            Paragraph('', cell_style),
        ])
    total_sellos = sum(len(str(e['edifil']).split(',')) for _, e, _ in entradas_con_pagina)
    datos_tabla.append([
        '', '', '', Paragraph('<b>Total del año</b>', cell_style),
        Paragraph(f'<b>{total_sellos}</b>', cell_style),
        '', Paragraph('', cell_style), '', '',
    ])

    tabla = Table(datos_tabla, colWidths=widths, repeatRows=1)
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -2), 'CENTER'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('ALIGN', (7, 0), (8, -2), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#cccccc')),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, colors.HexColor('#333333')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]
    prev_serie = None
    shade = False
    for idx in range(1, len(datos_tabla) - 1):
        serie_val = datos_tabla[idx][3].text
        if serie_val != prev_serie:
            shade = not shade
            prev_serie = serie_val
        if shade:
            estilo.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#f2f2f2')))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def planificar_indice(entradas_con_pagina, ancho_disponible, alto_primera, alto_siguientes):
    """Divide el índice en tantas 'páginas' (trozos de tabla) como haga
    falta para que ninguna se desborde, usando el partidor nativo de
    reportlab (Table.split), que respeta repeatRows automáticamente."""
    widths = [7*mm, 20*mm, 20*mm, ancho_disponible - (7+20+20+12+14+16+11+11)*mm, 12*mm, 14*mm, 16*mm, 11*mm, 11*mm]
    tabla = _construir_tabla_indice(None, entradas_con_pagina, widths)
    tw, th = tabla.wrap(ancho_disponible, alto_primera)
    if th <= alto_primera:
        return [tabla]
    piezas = tabla.split(ancho_disponible, alto_primera)
    if not piezas:
        # margen de seguridad: si ni una fila cabe, forzar al menos la tabla entera
        return [tabla]
    resultado = [piezas[0]]
    resto = piezas[1] if len(piezas) > 1 else None
    while resto is not None:
        tw, th = resto.wrap(ancho_disponible, alto_siguientes)
        if th <= alto_siguientes:
            resultado.append(resto)
            resto = None
        else:
            piezas = resto.split(ancho_disponible, alto_siguientes)
            if not piezas:
                resultado.append(resto)
                resto = None
            else:
                resultado.append(piezas[0])
                resto = piezas[1] if len(piezas) > 1 else None
    return resultado


def draw_indice_pagina(c, anio, tabla_pieza, es_primera, col_x, y_top, nota_final=None):
    if es_primera:
        c.setFont(FUENTE_NEGRITA, 26)
        c.setFillColor(colors.HexColor(COLOR_TEXT))
        c.drawCentredString(PAGE_W / 2, PAGE_H - FRAME_MARGIN - 22 * mm, str(anio))
        c.setFont(FUENTE_NORMAL, 11)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawCentredString(PAGE_W / 2, PAGE_H - FRAME_MARGIN - 28 * mm,
                             'Sobres de Primer Día — España — Índice del año')
    else:
        c.setFont(FUENTE_NEGRITA, 13)
        c.setFillColor(colors.HexColor(COLOR_TEXT))
        c.drawCentredString(PAGE_W / 2, PAGE_H - FRAME_MARGIN - HEADER_H - 8 * mm,
                             f'{anio} — Índice (continuación)')

    tw, th = tabla_pieza.wrap(0, 0)
    tabla_pieza.drawOn(c, col_x, y_top - th)

    if nota_final:
        p_nota = Paragraph(nota_final, ParagraphStyle('Nota', fontName=FUENTE_CURSIVA, fontSize=7.6,
                                                        textColor=colors.HexColor('#888888'), leading=9))
        ancho_nota = PAGE_W - 2 * (FRAME_MARGIN + INDICE_MARGIN)
        _, alto_nota = p_nota.wrap(ancho_nota, 30 * mm)
        p_nota.drawOn(c, col_x, FRAME_MARGIN + 8 * mm)


# ---------------------------------------------------------------- descripciones
def medir_bloque(edifil, serie, texto, ancho):
    p_title = Paragraph(f"Edifil {edifil} — {serie}", style_desc_title)
    p_body = Paragraph(texto.replace('\n', '<br/>'), style_desc_body)
    _, h1 = p_title.wrap(ancho, 1000 * mm)
    _, h2 = p_body.wrap(ancho, 1000 * mm)
    return p_title, p_body, h1 + h2


def planificar_descripciones(entradas, ancho):
    """Devuelve lista de páginas, cada una lista de (p_title, p_body)."""
    alto_disponible = (PAGE_H - 2 * FRAME_MARGIN - 2 * CONTENT_MARGIN - HEADER_H - FOOTER_H - 20 * mm)
    paginas = []
    pagina_actual = []
    alto_usado = 0
    for entry in entradas:
        for desc in entry['descripciones']:
            p_title, p_body, h = medir_bloque(entry['edifil'], entry['serie'], desc, ancho)
            if alto_usado + h > alto_disponible and pagina_actual:
                paginas.append(pagina_actual)
                pagina_actual = []
                alto_usado = 0
            pagina_actual.append((p_title, p_body, h))
            alto_usado += h
    if pagina_actual:
        paginas.append(pagina_actual)
    return paginas


def draw_pagina_descripciones(c, bloques, titulo_seccion=None):
    ancho = PAGE_W - 2 * (FRAME_MARGIN + CONTENT_MARGIN)
    x = FRAME_MARGIN + CONTENT_MARGIN
    y = PAGE_H - FRAME_MARGIN - HEADER_H - 14 * mm
    if titulo_seccion:
        c.setFont(FUENTE_NEGRITA, 13)
        c.setFillColor(colors.HexColor(COLOR_TEXT))
        c.drawString(x, y, titulo_seccion)
        y -= 9 * mm
    for p_title, p_body, h in bloques:
        p_title.drawOn(c, x, y - p_title.wrap(ancho, 1000 * mm)[1])
        y -= p_title.wrap(ancho, 1000 * mm)[1]
        p_body.drawOn(c, x, y - p_body.wrap(ancho, 1000 * mm)[1])
        y -= p_body.wrap(ancho, 1000 * mm)[1]


# ---------------------------------------------------------------- orquestador
def construir_pdf(anio, grupos, cache_dir, ruta_salida, log_fn=print, lineas_resumen=1, escala_imagen=100):
    from diseno import CAPTION_H_1L, CAPTION_H_2L
    caption_h = CAPTION_H_1L if lineas_resumen <= 1 else CAPTION_H_2L

    pequenos = [g for g in grupos if g['tamano'] == 'P']
    grandes = [g for g in grupos if g['tamano'] == 'MG']
    extra = [g for g in grupos if g['tamano'] == 'EXTRA']
    revisar = [g for g in grupos if g['tamano'] not in ('P', 'MG', 'EXTRA')]
    if revisar:
        log_fn(f'  Aviso: {len(revisar)} sobre(s) con tamaño ambiguo -> tratados como "pequeño" por defecto:')
        for g in revisar:
            log_fn(f'    - Edifil {g["edifil"]} ({g["imagen_nombre"]}): {g["motivo_tamano"]}')
        pequenos.extend(revisar)
    if extra:
        log_fn(f'  Aviso: {len(extra)} sobre(s) "extra grande" -> página solo con datos (sin imagen):')
        for g in extra:
            log_fn(f'    - Edifil {g["edifil"]}: {g["motivo_tamano"]}')

    for g in grupos:
        g['resumen_texto'] = ''
    for g in pequenos + grandes:
        if g['descripciones']:
            from datos import resumen_texto
            g['resumen_texto'] = resumen_texto(g['descripciones'][0])

    pages_pequenos = math.ceil(len(pequenos) / 2) if pequenos else 0
    pages_grandes = len(grandes)
    pages_extra = len(extra)

    ancho_desc = PAGE_W - 2 * (FRAME_MARGIN + CONTENT_MARGIN)
    todas_para_desc = [g for g in grupos if g['descripciones']]
    paginas_desc = planificar_descripciones(todas_para_desc, ancho_desc)
    pages_desc = len(paginas_desc)

    # el índice necesita saber en qué página física caerá cada sobre ANTES
    # de dibujarse, así que calculamos primero esas páginas (empezando
    # justo después de las que ocupe el propio índice, que a su vez
    # depende de cuántas filas quepan: lo resolvemos con una estimación
    # y, si hiciera falta más de 1 página de índice, se recoloca todo).
    ancho_indice = PAGE_W - 2 * (FRAME_MARGIN + INDICE_MARGIN)
    alto_primera_indice = (PAGE_H - FRAME_MARGIN - 36 * mm) - (FRAME_MARGIN + 16 * mm)
    alto_siguientes_indice = (PAGE_H - FRAME_MARGIN - HEADER_H - 14 * mm) - (FRAME_MARGIN + 16 * mm)

    def calcular_paginas_de(pages_indice):
        pagina_de = {}
        pag = 1 + pages_indice
        for i in range(0, len(pequenos), 2):
            for g in pequenos[i:i + 2]:
                pagina_de[id(g)] = pag
            pag += 1
        for g in grandes:
            pagina_de[id(g)] = pag
            pag += 1
        for g in extra:
            pagina_de[id(g)] = pag
            pag += 1
        return pagina_de

    # primera pasada asumiendo 2 páginas de índice (el hueco que reservamos
    # siempre, para que los sobres empiecen en la página 3 al imprimir a
    # doble cara — si el índice solo necesita 1, la página 2 queda en blanco)
    pagina_de = calcular_paginas_de(2)
    entradas_con_pagina = [(i + 1, g, pagina_de.get(id(g), '?')) for i, g in enumerate(grupos)]
    piezas_indice = planificar_indice(entradas_con_pagina, ancho_indice, alto_primera_indice, alto_siguientes_indice)

    pages_indice_reservadas = 2
    if len(piezas_indice) > 2:
        # el año tiene demasiados sobres para 2 páginas de índice a esta
        # letra: en vez de desbordar o encoger hasta ser ilegible, avisamos
        # y dejamos que el índice ocupe las páginas reales que necesite.
        log_fn(f'  Aviso: el índice de {anio} necesita {len(piezas_indice)} páginas '
               f'(más de las 2 previstas) porque el año tiene muchos sobres. '
               f'Los SPD empezarán después de esas páginas, no en la página 3.')
        pages_indice_reservadas = len(piezas_indice)
        pagina_de = calcular_paginas_de(pages_indice_reservadas)
        entradas_con_pagina = [(i + 1, g, pagina_de.get(id(g), '?')) for i, g in enumerate(grupos)]
        piezas_indice = planificar_indice(entradas_con_pagina, ancho_indice, alto_primera_indice, alto_siguientes_indice)

    total_paginas = pages_indice_reservadas + pages_pequenos + pages_grandes + pages_extra + pages_desc

    c = canvas.Canvas(ruta_salida, pagesize=A4)
    pagina_actual = 1

    # 1) índice (1 o 2 páginas reservadas; si el índice cabe en 1, la
    # segunda queda en blanco para que los sobres empiecen en la página 3)
    nota_indice = (f'Total sobres de primer día del año: {len(entradas_con_pagina)}. '
                   f'"Valor Edifil" y "Total" quedan en blanco para rellenar a mano '
                   f'(o desde tu propio catálogo cuando lo tengas centralizado).')
    for idx_pieza, pieza in enumerate(piezas_indice):
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        es_primera = (idx_pieza == 0)
        es_ultima = (idx_pieza == len(piezas_indice) - 1)
        y_top = (PAGE_H - FRAME_MARGIN - 36 * mm) if es_primera else (PAGE_H - FRAME_MARGIN - HEADER_H - 14 * mm)
        draw_indice_pagina(c, anio, pieza, es_primera, FRAME_MARGIN + INDICE_MARGIN, y_top,
                            nota_final=nota_indice if es_ultima else None)
        c.showPage()
        pagina_actual += 1
    if pages_indice_reservadas == 2 and len(piezas_indice) == 1:
        # página en blanco reservada (solo marco/cabecera/pie), para que
        # el primer sobre caiga siempre en la página 3
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        c.showPage()
        pagina_actual += 1

    # 2) pequeños, 2 por página
    numero_map = {id(g): i + 1 for i, g in enumerate(grupos)}
    for i in range(0, len(pequenos), 2):
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        y = PAGE_H - FRAME_MARGIN - HEADER_H - 5 * mm
        for g in pequenos[i:i + 2]:
            y = draw_pequeno_entry(c, y, numero_map[id(g)], g, cache_dir, caption_h,
                                    escala_pct=escala_imagen, lineas_resumen=lineas_resumen)
            y -= GAP_ENTRIES
        c.showPage()
        pagina_actual += 1

    # 3) medianos/grandes, 1 por página (tamaño real cuando se conoce)
    for g in grandes:
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        draw_grande_entry(c, numero_map[id(g)], g, cache_dir, escala_pct=escala_imagen)
        c.showPage()
        pagina_actual += 1

    # 4) extra grande, solo datos
    for g in extra:
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        draw_extra_entry(c, numero_map[id(g)], g)
        c.showPage()
        pagina_actual += 1

    # 5) descripciones
    for idx, bloques_pag in enumerate(paginas_desc):
        nueva_pagina(c, anio, pagina_actual, total_paginas)
        titulo = 'Descripciones completas' if idx == 0 else None
        draw_pagina_descripciones(c, bloques_pag, titulo_seccion=titulo)
        c.showPage()
        pagina_actual += 1

    c.save()
    return {
        'total_paginas': total_paginas,
        'pequenos': len(pequenos),
        'grandes': len(grandes),
        'extra': len(extra),
        'revisar': len(revisar),
        'pages_desc': pages_desc,
    }
