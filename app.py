import streamlit as st
import pandas as pd
import plotly.express as px
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
        'Carga de Aceleración': 'Acceleration Load',
        'Velocidad Máxima (m/s)': 'Max Velocity [ Per Max ]',
        'Aceleraciones Altas (#)': 'Acc3 Eff (Gen2)',
        'Aceleraciones Medias (#)': 'Acc2 Eff (Gen2)',
        'Aceleraciones Bajas (#)': 'Acc1 Eff (Gen2)',
        'Deceleraciones Altas (#)': 'Dec3 Eff (Gen2)',
        'Deceleraciones Medias (#)': 'Dec2 Eff (Gen2)',
        'Deceleraciones Bajas (#)': 'Dec1 Eff (Gen2)'
    }

    # Lista de partidos únicos
    partidos = ['Todos'] + sorted(full_df['Period Name'].dropna().unique().tolist())
    partido_seleccionado = st.sidebar.selectbox("Match", partidos)

    # Lista de jugadores únicos
    jugadores = ['Todos'] + sorted(full_df['Player Name'].dropna().unique().tolist())
    jugador_seleccionado = st.sidebar.selectbox("Player Name", jugadores)

    # Filtrar por partido
    df = full_df.copy()
    if partido_seleccionado != 'Todos':
        df = df[df['Period Name'] == partido_seleccionado]

    if jugador_seleccionado != 'Todos':
        df = df[df['Player Name'] == jugador_seleccionado]

    st.title("Match GPS Report")

    # Mostrar métricas generales (similares a parte inferior del ejemplo visual)
    avg_data = df.groupby('Player Name').agg({
        'Work Rate Total Dist': 'mean',
        'Acceleration Load': 'mean',
        'Max Velocity [ Per Max ]': 'mean',
        'Acc3 Eff (Gen2)': 'mean',
        'Acc2 Eff (Gen2)': 'mean',
        'Acc1 Eff (Gen2)': 'mean',
        'Dec3 Eff (Gen2)': 'mean',
        'Dec2 Eff (Gen2)': 'mean',
        'Dec1 Eff (Gen2)': 'mean'
    }).reset_index()

    td_avg = round(avg_data['Work Rate Total Dist'].mean(), 2)
    acc_avg = round(avg_data['Acceleration Load'].mean(), 2)
    vmax_avg = round(avg_data['Max Velocity [ Per Max ]'].mean(), 2)
    acc_total = avg_data[['Acc3 Eff (Gen2)', 'Acc2 Eff (Gen2)', 'Acc1 Eff (Gen2)']].sum(axis=1).mean()
    dec_total = avg_data[['Dec3 Eff (Gen2)', 'Dec2 Eff (Gen2)', 'Dec1 Eff (Gen2)']].sum(axis=1).mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"<div class='metric-box'><div class='metric-title'>TD Average</div><div class='metric-value'>{td_avg}</div></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-box'><div class='metric-title'>ACC Load Avg</div><div class='metric-value'>{acc_avg}</div></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-box'><div class='metric-title'>Max Speed Avg</div><div class='metric-value'>{vmax_avg}</div></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='metric-box'><div class='metric-title'>ACC Total Avg</div><div class='metric-value'>{acc_total:.0f}</div></div>", unsafe_allow_html=True)
    col5.markdown(f"<div class='metric-box'><div class='metric-title'>DEC Total Avg</div><div class='metric-value'>{dec_total:.0f}</div></div>", unsafe_allow_html=True)

    st.divider()

    # Tabla principal con todos los jugadores
    if jugador_seleccionado == 'Todos':
        tabla = df.groupby('Player Name')[list(selected_metrics.values())].mean().reset_index()
        tabla = tabla.rename(columns={v: k for k, v in selected_metrics.items()})
        st.dataframe(tabla)

else:
    st.info("Por favor, sube uno o más archivos CSV para comenzar.")

