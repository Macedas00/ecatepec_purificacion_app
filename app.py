import streamlit as st
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
from io import BytesIO

# ----- PDF (opcional con reportlab) -----
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ----- CONFIG PÁGINA -----
st.set_page_config(
    page_title="Purificación de Agua | Ecatepec",
    page_icon="💧",
    layout="wide",
)

# Fondo con estilo visual moderno (CSS)
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #003366 0%, #001a33 100%);
    color: white;
}
[data-testid="stSidebar"] {
    background-color: #001a33;
}
.block-container {
    padding-top: 2rem;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ----- TÍTULO -----
st.markdown(
    "<h1 style='text-align:center; color:white;'>💧 Simulador de Purificación de Agua – Ecatepec</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h5 style='text-align:center; color:#cce6ff;'>Modelo interactivo basado en contaminantes del agua de Ecatepec, México.</h5>",
    unsafe_allow_html=True,
)
st.write("---")

# ----- ESTADO PARA HISTORIAL Y DATOS COMPARTIDOS -----
if "historial" not in st.session_state:
    st.session_state["historial"] = []
if "df_filtros" not in st.session_state:
    st.session_state["df_filtros"] = None
if "fig_filtros" not in st.session_state:
    st.session_state["fig_filtros"] = None
if "fig_radar" not in st.session_state:
    st.session_state["fig_radar"] = None
if "fig_before_after" not in st.session_state:
    st.session_state["fig_before_after"] = None
if "tds_info" not in st.session_state:
    st.session_state["tds_info"] = None

# ----- SIDEBAR / FORMULARIO -----
st.sidebar.header("📋 Formulario de Datos del Agua")
st.sidebar.write("Introduce valores aproximados del agua de tu hogar para analizar la purificación:")

ph = st.sidebar.slider("pH del agua", 4.0, 9.0, 7.0)
turbidez = st.sidebar.slider("Turbidez (NTU)", 0.1, 50.0, 10.0)
coliformes = st.sidebar.slider("Coliformes fecales (NMP/100ml)", 0, 2000, 500)
metales = st.sidebar.slider("Metales pesados (ppm)", 0.0, 2.0, 0.4)

# TU ENFOQUE: TDS
tds = st.sidebar.slider("Sólidos disueltos totales (TDS) (mg/L)", 50, 1500, 650)

olor = st.sidebar.selectbox("¿Olor desagradable?", ["No", "Sí"])

boton = st.sidebar.button("Iniciar Simulación")

# ----- CÁLCULOS BASE -----
# Normalización simple de parámetros para un índice global
score = (turbidez / 50 + coliformes / 2000 + metales / 2 + tds / 1000) / 4
nivel = max(0.0, min(score * 100, 100.0))  # Nivel general de contaminación (0-100)

# ----- TABS -----
tab_analisis, tab_sim, tab_filtros, tab_tds, tab_hist = st.tabs(
    ["🔎 Análisis inicial", "⚙️ Simulación", "🧪 Filtros y comparativa", "💠 Enfoque TDS", "📂 Historial y reportes"]
)
# ===========================
# TAB 1: ANÁLISIS INICIAL
# ===========================
with tab_analisis:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔬 Análisis inicial del agua")
        st.write("Estos son los valores ingresados:")
        st.write(f"- **pH:** {ph}")
        st.write(f"- **Turbidez:** {turbidez:.2f} NTU")
        st.write(f"- **Coliformes:** {coliformes} NMP/100ml")
        st.write(f"- **Metales:** {metales:.3f} ppm")
        st.write(f"- **TDS:** {tds} mg/L")
        st.write(f"- **Olor:** {olor}")

    with col2:
        st.subheader("🧪 Índice global de contaminación")
        st.metric("Nivel general de contaminación", f"{nivel:.1f} %")

        # Clasificación de TDS básica
        if tds <= 500:
            clase_tds = "Aceptable para consumo según NOM-127 (≤ 500 mg/L)."
            st.success(f"TDS actual: {tds} mg/L — {clase_tds}")
        elif tds <= 900:
            clase_tds = "Alta mineralización (posible sabor desagradable)."
            st.warning(f"TDS actual: {tds} mg/L — {clase_tds}")
        else:
            clase_tds = "No recomendable para consumo directo (> 900 mg/L)."
            st.error(f"TDS actual: {tds} mg/L — {clase_tds}")

    st.info(
        "Este análisis es una aproximación basada en los parámetros ingresados. "
        "Valores altos indican mayor riesgo para la salud."
    )

# ===========================
# TAB 2: SIMULACIÓN
# ===========================
with tab_sim:
    st.subheader("⚙️ Simulación del proceso de purificación")

    if boton:
        etapas = [
            ("Pre-filtración", 2, "Eliminando sólidos grandes y residuos visibles…"),
            ("Sedimentación", 3, "Separando partículas suspendidas…"),
            ("Adsorción nanotecnológica", 4, "Capturando metales pesados…"),
            ("Desinfección UV", 4, "Inactivando bacterias, virus y coliformes…"),
            ("Pulido final", 2, "Mejorando olor, color y sabor…"),
        ]

        progreso_total = st.progress(0)
        avance = 0

        for nombre, tiempo, mensaje in etapas:
            st.write(f"### 🔵 {nombre}")
            st.write(mensaje)

            for _ in range(tiempo):
                time.sleep(0.7)
                avance += (1 / sum(e[1] for e in etapas))
                progreso_total.progress(min(avance, 1.0))

            eficiencia_etapa = np.clip(np.random.normal(85, 10), 60, 99.9)
            st.success(f"✔ Etapa completada — Eficiencia {eficiencia_etapa:.1f}%")

        st.success("✅ Simulación completada.")
    else:
        st.info("Presiona **'Iniciar Simulación'** en la barra lateral para ejecutar el proceso paso a paso.")
# ===========================
# TAB 3: FILTROS Y COMPARATIVA
# ===========================
with tab_filtros:
    st.subheader("🧪 Comparativa de filtros utilizados en México")

    filtros = {
        "Carbón activado": 0.70,
        "Ósmosis inversa": 0.97,
        "Zeolita": 0.80,
        "Nano-fibras": 0.92,
        "Ultrafiltración": 0.88,
    }

    tabla = []
    for filtro, eficiencia in filtros.items():
        purificacion = eficiencia * (100 - nivel)
        tabla.append([filtro, eficiencia * 100, purificacion])

    df = pd.DataFrame(tabla, columns=["Filtro", "Eficiencia base (%)", "Purificación estimada (%)"])

    df_display = df.copy()
    df_display["Eficiencia base (%)"] = df_display["Eficiencia base (%)"].map(lambda x: f"{x:.1f} %")
    df_display["Purificación estimada (%)"] = df_display["Purificación estimada (%)"].map(lambda x: f"{x:.1f} %")

    st.dataframe(df_display, use_container_width=True)

    mejor = df.iloc[df["Purificación estimada (%)"].idxmax()]
    st.write("---")
    st.success(
        f"### ⭐ Filtro recomendado: **{mejor['Filtro']}**\n"
        f"Purificación aproximada para tu caso: **{mejor['Purificación estimada (%)']:.1f} %**"
    )

    # ----- CÁLCULO ANTES / DESPUÉS (incluye TDS) -----
    eficiencia_filtro = mejor["Eficiencia base (%)"] / 100

    turbidez_after = turbidez * (1 - eficiencia_filtro)
    coliformes_after = coliformes * (1 - eficiencia_filtro)
    metales_after = metales * (1 - eficiencia_filtro)
    tds_after = tds * (1 - eficiencia_filtro)

    st.session_state["tds_info"] = {
        "tds_before": tds,
        "tds_after": tds_after,
        "eficiencia_filtro": eficiencia_filtro * 100,
        "filtro": mejor["Filtro"],
    }

    # ----- GRÁFICA DE BARRAS (FILTROS) -----
    st.write("## 📈 Eficiencia y purificación estimada por filtro")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["Filtro"], df["Eficiencia base (%)"], alpha=0.7, label="Eficiencia base (%)")
    ax.bar(df["Filtro"], df["Purificación estimada (%)"], alpha=0.7, label="Purificación estimada (%)")
    ax.set_ylabel("Porcentaje (%)")
    ax.set_title("Comparativa de filtros utilizados en México")
    ax.legend()
    plt.xticks(rotation=15)
    st.pyplot(fig)

    # ----- RADAR CHART -----
    st.write("## 🧬 Perfil de contaminación del agua (Radar)")

    categorias = ["Turbidez", "Coliformes", "Metales", "TDS"]
    valores_before = [
        turbidez / 50,
        coliformes / 2000,
        metales / 2,
        tds / 1000,
    ]
    valores_before += valores_before[:1]

    angles = [n / float(len(categorias)) * 2 * pi for n in range(len(categorias))]
    angles += angles[:1]

    fig2 = plt.figure(figsize=(6, 6))
    ax2 = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], categorias, color="white")
    ax2.plot(angles, valores_before, linewidth=2)
    ax2.fill(angles, valores_before, alpha=0.3)
    st.pyplot(fig2)

    # ----- GRÁFICA ANTES vs DESPUÉS -----
    st.write("## 🔄 Comparativa de contaminantes antes y después del filtrado")

    labels = ["Turbidez (NTU)", "Coliformes (NMP/100ml)", "Metales (ppm)", "TDS (mg/L)"]
    before = [turbidez, coliformes, metales, tds]
    after = [turbidez_after, coliformes_after, metales_after, tds_after]

    x = np.arange(len(labels))
    width = 0.35

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.bar(x - width / 2, before, width, label="Antes", color="#d9534f")
    ax3.bar(x + width / 2, after, width, label="Después", color="#5cb85c")
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=15)
    ax3.set_ylabel("Concentración")
    ax3.set_title("Reducción de contaminantes tras el filtrado")
    ax3.legend()
    st.pyplot(fig3)

    # Guardar para el reporte
    st.session_state["df_filtros"] = df
    st.session_state["fig_filtros"] = fig
    st.session_state["fig_radar"] = fig2
    st.session_state["fig_before_after"] = fig3

    # ----- GUARDAR EN HISTORIAL (cuando haya simulación) -----
    if boton:
        st.session_state["historial"].append(
            {
                "pH": ph,
                "Turbidez_NTU": turbidez,
                "Coliformes_NMP_100ml": coliformes,
                "Metales_ppm": metales,
                "TDS_mgL": tds,
                "Olor": olor,
                "Nivel_contaminacion_%": nivel,
                "Filtro_recomendado": mejor["Filtro"],
                "Purificacion_recomendada_%": round(mejor["Purificación estimada (%)"], 1),
                "TDS_filtrado_mgL": round(tds_after, 2),
            }
        )

