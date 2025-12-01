import streamlit as st
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
from io import BytesIO

import plotly.express as px
import plotly.graph_objects as go

# ----- PDF (opcional con reportlab) -----
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ----- Google Sheets (opcional) -----
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
def log_to_google_sheets(row_dict):
    """
    Envía una fila con resultados a una hoja de cálculo de Google Sheets.
    Requiere:
    - Haber creado un Service Account en Google Cloud.
    - Haber puesto el JSON del servicio en st.secrets["gcp_service_account"].
    - Haber creado una hoja llamada 'Historial_Purificacion_Ecatepec' y
      compartido con el correo del service account.
    """
    if not GSPREAD_AVAILABLE:
        return

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
        client = gspread.authorize(creds)

        sh = client.open("Historial_Purificacion_Ecatepec")
        ws = sh.sheet1

        # Aseguramos orden de columnas
        columnas = [
            "pH",
            "Turbidez_NTU",
            "Coliformes_NMP_100ml",
            "Metales_ppm",
            "TDS_mgL",
            "Olor",
            "Nivel_contaminacion_%",
            "Filtro_recomendado",
            "Purificacion_recomendada_%",
            "TDS_filtrado_mgL",
        ]
        fila = [row_dict.get(col, "") for col in columnas]
        ws.append_row(fila)
    except Exception:
        # No tiramos la app, solo ignoramos si falla
        pass

# Fondo con estilo visual moderno (CSS)
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, #004080 0%, #001428 40%, #000814 100%);
    color: white;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001a33 0%, #000814 100%);
}

.block-container {
    padding-top: 2rem;
}

/* Títulos con animación */
h1, h2, h3 {
    animation: fadeInDown 0.8s ease-out;
}

/* Tarjetas */
.report-card {
    background: rgba(0, 20, 40, 0.85);
    border-radius: 16px;
    padding: 18px 22px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
    border: 1px solid rgba(0, 120, 255, 0.15);
}

/* Botón grande landing */
.big-button button {
    font-size: 1.05rem !important;
    padding: 0.6rem 1.4rem !important;
    border-radius: 999px !important;
}

/* Animación fade */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
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
if "started" not in st.session_state:
    st.session_state["started"] = False

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

