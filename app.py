import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

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
        "impacts": "Impacts Count",
        "work_rate": "Work Rate (m/min)",
        "power_score": "Power Score",
        "work_ratio": "Work Ratio (%)",
        "max_acc": "Max Acceleration (m/s²)",
        "max_dec": "Max Deceleration (m/s²)",
        "power_plays": "Power Plays",
        "session_score": "Session Score (%)",
        "rhie": "RHIE Count"
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
        "impacts": "Recuento de Impactos",
        "work_rate": "Índice de Trabajo (m/min)",
        "power_score": "Puntuación de Potencia",
        "work_ratio": "Ratio de Trabajo (%)",
        "max_acc": "Aceleración Máxima (m/s²)",
        "max_dec": "Deceleración Máxima (m/s²)",
        "power_plays": "Jugadas de Potencia",
        "session_score": "Puntuación de la Sesión (%)",
        "rhie": "Esfuerzos Repetidos Alta Intensidad"
    }
}[lang]

st.markdown("""
    <style>
        .metric-box {
            background: linear-gradient(135deg, #1a1a1a, #333333);
            color: #ff0040;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            margin: 6px;
            box-shadow: 0 0 8px #ff0040;
        }
        .metric-title {
            font-size: 16px;
            color: white;
        }
        .metric-value {
            font-size: 26px;
            font-weight: bold;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

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

    st.title(labels["title"])

    if not df.empty:
        columns_exist = [v for v in metrics.values() if v in df.columns]
        numeric_df = df[columns_exist].apply(pd.to_numeric, errors='coerce')
        df_grouped = df.groupby('Player Name')[columns_exist].apply(lambda x: pd.to_numeric(x, errors='coerce')).mean().reset_index()

        st.subheader(labels["averages"])

        metric_labels = list(metrics.items())
        for i in range(0, len(metric_labels), 4):
            metric_cols = st.columns(4)
            for j, (k, v) in enumerate(metric_labels[i:i+4]):
                if v in df_grouped.columns:
                    avg = df_grouped[v].mean()
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
                fig = go.Figure(go.Bar(
                    x=chart_df[v],
                    y=chart_df['Player Name'],
                    orientation='h',
                    text=chart_df[v].round(1),
                    textposition='outside',
                    marker_color='crimson'
                ))
                fig.update_layout(height=400, xaxis_title=k, yaxis_title=labels["player"])
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Cargue uno o más archivos CSV para comenzar / Upload one or more CSV files to begin.")