# ===========================
# TAB 4: ENFOQUE TDS
# ===========================
with tab_tds:
    st.subheader("💠 Enfoque especializado en TDS (Sólidos disueltos totales)")

    info_tds = st.session_state.get("tds_info", None)

    col_a, col_b = st.columns(2)

    with col_a:
        st.write("### 🔹 Situación actual del TDS")
        st.write(f"**TDS inicial:** {tds} mg/L")

        if tds <= 500:
            st.success("El TDS se encuentra dentro de los valores recomendados por la NOM-127 (≤ 500 mg/L).")
        elif tds <= 900:
            st.warning("El TDS supera el valor recomendado. Puede haber sabor salado/amarargo y sedimentos.")
        else:
            st.error("El TDS es muy elevado (> 900 mg/L). El agua no es recomendable para consumo directo.")

    with col_b:
        if info_tds is not None:
            tds_after_local = info_tds["tds_after"]
            reduccion = 100 * (1 - tds_after_local / tds) if tds > 0 else 0
            st.write("### 🔹 Efecto del filtro recomendado sobre el TDS")
            st.write(f"**Filtro recomendado:** {info_tds['filtro']}")
            st.metric("TDS después del filtrado (estimado)", f"{tds_after_local:.2f} mg/L")
            st.write(f"Reducción aproximada de TDS: **{reduccion:.1f}%**")
        else:
            st.info("Aún no se ha calculado un filtro recomendado. Ve primero a la pestaña **'Filtros y comparativa'**.")

    # Gráfica simple de TDS antes / después
    if info_tds is not None:
        st.write("---")
        st.write("### 📉 Gráfica de TDS antes y después del filtrado")
        fig_tds, ax_tds = plt.subplots(figsize=(6, 4))
        ax_tds.bar(["Antes", "Después"], [tds, info_tds["tds_after"]], color=["#d9534f", "#5cb85c"])
        ax_tds.set_ylabel("TDS (mg/L)")
        ax_tds.set_title("Cambio en TDS tras el filtrado")
        st.pyplot(fig_tds)

        # Opcional: guardar esta gráfica para usarla después si quieres
        st.session_state["fig_tds"] = fig_tds