# ----- LANDING PAGE -----
if not st.session_state["started"]:
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.markdown(
            "<h1 style='font-size:2.4rem; margin-bottom:0;'>💧 IA para purificación de agua en Ecatepec</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#cce6ff; font-size:1.05rem;'>Simulador interactivo que estima la eficiencia de filtros y nanofiltros "
            "para mejorar la calidad del agua, con enfoque especial en sólidos disueltos totales (TDS).</p>",
            unsafe_allow_html=True,
        )
        st.markdown("#### 🎯 ¿Qué hace este prototipo?")
        st.markdown(
            """
            - Analiza parámetros clave: turbidez, coliformes, metales, TDS y olor.
            - Compara filtros convencionales y nanotecnológicos.
            - Estima la reducción de contaminantes antes y después del filtrado.
            - Genera un **reporte PDF profesional** con tablas, gráficas e interpretación.
            - Incluye un módulo específico para **TDS**, tu parte del proyecto.  
            """
        )

        st.markdown('<div class="big-button">', unsafe_allow_html=True)
        if st.button("🚀 Entrar al simulador"):
            st.session_state["started"] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen rápido")
        st.write("• Modelo pensado para el contexto de Ecatepec.")
        st.write("• Soporta gráficas interactivas y reportes exportables.")
        st.write("• Ideal para presentar en clase como prototipo funcional.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()  # No sigue al resto del código hasta que presionen el botón

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
    
    st.write("### 🧠 Interpretación experta de parámetros")

    # Interpretación de turbidez
    if turbidez < 1:
        st.success("✔ La turbidez es excelente. El agua está visualmente limpia y permite una desinfección UV altamente eficiente.")
    elif turbidez < 5:
        st.info("ℹ La turbidez es aceptable, pero puede interferir ligeramente con la desinfección UV si aumenta.")
    else:
        st.error("⚠️ La turbidez es alta. Refleja presencia de partículas suspendidas, arcillas o microorganismos. Se recomienda prefiltración inmediata.")
    
    # Interpretación coliformes
    if coliformes == 0:
        st.success("✔ No hay coliformes fecales. El agua no presenta contaminación biológica detectable.")
    elif coliformes < 200:
        st.warning("⚠️ Hay baja presencia de coliformes fecales. Requiere desinfección UV para garantizar potabilidad.")
    else:
        st.error("❌ Alto nivel de coliformes. El agua NO es apta para consumo sin un tratamiento intensivo (UV obligatorio).")
    
    # Interpretación metales
    if metales < 0.01:
        st.success("✔ Metales pesados dentro de los límites recomendados por la NOM-127.")
    elif metales < 0.05:
        st.warning("⚠️ Metales moderados. Es recomendable nanofiltración o adsorción nanotecnológica.")
    else:
        st.error("❌ Metales pesados elevados. El agua puede contener arsénico, plomo u otros contaminantes peligrosos.")
    
    # Interpretación TDS
    if tds < 300:
        st.success("✔ Excelente calidad mineral del agua (TDS bajo).")
    elif tds < 600:
        st.info("ℹ Buena calidad del agua. Puede tener sabores minerales leves.")
    elif tds < 900:
        st.warning("⚠️ TDS alto. El agua puede tener sabor salado o amargo. No es ideal para consumo frecuente.")
    else:
        st.error("❌ TDS muy alto. El agua NO es apta para consumo humano directo.")


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

    # ===== INTERPRETACIÓN DEL FILTRO RECOMENDADO =====
    st.write("### 🧠 ¿Por qué se recomienda este filtro?")
    
    filtro = mejor["Filtro"]
    
    if filtro == "Ósmosis inversa":
        st.write("""
        ✔ **La ósmosis inversa es el filtro más eficiente a nivel doméstico y municipal.**  
        - Elimina hasta **99% de partículas**, metales y TDS.
        - Es ideal cuando el agua tiene **altos niveles de salinidad, arsénico o metales pesados**.
        - En Ecatepec se recomienda debido a la **dureza, sedimentos y TDS elevado**.
        """)
    elif filtro == "Carbón activado":
        st.write("""
        ✔ **Excelente para absorber olores, cloro y compuestos orgánicos volátiles (COVs).**  
        - Ideal cuando el agua huele mal o tiene sabor desagradable.  
        - No reduce mucho metales ni TDS.
        """)
    elif filtro == "Zeolita":
        st.write("""
        ✔ **La zeolita es un material natural que atrapa metales pesados y amonio.**  
        - Útil para aguas con turbidez moderada y presencia de metales.
        - Eficiente en sistemas municipales por su baja saturación.
        """)
    elif filtro == "Nano-fibras":
        st.write("""
        ✔ **Las nanofibras eliminan bacterias, virus y partículas submicrométricas.**  
        - Muy utilizadas en investigación de potabilización.
        - Logran altos niveles de remoción biológica sin químicos.
        """)
    elif filtro == "Ultrafiltración":
        st.write("""
        ✔ **La ultrafiltración retiene microorganismos y sólidos suspendidos.**  
        - Ideal cuando hay **coliformes, turbidez y sedimentos**.
        - Suele combinarse con carbón activado o UV.
        """)
    
    st.info(f"📌 Este filtro se seleccionó porque obtuvo **{mejor['Purificación estimada (%)']:.1f}%** de purificación según tus parámetros.")

    
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

    # ===== ANÁLISIS DE RIESGO ANTES / DESPUÉS =====
    st.write("### ⚠️ Análisis de riesgo del agua antes y después del filtrado")
    
    # Normalizamos los contaminantes a un índice 0–100 para comparar riesgo
    def normalizar(valor, maximo):
        return min(100, (valor / maximo) * 100)
    
    riesgo_before = {
        "Turbidez": normalizar(turbidez, 50),
        "Coliformes": normalizar(coliformes, 2000),
        "Metales": normalizar(metales, 2),
        "TDS": normalizar(tds, 1000),
    }
    
    riesgo_after = {
        "Turbidez": normalizar(turbidez_after, 50),
        "Coliformes": normalizar(coliformes_after, 2000),
        "Metales": normalizar(metales_after, 2),
        "TDS": normalizar(tds_after, 1000),
    }
    
    # Índice global (promedio)
    riesgo_global_before = sum(riesgo_before.values()) / 4
    riesgo_global_after = sum(riesgo_after.values()) / 4
    
    st.metric(
        "📉 Reducción de riesgo total (%)",
        f"{(100 - riesgo_global_after):.1f}%"
    )
    
    # Interpretación automática
    st.write("### 🧠 Interpretación del riesgo")
    if riesgo_global_before >= 70:
        st.write("🔴 El agua **inicialmente era de muy alto riesgo** para uso doméstico.")
    elif riesgo_global_before >= 40:
        st.write("🟠 El agua tenía **riesgo moderado** debido a niveles elevados de contaminantes.")
    else:
        st.write("🟡 El agua tenía **riesgo bajo**, aunque no estaba completamente dentro de normas sanitarias.")
    
    if riesgo_global_after <= 20:
        st.success("🟢 Tras el filtrado, el agua muestra un **riesgo bajo**, adecuada para la mayoría de usos.")
    elif riesgo_global_after <= 40:
        st.info("🟡 Tras el filtrado, el agua quedó en un **rango aceptable**, aunque requiere monitoreo.")
    else:
        st.warning("🟠 A pesar del filtrado, el agua mantiene **riesgo considerable**. Se recomienda filtración adicional.")
    
    # ===== GRÁFICA DE PIE — Reducción porcentual =====
    st.write("### 🥧 Distribución del riesgo por contaminante")
    
    df_riesgo = pd.DataFrame({
        "Contaminante": list(riesgo_before.keys()),
        "Antes (%)": list(riesgo_before.values()),
        "Después (%)": list(riesgo_after.values())
    })
    
    fig_pie = px.pie(
        df_riesgo,
        names="Contaminante",
        values="Antes (%)",
        title="Riesgo relativo antes del filtrado",
    )
    fig_pie.update_layout(template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)
    
    fig_pie2 = px.pie(
        df_riesgo,
        names="Contaminante",
        values="Después (%)",
        title="Riesgo relativo después del filtrado",
    )
    fig_pie2.update_layout(template="plotly_dark")
    st.plotly_chart(fig_pie2, use_container_width=True)
    
    # Guardamos estas gráficas para el PDF
    st.session_state["fig_pie_before"] = fig_pie
    st.session_state["fig_pie_after"] = fig_pie2
    st.session_state["riesgo_before"] = riesgo_before
    st.session_state["riesgo_after"] = riesgo_after

    
    # ----- GRÁFICA DE BARRAS (FILTROS) - PLOTLY -----
    st.write("## 📈 Eficiencia y purificación estimada por filtro")
    
    df_plot = df.copy()
    fig = px.bar(
        df_plot,
        x="Filtro",
        y=["Eficiencia base (%)", "Purificación estimada (%)"],
        barmode="group",
        labels={"value": "Porcentaje (%)", "variable": "Métrica"},
        title="Comparativa de filtros utilizados en México",
    )
    fig.update_layout(template="plotly_dark", legend_title_text="Métrica")
    st.plotly_chart(fig, use_container_width=True)


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

    # ===== INTERPRETACIÓN AUTOMÁTICA DEL RADAR =====
    st.write("### 🧠 Interpretación del perfil de contaminación")
    
    interpretaciones = []
    
    # Turbidez
    if turbidez < 1:
        interpretaciones.append("✔ La turbidez es muy baja. El agua está visualmente clara.")
    elif turbidez < 5:
        interpretaciones.append("ℹ La turbidez es moderada y podría afectar ligeramente la desinfección UV.")
    else:
        interpretaciones.append("⚠️ Alta turbidez. Refleja partículas, sedimentos o microorganismos.")
    
    # Coliformes
    if coliformes == 0:
        interpretaciones.append("✔ No se detectan coliformes fecales.")
    elif coliformes < 200:
        interpretaciones.append("⚠️ Hay presencia leve de coliformes. Se recomienda desinfección UV.")
    else:
        interpretaciones.append("❌ Coliformes muy altos. El agua NO es potable sin tratamiento intensivo.")
    
    # Metales
    if metales < 0.01:
        interpretaciones.append("✔ Metales pesados dentro de límites seguros según NOM-127.")
    elif metales < 0.05:
        interpretaciones.append("⚠️ Metales moderados. Sugiere riesgo bajo pero requiere monitoreo.")
    else:
        interpretaciones.append("❌ Metales peligrosamente elevados. Podría incluir plomo o arsénico.")
    
    # TDS
    if tds < 300:
        interpretaciones.append("✔ TDS muy bajo. Agua con excelente calidad mineral.")
    elif tds < 600:
        interpretaciones.append("ℹ TDS moderado. Sabor mineral aceptable.")
    elif tds < 900:
        interpretaciones.append("⚠️ TDS elevado. Sabor salado o amargo probable.")
    else:
        interpretaciones.append("❌ TDS extremadamente alto. Agua NO apta para consumo.")
    
    # Mostrar interpretación
    for item in interpretaciones:
        st.write(item)

    
    # ----- GRÁFICA ANTES vs DESPUÉS -----
    st.write("## 🔄 Comparativa de contaminantes antes y después del filtrado")

    labels = ["Turbidez (NTU)", "Coliformes (NMP/100ml)", "Metales (ppm)", "TDS (mg/L)"]
    before = [turbidez, coliformes, metales, tds]
    after = [turbidez_after, coliformes_after, metales_after, tds_after]

    x = np.arange(len(labels))
    width = 0.35

    df_ba = pd.DataFrame(
        {
            "Parámetro": labels,
            "Antes": before,
            "Después": after,
        }
    )

    fig3 = px.bar(
        df_ba,
        x="Parámetro",
        y=["Antes", "Después"],
        barmode="group",
        title="Reducción de contaminantes tras el filtrado",
    )
    fig3.update_layout(template="plotly_dark", legend_title_text="Estado")
    st.plotly_chart(fig3, use_container_width=True)


    # Guardar para el reporte
    st.session_state["df_filtros"] = df
    st.session_state["fig_filtros"] = fig
    st.session_state["fig_radar"] = fig2
    st.session_state["fig_before_after"] = fig3

    # ----- GUARDAR EN HISTORIAL (cuando haya simulación) -----
    if boton:
        entry = {
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
    
        st.session_state["historial"].append(entry)
    
        # Si luego activas Google Sheets, con esto sube automáticamente
        try:
            log_to_google_sheets(entry)
        except:
            pass


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
        df_tds = pd.DataFrame(
            {"Estado": ["Antes", "Después"], "TDS (mg/L)": [tds, info_tds["tds_after"]]}
        )
        fig_tds = px.bar(
            df_tds,
            x="Estado",
            y="TDS (mg/L)",
            title="Cambio en TDS tras el filtrado",
            color="Estado",
        )
        fig_tds.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_tds, use_container_width=True)
        
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
    import matplotlib.pyplot as plt

    def plotly_to_matplotlib(fig_plotly):
        """
        Convierte trazos de Plotly a un gráfico Matplotlib compatible
        incluso cuando hay varias series, valores categóricos o estructuras
        no estándar.
        """
        fig_dict = fig_plotly.to_dict()
    
        plt_fig, ax = plt.subplots(figsize=(6,4))
    
        for trace in fig_dict["data"]:
    
            x = trace.get("x", [])
            y = trace.get("y", [])
    
            # --- Limpieza de valores ---
            # Plotly usa a veces numpy, pandas o listas no estándar.
            # Aquí convertimos TODO a listas nativas:
            if hasattr(x, "tolist"):
                x = x.tolist()
            if hasattr(y, "tolist"):
                y = y.tolist()
    
            # Si y es None o está vacío, saltamos este trace
            if y is None or len(y) == 0:
                continue
    
            # Si x es None o está vacío, generamos índices automáticos
            if x is None or len(x) == 0:
                x = list(range(len(y)))
    
            # Aseguramos conversiones numéricas cuando sea posible
            try:
                y = [float(v) for v in y]
            except:
                # Si NO se pueden convertir (categorías), saltamos
                continue
    
            # ----- Gráfica tipo barra -----
            if trace["type"] == "bar":
                ax.bar(
                    x,
                    y,
                    label = trace.get("name", "")
                )
    
            # ----- Gráfica tipo línea -----
            elif trace["type"] == "scatter":
                ax.plot(
                    x,
                    y,
                    label = trace.get("name", "")
                )
    
        # ---- Títulos -----
        layout = fig_dict.get("layout", {})
        ax.set_title(layout.get("title", {}).get("text", ""))
        ax.set_xlabel(layout.get("xaxis", {}).get("title", {}).get("text", ""))
        ax.set_ylabel(layout.get("yaxis", {}).get("title", {}).get("text", ""))
    
        if "legend" in layout:
            ax.legend()
    
        plt.tight_layout()
        return plt_fig

    
    def fig_to_image_reader(fig_local):
        buf = BytesIO()
    
        # Si es figura de Matplotlib
        if hasattr(fig_local, "savefig"):
            fig_local.savefig(buf, format="png", dpi=120, bbox_inches="tight")
            buf.seek(0)
            return ImageReader(buf)
    
        # Si es Plotly
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(fig_local, format="png", engine="json")
            buf.write(img_bytes)
            buf.seek(0)
            return ImageReader(buf)
        except:
            raise ValueError("Error convirtiendo figura Plotly a PNG")
    
    
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
    
        # ---------- TÍTULO ----------
        c.setFillColor(colors.darkblue)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "Reporte de Purificación de Agua – Ecatepec")
        c.setFillColor(colors.black)
    
        # ---------- DATOS ----------
        y = height - 90
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "1. Datos del agua analizada")
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
    
        # ---------- TABLA FILTROS ----------
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "2. Comparativa de filtros utilizados")
        y -= 20
    
        # Encabezado
        c.setFillColor(colors.darkblue)
        c.rect(50, y - 15, 500, 18, fill=1)
        c.setFillColor(colors.white)
        c.drawString(55, y - 12, "Filtro")
        c.drawString(220, y - 12, "Eficiencia (%)")
        c.drawString(390, y - 12, "Purificación (%)")
    
        c.setFillColor(colors.black)
        y -= 25
        c.setFont("Helvetica", 9)
    
        for _, fila in df_filtros_local.iterrows():
            if y < 120:
                c.showPage()
                y = height - 80
            c.drawString(55, y, str(fila["Filtro"]))
            c.drawString(220, y, f"{fila['Eficiencia base (%)']:.1f}")
            c.drawString(390, y, f"{fila['Purificación estimada (%)']:.1f}")
            y -= 14
    
        # ---------- GRÁFICAS ----------
        c.showPage()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 50, "3. Gráficas de análisis")
    
        # ----- Filtros -----
        fig_filtros_mpl = plotly_to_matplotlib(fig_filtros_local)
        img_filtros = fig_to_image_reader(fig_filtros_mpl)
        
        # ----- Radar (mpl) -----
        img_radar = fig_to_image_reader(fig_radar_local)
        
        # ----- ANTES / DESPUES -----
        fig_ba_mpl = plotly_to_matplotlib(fig_before_after_local)
        img_ba = fig_to_image_reader(fig_ba_mpl)

    
        c.drawImage(img_filtros, 50, height - 350, width=500, height=250)
        c.drawImage(img_radar, 150, 50, width=300, height=220)
    
        # ---------- BEFORE / AFTER ----------
        c.showPage()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 50, "4. Comparativa antes/después del filtrado")
        c.drawImage(img_ba, 50, 200, width=500, height=300)
    
        # ---------- TDS ----------
        c.showPage()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 50, "5. Análisis especializado de TDS")
    
        y = height - 90
        c.setFont("Helvetica", 10)
    
        tds_before = info_tds_local["tds_before"]
        tds_after = info_tds_local["tds_after"]
        reduccion = 100 * (1 - tds_after / tds_before)
    
        tds_lineas = [
            f"TDS inicial: {tds_before:.2f} mg/L",
            f"TDS tras filtrado: {tds_after:.2f} mg/L",
            f"Reducción estimada: {reduccion:.1f} %",
        ]
    
        for l in tds_lineas:
            c.drawString(60, y, l)
            y -= 16
    
        # ---------- FIN ----------
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    # ===============================
    #           GENERAR PDF
    # ===============================
    st.write("---")
    st.subheader("📄 Generar reporte PDF de la última simulación (con enfoque TDS)")
    
    # 1) Si NO hay historial → no podemos generar PDF
    if len(st.session_state["historial"]) == 0:
        st.warning("Aún no puedes generar el PDF porque no hay simulaciones guardadas.")
    else:
        # 2) Cargar historial
        df_hist = pd.DataFrame(st.session_state["historial"])
    
        # 3) Validar que existan datos para todas las gráficas
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
            # --- TODO OK, GENERAMOS EL PDF ---
            ultima = df_hist.iloc[-1]   # AHORA df_hist sí existe
            df_filtros = st.session_state["df_filtros"]
            fig_filtros = st.session_state["fig_filtros"]
            fig_radar = st.session_state["fig_radar"]
            fig_before_after = st.session_state["fig_before_after"]
            info_tds = st.session_state["tds_info"]
    
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
