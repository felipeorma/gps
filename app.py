import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

st.set_page_config(layout="wide")

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

# Cargar múltiples archivos CSV
st.sidebar.header("Filtros")
uploaded_files = st.sidebar.file_uploader("Sube uno o más archivos del partido (.csv)", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file, delimiter=';')
        df.columns = df.columns.str.strip()

        # Extraer fecha desde nombre del archivo
        name_parts = file.name.split('_')
        try:
            year, month, day = name_parts[-3], name_parts[-2], name_parts[-1].split('.')[0]
            fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            fecha = 'Sin Fecha'

        df['Fecha CSV'] = fecha
        df['Archivo'] = file.name
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)

    # Diccionario de métricas
    selected_metrics = {
        'Distancia Total (m)': 'Work Rate Total Dist',
        'Distancia Tempo (m)': 'Tempo Distance (Gen2)',
        'Distancia HSR (m)': 'HSR Eff Distance (Gen2)',
        'Distancia Sprint (m)': 'Sprint Eff Distance (Gen2)',
        'N° Sprints': 'Sprint Eff Count (Gen2)',
        'Velocidad Máxima (m/s)': 'Max Velocity [ Per Max ]',
        'Aceleraciones (#)': 'Acc Eff Count (Gen2)',
        'Deceleraciones (#)': 'Dec Eff Count (Gen2)'
    }

    partidos_unicos = full_df['Period Name'].dropna().unique().tolist()
    partidos = ['Todos'] + partidos_unicos if len(partidos_unicos) > 1 else partidos_unicos
    partido_seleccionado = st.sidebar.selectbox("Match", partidos)

    tiempos = ['Todos', 1, 2]
    tiempo_seleccionado = st.sidebar.selectbox("Tiempo", tiempos)

    jugadores = ['Todos'] + sorted(full_df['Player Name'].dropna().unique().tolist())
    jugador_seleccionado = st.sidebar.selectbox("Jugador", jugadores)

    df = full_df.copy()
    if partido_seleccionado != 'Todos':
        df = df[df['Period Name'] == partido_seleccionado]
    if tiempo_seleccionado != 'Todos':
        df = df[df['Period Number'] == tiempo_seleccionado]
    if jugador_seleccionado != 'Todos':
        df = df[df['Player Name'] == jugador_seleccionado]

    st.title("Match GPS Report")

    if jugador_seleccionado == 'Todos':
        grouped = df.groupby('Player Name').agg({col: 'sum' for col in selected_metrics.values()}).reset_index()
        grouped = grouped.rename(columns={v: k for k, v in selected_metrics.items()})
        grouped = grouped.sort_values(by='Distancia Total (m)', ascending=False)

        st.subheader("Visualización de Jugadores")
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=grouped['Player Name'],
            y=grouped['Distancia Total (m)'],
            name='Total Distance',
            marker_color='dodgerblue',
            text=grouped['Distancia Total (m)'].round(0),
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            x=grouped['Player Name'],
            y=grouped['Distancia Tempo (m)'],
            name='Tempo',
            marker_color='coral',
            text=grouped['Distancia Tempo (m)'].round(0),
            textposition='inside'
        ))

        fig.add_trace(go.Bar(
            x=grouped['Player Name'],
            y=grouped['Distancia HSR (m)'],
            name='HSR',
            marker_color='hotpink',
            text=grouped['Distancia HSR (m)'].round(0),
            textposition='inside'
        ))

        fig.add_trace(go.Bar(
            x=grouped['Player Name'],
            y=grouped['Distancia Sprint (m)'],
            name='Sprint',
            marker_color='goldenrod',
            text=grouped['Distancia Sprint (m)'].round(0),
            textposition='inside'
        ))

        fig.update_layout(
            barmode='group',
            xaxis_title='Jugador',
            yaxis_title='Metros / Métrica',
            height=600,
            legend_title_text='Métricas',
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Por favor, sube uno o más archivos CSV para comenzar.")