# ===========================
# TAB 5: HISTORIAL Y REPORTES
# ===========================
with tab_hist:
    st.subheader("📂 Historial de simulaciones")

    if len(st.session_state["historial"]) == 0:
        st.info("Aún no hay simulaciones guardadas. Ejecuta una simulación y revisa la pestaña de 'Filtros y comparativa'.")
    else:
        df_hist = pd.DataFrame(st.session_state["historial"])
        st.dataframe(df_hist, use_container_width=True)

        # ----- DESCARGAR CSV -----
        csv_bytes = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar historial en CSV",
            data=csv_bytes,
            file_name="historial_purificacion_ecatepec.csv",
            mime="text/csv",
        )

        # ----- GENERAR PDF -----
        st.write("---")
        st.subheader("📄 Generar reporte PDF de la última simulación (con enfoque TDS)")

        if not REPORTLAB_AVAILABLE:
            st.warning(
                "Para generar el PDF instala la librería `reportlab` en tu entorno:\n\n"
                "`pip install reportlab`"
            )
        else:
            if (
                st.session_state["df_filtros"] is None
                or st.session_state["fig_filtros"] is None
                or st.session_state["fig_radar"] is None
                or st.session_state["fig_before_after"] is None
                or st.session_state["tds_info"] is None
            ):
                st.warning(
                    "Aún no hay datos completos para el reporte (filtros, gráficas y TDS). "
                    "Ve a la pestaña **'Filtros y comparativa'** primero."
                )
            else:
                ultima = df_hist.iloc[-1]
                df_filtros = st.session_state["df_filtros"]
                fig_filtros = st.session_state["fig_filtros"]
                fig_radar = st.session_state["fig_radar"]
                fig_before_after = st.session_state["fig_before_after"]
                info_tds = st.session_state["tds_info"]

                def fig_to_image_reader(fig_local):
                    buf = BytesIO()
                    fig_local.savefig(buf, format="png", dpi=120, bbox_inches="tight")
                    buf.seek(0)
                    return ImageReader(buf)

                def generar_pdf(
                    datos,
                    df_filtros_local,
                    fig_filtros_local,
                    fig_radar_local,
                    fig_before_after_local,
                    info_tds_local,
                ):
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    width, height = letter

                    # Título
                    c.setFillColor(colors.darkblue)
                    c.setFont("Helvetica-Bold", 18)
                    c.drawString(50, height - 50, "Reporte de Purificación de Agua – Ecatepec")
                    c.setFillColor(colors.black)

                    # 1. Datos del agua
                    y = height - 90
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, "1. Datos del agua")
                    y -= 20
                    c.setFont("Helvetica", 10)

                    lineas = [
                        f"pH: {datos['pH']}",
                        f"Turbidez (NTU): {datos['Turbidez_NTU']}",
                        f"Coliformes (NMP/100ml): {datos['Coliformes_NMP_100ml']}",
                        f"Metales (ppm): {datos['Metales_ppm']}",
                        f"TDS (mg/L): {datos['TDS_mgL']}",
                        f"Olor desagradable: {datos['Olor']}",
                        f"Nivel de contaminación: {datos['Nivel_contaminacion_%']:.1f} %",
                    ]
                    for linea in lineas:
                        c.drawString(60, y, linea)
                        y -= 14

                    # 2. Comparativa de filtros
                    y -= 10
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, "2. Comparativa de filtros utilizados en México")
                    y -= 20

                    c.setFont("Helvetica-Bold", 10)
                    c.setFillColor(colors.white)
                    c.setStrokeColor(colors.darkblue)
                    c.setLineWidth(0.5)

                    c.setFillColor(colors.darkblue)
                    c.rect(50, y - 15, 500, 18, fill=1, stroke=1)
                    c.setFillColor(colors.white)
                    c.drawString(55, y - 12, "Filtro")
                    c.drawString(220, y - 12, "Eficiencia base (%)")
                    c.drawString(390, y - 12, "Purificación estimada (%)")

                    y -= 25
                    c.setFont("Helvetica", 9)
                    c.setFillColor(colors.black)
                    for _, fila in df_filtros_local.iterrows():
                        if y < 120:
                            c.showPage()
                            width, height = letter
                            y = height - 80
                        c.drawString(55, y, str(fila["Filtro"]))
                        c.drawString(220, y, f"{fila['Eficiencia base (%)']:.1f}")
                        c.drawString(390, y, f"{fila['Purificación estimada (%)']:.1f}")
                        y -= 14

                    # 3. Gráficas generales
                    c.showPage()
                    width, height = letter

                    c.setFont("Helvetica-Bold", 12)
                    c.setFillColor(colors.darkblue)
                    c.drawString(50, height - 50, "3. Gráficas del proceso de purificación")
                    c.setFillColor(colors.black)

                    img_filtros = fig_to_image_reader(fig_filtros_local)
                    c.drawImage(img_filtros, 50, height - 360, width=500, height=250, preserveAspectRatio=True)

                    img_radar = fig_to_image_reader(fig_radar_local)
                    c.drawImage(img_radar, 150, 80, width=300, height=220, preserveAspectRatio=True)

                    # 4. Reducción de contaminantes + TDS
                    c.showPage()
                    width, height = letter
                    c.setFont("Helvetica-Bold", 12)
                    c.setFillColor(colors.darkblue)
                    c.drawString(50, height - 50, "4. Reducción de contaminantes antes y después del filtrado")
                    c.setFillColor(colors.black)

                    img_before_after = fig_to_image_reader(fig_before_after_local)
                    c.drawImage(img_before_after, 50, height - 380, width=500, height=260, preserveAspectRatio=True)

                    # 5. Análisis especializado de TDS
                    y = height - 420
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, "5. Análisis especializado de TDS")
                    y -= 20
                    c.setFont("Helvetica", 10)

                    tds_before = info_tds_local["tds_before"]
                    tds_after = info_tds_local["tds_after"]
                    reduccion = 100 * (1 - tds_after / tds_before) if tds_before > 0 else 0

                    lineas_tds = [
                        f"TDS inicial: {tds_before:.2f} mg/L",
                        f"TDS estimado después del filtrado: {tds_after:.2f} mg/L",
                        f"Reducción aproximada de TDS: {reduccion:.1f} %",
                        "",
                        "Interpretación:",
                    ]

                    if tds_before <= 500:
                        lineas_tds.append(
                            "- El agua ya cumple el valor guía de TDS de la NOM-127 (≤ 500 mg/L); el filtrado mejora aún más la calidad."
                        )
                    elif tds_before <= 900:
                        lineas_tds.append(
                            "- El TDS inicial indica alta mineralización; tras el filtrado se observa una mejora significativa."
                        )
                    else:
                        lineas_tds.append(
                            "- El TDS inicial es muy elevado; el filtrado reduce de forma importante la carga disuelta, "
                            "pero se recomienda un tratamiento adicional para cumplir completamente la norma."
                        )

                    for linea in lineas_tds:
                        c.drawString(60, y, linea)
                        y -= 16

                    # 6. Filtro recomendado
                    c.showPage()
                    width, height = letter
                    c.setFont("Helvetica-Bold", 12)
                    c.setFillColor(colors.darkblue)
                    c.drawString(50, height - 50, "6. Filtro recomendado")
                    c.setFillColor(colors.black)

                    c.setFont("Helvetica", 11)
                    y = height - 90
                    c.drawString(60, y, f"Filtro recomendado por la simulación: {datos['Filtro_recomendado']}")
                    y -= 20
                    c.drawString(60, y, f"Purificación estimada global: {datos['Purificacion_recomendada_%']:.1f} %")
                    y -= 20
                    c.drawString(60, y, f"TDS estimado después del filtrado: {datos['TDS_filtrado_mgL']:.2f} mg/L")

                    c.showPage()
                    c.save()
                    buffer.seek(0)
                    return buffer

                pdf_buffer = generar_pdf(
                    ultima,
                    df_filtros,
                    fig_filtros,
                    fig_radar,
                    fig_before_after,
                    info_tds,
                )

                st.download_button(
                    label="⬇️ Descargar reporte PDF con tablas, gráficas y enfoque TDS",
                    data=pdf_buffer,
                    file_name="reporte_purificacion_ecatepec_TDS.pdf",
                    mime="application/pdf",
                )
