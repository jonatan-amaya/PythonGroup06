"""Dashboard: ¿el Estado declara emergencia donde más llueve? (temporada 2023).

Correr en local, desde la carpeta assignment_3/:
    uv run streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------- configuracion
st.set_page_config(page_title="Lluvias y emergencias 2023", page_icon="🌧️", layout="wide")

# La ruta se arma desde la ubicación de este archivo: Streamlit Cloud ejecuta la
# app desde la raíz del repositorio, no desde assignment_3/.
DATOS = Path(__file__).parent / "datos" / "dataset.csv"
FUENTE = "Fuente: decretos de emergencia PCM (gob.pe) + Open-Meteo · temporada ene-may 2023"

# Rampa secuencial de un solo tono (azul = lluvia): claro = poca, oscuro = mucha.
AZULES = ["#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]

VARIABLES_LLUVIA = {
    "Lluvia total (mm)": "lluvia_total_mm",
    "Días de lluvia fuerte (≥ 20 mm)": "dias_lluvia_fuerte",
}

ETIQUETAS = {
    "departamento": "Departamento",
    "capital": "Capital",
    "lluvia_total_mm": "Lluvia total (mm)",
    "dias_lluvia_fuerte": "Días de lluvia fuerte",
    "declaratorias": "Declaratorias",
    "prorrogas": "Prórrogas",
}


# ------------------------------------------------------------------ carga datos
# @st.cache_data guarda el resultado: sin esto, el CSV se lee otra vez cada vez
# que alguien mueve un filtro.
@st.cache_data
def cargar():
    return pd.read_csv(DATOS, dtype={"ubigeo": str}, encoding="utf-8-sig")


datos = cargar()

# ----------------------------------------------------------------------- filtros
st.sidebar.header("Filtros")

departamentos = sorted(datos["departamento"].unique())
elegidos = st.sidebar.multiselect(
    "Departamento", departamentos, placeholder="Todos (vacío = los 25)"
)

etiqueta_lluvia = st.sidebar.selectbox("Variable de lluvia", list(VARIABLES_LLUVIA))
var_lluvia = VARIABLES_LLUVIA[etiqueta_lluvia]

tope = int(-(-datos["lluvia_total_mm"].max() // 50) * 50)  # redondeo hacia arriba a 50
lluvia_min, lluvia_max = st.sidebar.slider(
    "Rango de lluvia total (mm)", 0, tope, (0, tope), step=50
)

solo_con_declaratoria = st.sidebar.checkbox("Solo departamentos con al menos una declaratoria")

filtrado = datos[datos["lluvia_total_mm"].between(lluvia_min, lluvia_max)]
if elegidos:
    filtrado = filtrado[filtrado["departamento"].isin(elegidos)]
if solo_con_declaratoria:
    filtrado = filtrado[filtrado["declaratorias"] > 0]

st.sidebar.caption(f"{len(filtrado)} de {len(datos)} departamentos en la vista.")

# ------------------------------------------------------------------------ titulo
st.title("🌧️ ¿El Estado declara emergencia donde más llueve?")
st.caption(f"Declaratorias de emergencia por lluvias vs. lluvia registrada en la capital de cada departamento · {FUENTE}")

if filtrado.empty:
    st.warning("No hay departamentos que cumplan los filtros. Ajusta la selección.")
    st.stop()

# ---------------------------------------------------------------------- metricas
promedio_nacional = datos[var_lluvia].mean()
promedio_vista = filtrado[var_lluvia].mean()
unidad = "mm" if var_lluvia == "lluvia_total_mm" else "días"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Departamentos", f"{len(filtrado)}")
AYUDA_SUMA = ("Un mismo decreto puede abarcar varios departamentos: se cuenta una vez "
              "por cada departamento que menciona, no como decretos distintos.")
c2.metric("Total de declaratorias ", f"{int(filtrado['declaratorias'].sum())}", help=AYUDA_SUMA)
c3.metric("Prórrogas (suma por depto.)", f"{int(filtrado['prorrogas'].sum())}", help=AYUDA_SUMA)
c4.metric(
    f"{etiqueta_lluvia.split(' (')[0]} promedio",
    f"{promedio_vista:,.1f} {unidad}",
    # El delta solo tiene sentido cuando la vista no es el país completo.
    delta=(f"{promedio_vista - promedio_nacional:+,.1f} vs. promedio nacional"
           if len(filtrado) < len(datos) else None),
    delta_color="off",
)

st.divider()

# ---------------------------------------------------------------------- graficos
alto = max(350, 24 * len(filtrado) + 80)
izq, der = st.columns(2)

with izq:
    st.subheader("Lima y Ancash lideran emergencias con poca lluvia(correlacion-0.19)")
    st.caption(f"El color indica la {etiqueta_lluvia.lower()}: más oscuro, más lluvia.")
    por_depto = filtrado.sort_values(["declaratorias", var_lluvia])
    fig = px.bar(
        por_depto, x="declaratorias", y="departamento", orientation="h",
        color=var_lluvia, color_continuous_scale=AZULES, text="declaratorias",
        hover_data={"capital": True, "lluvia_total_mm": True, "dias_lluvia_fuerte": True,
                    "prorrogas": True},
        labels={**ETIQUETAS, "departamento": ""},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=alto,
        coloraxis_colorbar=dict(title=unidad),
        margin=dict(l=0, r=10, t=10, b=0),
    )
    fig.update_yaxes(automargin=True)
    st.plotly_chart(fig, width="stretch")

with der:
    st.subheader(f"{etiqueta_lluvia} vs. declaratorias")
    # Spearman = correlación de Pearson sobre los rangos (evita depender de scipy).
    rho = (filtrado[var_lluvia].rank().corr(filtrado["declaratorias"].rank())
           if len(filtrado) >= 3 else float("nan"))
    if pd.notna(rho):
        st.caption(f"Correlación de Spearman en la vista: **{rho:+.2f}** "
                   "(cercana a 0 = no hay relación; positiva = más lluvia, más declaratorias).")
    else:
        st.caption("Se necesitan al menos 3 departamentos con valores distintos para calcular la correlación.")
    fig = px.scatter(
        filtrado, x=var_lluvia, y="declaratorias",
        hover_name="departamento",
        hover_data={"capital": True, "prorrogas": True},
        labels=ETIQUETAS,
    )
    fig.update_traces(
        marker=dict(size=12, color="#2a78d6", line=dict(width=2, color="white")),
    )
    # Etiquetas directas solo para los extremos, no en cada punto.
    extremos = pd.concat([
        filtrado.nlargest(2, "declaratorias"),
        filtrado.nlargest(2, var_lluvia),
    ]).drop_duplicates("departamento")
    for _, fila in extremos.iterrows():
        fig.add_annotation(
            x=fila[var_lluvia], y=fila["declaratorias"], text=fila["departamento"],
            showarrow=False, yshift=14, font=dict(size=12),
        )
    fig.update_layout(height=alto, margin=dict(l=0, r=10, t=10, b=0))
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True, dtick=1)
    st.plotly_chart(fig, width="stretch")

# -------------------------------------------------------------------------- mapa
st.subheader("Mapa: capitales departamentales")
st.caption(f"Tamaño del círculo = número de declaratorias · color = {etiqueta_lluvia.lower()}.")

mapa = filtrado.assign(tamano=filtrado["declaratorias"] + 1)  # +1 para que 0 se vea
fig = px.scatter_map(
    mapa, lat="latitud", lon="longitud",
    size="tamano", size_max=30,
    color=var_lluvia, color_continuous_scale=AZULES,
    hover_name="departamento",
    hover_data={"capital": True, "declaratorias": True, "prorrogas": True,
                "lluvia_total_mm": True, "dias_lluvia_fuerte": True,
                "tamano": False, "latitud": False, "longitud": False},
    labels=ETIQUETAS,
    map_style="carto-positron",
    zoom=4.8, center={"lat": -10.0, "lon": -75.0},
    height=600,
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar=dict(title=unidad))
# scrollZoom=False: la rueda del mouse desplaza la página en vez de hacer zoom al mapa.
st.plotly_chart(fig, width="stretch", config={"scrollZoom": False})

# ------------------------------------------------------------------------- tabla
st.subheader("Datos filtrados")

tabla = filtrado.sort_values("declaratorias", ascending=False)[
    ["ubigeo", "departamento", "capital", "lluvia_total_mm", "dias_lluvia_fuerte",
     "declaratorias", "prorrogas"]
]
st.dataframe(
    tabla,
    width="stretch",
    hide_index=True,
    column_config={
        "ubigeo": "Ubigeo",
        "departamento": "Departamento",
        "capital": "Capital",
        "lluvia_total_mm": st.column_config.ProgressColumn(
            "Lluvia total (mm)", format="%.1f", min_value=0,
            max_value=float(datos["lluvia_total_mm"].max()),
        ),
        "dias_lluvia_fuerte": "Días de lluvia fuerte",
        "declaratorias": "Declaratorias",
        "prorrogas": "Prórrogas",
    },
)

st.download_button(
    "Descargar datos filtrados (CSV)",
    tabla.to_csv(index=False).encode("utf-8"),
    "lluvias_emergencias_filtrado.csv",
    "text/csv",
)

st.caption(FUENTE)
