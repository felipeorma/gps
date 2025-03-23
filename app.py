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
        "dec": "Decelerations (#)"
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
        "dec": "Deceleraciones (#)"
    }
}[lang]

st.markdown("""
    <style>
        .metric-box {
            background-color: #003C3C;
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 5px;
        }
        .metric-title {
            font-size: 16px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
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
        labels["max_speed"]: 'Max Velocity [ Per Max ]',
        labels["acc"]: 'Acc Eff Count (Gen2)',
        labels["dec"]: 'Dec Eff Count (Gen2)'
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
        df_grouped = df.groupby('Player Name')[columns_exist].mean().reset_index()

        st.subheader(labels["averages"])

        cols = st.columns(len(columns_exist))
        for i, (k, v) in enumerate(metrics.items()):
            if v in df_grouped.columns:
                avg = df_grouped[v].mean()
                cols[i].markdown(f"""
                    <div class='metric-box'>
                        <div class='metric-title'>{k}</div>
                        <div class='metric-value'>{avg:.0f}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Mostrar gráficos individuales
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
                    marker_color='teal'
                ))
                fig.update_layout(height=400, xaxis_title=k, yaxis_title=labels["player"])
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Cargue uno o más archivos CSV para comenzar / Upload one or more CSV files to begin.")
