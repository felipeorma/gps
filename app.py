
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import base64
from fpdf import FPDF

st.set_page_config(layout="wide")

# Idioma
lang = st.sidebar.selectbox("Language / Idioma", ["English", "Español"])

# Traducción de métricas y textos
labels = {
    "English": {
        "title": "Match GPS Report",
        "upload": "Upload match CSV files",
        "match": "Match",
        "half": "Half",
        "player": "Player",
        "first_half": "First Half",
        "second_half": "Second Half",
        "all": "All",
        "averages": "Player(s) Averages",
        "distance": "Total Distance (m)",
        "tempo": "Tempo Distance (m)",
        "hsr": "HSR Distance (m)",
        "sprint": "Sprint Distance (m)",
        "sprint_count": "Number of Sprints",
        "max_speed": "Max Speed (m/s)",
        "acc": "Accelerations (#)",
        "dec": "Decelerations (#)",
        "load": "Player Load",
        "rhie": "RHIE Count",
        "create_pdf": "📄 Generate PDF Report",
        "download_pdf": "📥 Download PDF Report",
        "avg_of": "Average of",
        "Carga": "Load",
        "Velocidad e Intensidad": "Speed & Intensity",
        "Aceleración y Desaceleración": "Acceleration & Deceleration",
        "Distancias": "Distances",
        "Esfuerzos Repetidos": "Repeated High-Intensity Efforts",
        "pdf_title": "Team GPS Report",
        "pdf_file": "gps_report.pdf"
    },
    "Español": {
        "title": "Informe GPS del Partido",
        "upload": "Sube archivos CSV del partido",
        "match": "Partido",
        "half": "Tiempo",
        "player": "Jugador",
        "first_half": "Primer Tiempo",
        "second_half": "Segundo Tiempo",
        "all": "Todos",
        "averages": "Promedios del(los) Jugador(es)",
        "distance": "Distancia Total (m)",
        "tempo": "Distancia en Tempo (m)",
        "hsr": "Distancia HSR (m)",
        "sprint": "Distancia en Sprint (m)",
        "sprint_count": "N° de Sprints",
        "max_speed": "Velocidad Máxima (m/s)",
        "acc": "Aceleraciones (#)",
        "dec": "Deceleraciones (#)",
        "load": "Carga del Jugador",
        "rhie": "Esfuerzos Repetidos Alta Intensidad",
        "create_pdf": "📄 Crear Informe PDF",
        "download_pdf": "📥 Descargar Informe PDF",
        "avg_of": "Promedio de",
        "Carga": "Carga",
        "Velocidad e Intensidad": "Velocidad e Intensidad",
        "Aceleración y Desaceleración": "Aceleración y Desaceleración",
        "Distancias": "Distancias",
        "Esfuerzos Repetidos": "Esfuerzos Repetidos",
        "pdf_title": "Informe GPS del Equipo",
        "pdf_file": "informe_gps.pdf"
    }
}[lang]

# Estilos neón rojo
st.markdown("""
    <style>
        .metric-box {
            background: linear-gradient(135deg, #1a0000, #330000);
            color: #ff0033;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            margin: 6px;
            box-shadow: 0 0 12px #ff0033;
        }
        .metric-title {
            font-size: 16px;
            font-weight: bold;
            color: white;
        }
        .metric-value {
            font-size: 26px;
            font-weight: bold;
            color: white;
        }
        body {
            background-color: #0d0d0d;
        }
        .stApp {
            background-image: linear-gradient(to right, #0d0d0d 0%, #1a1a1a 100%);
        }
    </style>
""", unsafe_allow_html=True)

def generate_pdf(title, summary, avg_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    for k, v in summary.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    pdf.ln(5)
    for cat, items in avg_data.items():
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"{labels['avg_of']} {cat}", ln=True)
        pdf.set_font("Arial", size=11)
        for label, val in items:
            pdf.cell(200, 8, txt=f"{label}: {val:.1f}", ln=True)
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

def neon_bar_chart(df, label, column):
    fig = go.Figure(go.Bar(
        x=df[column],
        y=df['Player Name'],
        orientation='h',
        text=df[column].round(1),
        textposition='outside',
        marker_color='lime'
    ))
    fig.update_layout(
        height=400,
        xaxis_title=label,
        yaxis_title=labels["player"],
        plot_bgcolor='#0d0d0d',
        paper_bgcolor='#0d0d0d',
        font=dict(color='white')
    )
    return fig

