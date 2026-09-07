# -*- coding: utf-8 -*-
"""
app_streamlit.py — Versión web (Streamlit) de la app de escritorio original.
Reutiliza generar_album.generar(), pdf_builder, docx_builder, portada, etc.
tal cual, sin tocar su lógica interna.

Ejecutar en local con:
    streamlit run app_streamlit.py

Desplegar gratis en:
    https://share.streamlit.io  (Streamlit Community Cloud)
"""
import os
import shutil
import tempfile

import streamlit as st

from generar_album import generar
import acontecimientos as acontecimientos_mod
import portada as portada_mod

st.set_page_config(page_title="Álbum de Sobres de Primer Día", page_icon="📮", layout="centered")

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA_IMAGENES_PORTADA = os.path.join(AQUI, "imagenes_portada")

st.title("📮 Álbum de Sobres de Primer Día")
st.caption("Rellena los datos y pulsa \"Generar álbum\".")

# ---------------------------------------------------------------------------
# 1. Archivos de entrada
# ---------------------------------------------------------------------------
st.header("1. Archivos de entrada")

csv_file = st.file_uploader("CSV del catálogo", type=["csv"])
imagenes_files = st.file_uploader(
    "Imágenes SPD del año (selecciona todas las de la carpeta)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

# ---------------------------------------------------------------------------
# 2. Año y acontecimientos (para la portada)
# ---------------------------------------------------------------------------
st.header("2. Año y acontecimientos (para la portada)")

anio = st.number_input("Año", min_value=1850, max_value=2030, value=1965, step=1)

# Autorrelleno desde acontecimientos.csv al cambiar de año
if "anio_cargado" not in st.session_state or st.session_state["anio_cargado"] != anio:
    datos_previos = acontecimientos_mod.obtener(int(anio))
    for campo, valor in datos_previos.items():
        st.session_state[f"campo_{campo}"] = valor
    st.session_state["anio_cargado"] = anio

col1, col2 = st.columns(2)
with col1:
    mundial_1 = st.text_input("Mundial 1", key="campo_mundial_1")
    espana_1 = st.text_input("España 1", key="campo_espana_1")
with col2:
    mundial_2 = st.text_input("Mundial 2", key="campo_mundial_2")
    espana_2 = st.text_input("España 2", key="campo_espana_2")

fdc_destacado = st.text_input("FDC destacado del año", key="campo_fdc_destacado")

st.subheader("Acontecimientos personales (opcional)")
TIPOS_PERSONALES = ["ninguno", "boda", "nacimiento", "fallecimiento", "viaje", "compra"]

col3, col4 = st.columns(2)
with col3:
    personal_1 = st.text_input("Personal 1 (sello pareja)", key="campo_personal_1")
    tipo_1 = st.selectbox(
        "Tipo personal 1",
        TIPOS_PERSONALES,
        index=TIPOS_PERSONALES.index(st.session_state.get("campo_personal_1_tipo") or "ninguno"),
        key="campo_personal_1_tipo",
    )
with col4:
    personal_2 = st.text_input("Personal 2 (sello individual)", key="campo_personal_2")
    tipo_2 = st.selectbox(
        "Tipo personal 2",
        TIPOS_PERSONALES,
        index=TIPOS_PERSONALES.index(st.session_state.get("campo_personal_2_tipo") or "ninguno"),
        key="campo_personal_2_tipo",
    )

st.caption(
    "Autorrellenados desde acontecimientos.csv — cámbialos si quieres. "
    "⚠️ En Streamlit Community Cloud estos cambios NO se guardan de forma permanente "
    "(el disco se reinicia con cada despliegue): trátalo como una edición puntual, "
    "no como almacenamiento definitivo."
)

st.subheader("Imágenes personalizadas de portada (opcional)")
img_fdc = st.file_uploader("Imagen del FDC destacado", type=["png", "jpg", "jpeg"], key="up_fdc")
img_1 = st.file_uploader("Imagen 1 (sello pareja)", type=["png", "jpg", "jpeg"], key="up_1")
img_2 = st.file_uploader("Imagen 2 (sello individual)", type=["png", "jpg", "jpeg"], key="up_2")

# ---------------------------------------------------------------------------
# 3. Opciones de maquetación
# ---------------------------------------------------------------------------
st.header("3. Opciones de maquetación")

lineas_resumen = st.radio("Líneas de resumen", [1, 2], horizontal=True)
escala_imagen = st.slider(
    "Escala de imagen (%)", min_value=90, max_value=115, value=100,
    help="100% = ajuste normal; súbelo un poco si quieres que la imagen llene más "
         "el recuadro, recortando ligeramente los bordes.",
)

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _guardar_imagen_portada(archivo_subido, prefijo, anio):
    """Copia una imagen subida a imagenes_portada/ con el nombre que espera portada.py."""
    if archivo_subido is None:
        return ""
    os.makedirs(CARPETA_IMAGENES_PORTADA, exist_ok=True)
    ext = os.path.splitext(archivo_subido.name)[1].lower() or ".png"
    nombre_destino = f"{prefijo}_{anio}{ext}"
    ruta_destino = os.path.join(CARPETA_IMAGENES_PORTADA, nombre_destino)
    with open(ruta_destino, "wb") as f:
        f.write(archivo_subido.getbuffer())
    return nombre_destino


def _recoger_acontecimientos(anio):
    nombre_fdc = _guardar_imagen_portada(img_fdc, "imagen_fdc", anio)
    nombre_1 = _guardar_imagen_portada(img_1, "imagen1", anio)
    nombre_2 = _guardar_imagen_portada(img_2, "imagen2", anio)
    return {
        "mundial_1": mundial_1.strip(),
        "mundial_2": mundial_2.strip(),
        "espana_1": espana_1.strip(),
        "espana_2": espana_2.strip(),
        "fdc_destacado": fdc_destacado.strip(),
        "personal_1": personal_1.strip(),
        "personal_1_tipo": tipo_1,
        "personal_2": personal_2.strip(),
        "personal_2_tipo": tipo_2,
        # Si no se sube nada nuevo, se conserva lo que ya hubiera guardado (autorrelleno)
        "imagen_fdc": nombre_fdc or st.session_state.get("campo_imagen_fdc", ""),
        "imagen_1": nombre_1 or st.session_state.get("campo_imagen_1", ""),
        "imagen_2": nombre_2 or st.session_state.get("campo_imagen_2", ""),
    }


def _preparar_directorio_imagenes(archivos_subidos):
    """Guarda las imágenes subidas en una carpeta temporal, tal como espera generar()."""
    carpeta = tempfile.mkdtemp(prefix="imagenes_")
    for archivo in archivos_subidos:
        ruta = os.path.join(carpeta, archivo.name)
        with open(ruta, "wb") as f:
            f.write(archivo.getbuffer())
    return carpeta


# ---------------------------------------------------------------------------
# 4. Botones de acción
# ---------------------------------------------------------------------------
st.header("4. Generar")

col_a, col_b = st.columns(2)
generar_album_btn = col_a.button("📘 Generar álbum completo", type="primary", use_container_width=True)
generar_portada_btn = col_b.button("🖼️ Generar solo portada", use_container_width=True)

log_placeholder = st.empty()
logs = []


def log_fn(texto):
    logs.append(texto)
    log_placeholder.code("\n".join(logs))


if generar_portada_btn:
    if not str(int(anio)).isdigit():
        st.error("Introduce un año válido.")
    else:
        with st.spinner("Generando portada..."):
            salida_dir = tempfile.mkdtemp(prefix="salida_")
            datos_acontecimientos = _recoger_acontecimientos(int(anio))
            acontecimientos_mod.guardar(int(anio), datos_acontecimientos)
            ruta_portada = os.path.join(salida_dir, f"portada_{int(anio)}.pdf")
            try:
                portada_mod.construir_portada(int(anio), datos_acontecimientos, ruta_portada)
                st.success("¡Portada generada!")
                with open(ruta_portada, "rb") as f:
                    st.download_button(
                        "⬇️ Descargar portada (PDF)", f, file_name=f"portada_{int(anio)}.pdf",
                        mime="application/pdf",
                    )
            except Exception as e:
                st.error(f"No se pudo generar la portada: {e}")

if generar_album_btn:
    if csv_file is None:
        st.error("Falta el CSV del catálogo.")
    elif not imagenes_files:
        st.error("Falta al menos una imagen SPD.")
    else:
        with st.spinner("Generando álbum... esto puede tardar un poco"):
            # Guardar el CSV subido en un archivo temporal
            csv_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            csv_tmp.write(csv_file.getbuffer())
            csv_tmp.close()

            imagenes_dir = _preparar_directorio_imagenes(imagenes_files)
            salida_dir = tempfile.mkdtemp(prefix="salida_")
            datos_acontecimientos = _recoger_acontecimientos(int(anio))

            try:
                info = generar(
                    csv_tmp.name,
                    imagenes_dir,
                    int(anio),
                    salida_dir,
                    lineas_resumen=lineas_resumen,
                    escala_imagen=escala_imagen,
                    acontecimientos=datos_acontecimientos,
                    log_fn=log_fn,
                )
            except Exception as e:
                info = None
                log_fn(f"ERROR: {e}")

            if info:
                st.success("¡Álbum generado!")
                c1, c2, c3 = st.columns(3)
                with open(info["ruta_pdf"], "rb") as f:
                    c1.download_button("⬇️ PDF", f, file_name=os.path.basename(info["ruta_pdf"]),
                                        mime="application/pdf")
                with open(info["ruta_docx"], "rb") as f:
                    c2.download_button(
                        "⬇️ DOCX", f, file_name=os.path.basename(info["ruta_docx"]),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                if info.get("ruta_portada"):
                    with open(info["ruta_portada"], "rb") as f:
                        c3.download_button("⬇️ Portada", f, file_name=os.path.basename(info["ruta_portada"]),
                                            mime="application/pdf")
            else:
                st.error("No se pudo generar el álbum. Revisa el registro de arriba.")

            # Limpieza de temporales de entrada (no de los de salida, que se sirven en descarga)
            shutil.rmtree(imagenes_dir, ignore_errors=True)
            os.unlink(csv_tmp.name)