# Sidebar y lógica
st.sidebar.header("Filtros")
uploaded_files = st.sidebar.file_uploader(labels["upload"], type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file, delimiter=';')
        df.columns = df.columns.str.strip()
        name_parts = file.name.split('_')
        try:
            year, month, day = name_parts[-3], name_parts[-2], name_parts[-1].split('.')[0]
            fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            fecha = 'Sin Fecha'
        df['Fecha CSV'] = fecha
        df['Archivo'] = file.name
        partido_base = re.sub(r'\s*[-_]*\s*(1ER|2DO)?\s*TIEMPO', '', df['Period Name'].iloc[0], flags=re.IGNORECASE)
        df['Partido + Fecha'] = f"{partido_base.strip()} | {fecha}"
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)

    metrics = {
        labels["distance"]: 'Work Rate Total Dist',
        labels["tempo"]: 'Tempo Distance (Gen2)',
        labels["hsr"]: 'HSR Eff Distance (Gen2)',
        labels["sprint"]: 'Sprint Eff Distance (Gen2)',
        labels["sprint_count"]: 'Sprint Eff Count (Gen2)',
        labels["max_speed"]: 'Max Velocity',
        labels["acc"]: 'Acc Eff Count (Gen2)',
        labels["dec"]: 'Dec Eff Count (Gen2)',
        labels["load"]: 'Player Load',
        "Peak Player Load": 'Peak Player Load',
        "Player Load Work Time": 'Player Load Work Time',
        "Player Load Rest Time": 'Player Load Rest Time',
        "Player Load Work:Rest": 'Player Load Work:Rest',
        "Velocity Exertion": 'Velocity Exertion',
        "Velocity Exertion Per Min": 'Velocity Exertion Per Min',
        "Acceleration Load": 'Acceleration Load',
        "Acceleration Density Index": 'Acceleration Density Index',
        labels["rhie"]: 'RHIE Total Bouts'
    }

    partidos = sorted(set([p for p in full_df['Partido + Fecha'].unique() if not re.search(r'(1ER|2DO)', p, re.IGNORECASE)]))
    partido = st.sidebar.selectbox(labels["match"], [labels["all"]] + partidos)

    tiempo_map = {labels["all"]: 'Todos', labels["first_half"]: 1, labels["second_half"]: 2}
    tiempo_sel = st.sidebar.selectbox(labels["half"], list(tiempo_map.keys()))

    jugadores = [labels["all"]] + sorted(full_df['Player Name'].dropna().unique().tolist())
    jugador = st.sidebar.selectbox(labels["player"], jugadores)

    df = full_df.copy()
    if partido != labels["all"]:
        df = df[df['Partido + Fecha'] == partido]
    if tiempo_map[tiempo_sel] != 'Todos':
        df = df[df['Period Number'] == tiempo_map[tiempo_sel]]
    if jugador != labels["all"]:
        df = df[df['Player Name'] == jugador]

    st.title(f"{labels['title']} - {jugador if jugador != labels['all'] else ''} {('| ' + partido) if partido != labels['all'] else ''}")

    if not df.empty:
        columns_exist = [v for v in metrics.values() if v in df.columns]
        df[columns_exist] = df[columns_exist].apply(pd.to_numeric, errors='coerce')
        df_grouped = df.groupby('Player Name')[columns_exist].mean().reset_index()

        st.subheader(f"{labels['averages']}: {jugador}" if jugador != labels["all"] else labels['averages'])

        grouped_metrics = {
            labels["Carga"]: [labels["load"], "Peak Player Load", "Player Load Work Time", "Player Load Rest Time", "Player Load Work:Rest"],
            labels["Velocidad e Intensidad"]: [labels["max_speed"], "Velocity Exertion", "Velocity Exertion Per Min"],
            labels["Aceleración y Desaceleración"]: [labels["acc"], labels["dec"], "Acceleration Load", "Acceleration Density Index"],
            labels["Distancias"]: [labels["distance"], labels["tempo"], labels["hsr"], labels["sprint"], labels["sprint_count"]],
            labels["Esfuerzos Repetidos"]: [labels["rhie"]]
        }

        if st.button(labels["create_pdf"]):
            resumen = {"Partido": partido, "Fecha": df['Fecha CSV'].iloc[0], "Jugador": jugador}
            resumen_avg = {}
            for group, keys in grouped_metrics.items():
                items = []
                for k in keys:
                    col_key = metrics.get(k)
                    if col_key in df_grouped.columns:
                        val = df_grouped[col_key].mean()
                        if not pd.isna(val) and val != 0:
                            items.append((k, val))
                if items:
                    resumen_avg[group] = items

            pdf_bytes = generate_pdf(labels["pdf_title"], resumen, resumen_avg)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{labels["pdf_file"]}">{labels["download_pdf"]}</a>'
            st.markdown(href, unsafe_allow_html=True)

        for group, keys in grouped_metrics.items():
            st.markdown(f"### {labels['avg_of']} {group}")
            metric_items = [(k, metrics[k]) for k in keys if k in metrics and metrics[k] in df_grouped.columns]
            for i in range(0, len(metric_items), 4):
                metric_cols = st.columns(4)
                for j, (k, v) in enumerate(metric_items[i:i+4]):
                    avg = df_grouped[v].mean()
                    if not pd.isna(avg) and avg != 0:
                        metric_cols[j].markdown(f"""
                            <div class='metric-box'>
                                <div class='metric-title'>{k}</div>
                                <div class='metric-value'>{avg:.0f}</div>
                            </div>
                        """, unsafe_allow_html=True)

        st.divider()

        for k, v in metrics.items():
            if v in df.columns:
                st.subheader(k)
                chart_df = df.groupby('Player Name')[v].sum().reset_index().sort_values(v, ascending=True)
                fig = neon_bar_chart(chart_df, k, v)
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Cargue uno o más archivos CSV para comenzar / Upload one or more CSV files to begin.")
