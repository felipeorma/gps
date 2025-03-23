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

        # Asegurar nombre limpio del partido (sin tiempos u otros)
        partido_base = re.sub(r'\s*[-_]*\s*(1ER|2DO)?\s*TIEMPO', '', df['Period Name'].iloc[0], flags=re.IGNORECASE)
        df['Partido + Fecha'] = f"{partido_base.strip()} | {fecha}"

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

    partidos_unicos = sorted(set([p for p in full_df['Partido + Fecha'].unique() if not re.search(r'(1ER|2DO)\s*TIEMPO', p, re.IGNORECASE)]))
    partidos = ['Todos'] + partidos_unicos if len(partidos_unicos) > 1 else partidos_unicos
    partido_seleccionado = st.sidebar.selectbox("Match", partidos)

    tiempo_dict = {'Todos': 'Todos', 1: 'Primer Tiempo', 2: 'Segundo Tiempo'}
    tiempo_seleccionado_raw = st.sidebar.selectbox("Tiempo", list(tiempo_dict.keys()), format_func=lambda x: tiempo_dict[x])

    jugadores = ['Todos'] + sorted(full_df['Player Name'].dropna().unique().tolist())
    jugador_seleccionado = st.sidebar.selectbox("Jugador", jugadores)

    df = full_df.copy()
    if partido_seleccionado != 'Todos':
        df = df[df['Partido + Fecha'] == partido_seleccionado]
    if tiempo_seleccionado_raw != 'Todos':
        df = df[df['Period Number'] == tiempo_seleccionado_raw]
    if jugador_seleccionado != 'Todos':
        df = df[df['Player Name'] == jugador_seleccionado]

    st.title("Match GPS Report")

    if jugador_seleccionado == 'Todos':
        columns_existentes = [col for col in selected_metrics.values() if col in df.columns]
        grouped = df.groupby('Player Name').agg({col: 'sum' for col in columns_existentes}).reset_index()
        rename_dict = {v: k for k, v in selected_metrics.items() if v in columns_existentes}
        grouped = grouped.rename(columns=rename_dict)

        if 'Distancia Total (m)' in grouped.columns:
            grouped = grouped.sort_values(by='Distancia Total (m)', ascending=False)

        # Agregar fila con totales del equipo
        team_total = grouped.drop(columns=['Player Name']).sum(numeric_only=True)
        team_total['Player Name'] = 'Total Equipo'
        grouped = pd.concat([grouped, pd.DataFrame([team_total])], ignore_index=True)

        # Calcular promedios para visual boxes
        td_avg = grouped['Distancia Total (m)'][:-1].mean()
        tempo_avg = grouped['Distancia Tempo (m)'][:-1].mean()
        hsr_avg = grouped['Distancia HSR (m)'][:-1].mean()
        sprint_avg = grouped['Distancia Sprint (m)'][:-1].mean()
        acc_avg = grouped['Aceleraciones (#)'][:-1].mean()
        dec_avg = grouped['Deceleraciones (#)'][:-1].mean()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.markdown(f"<div class='metric-box'><div class='metric-title'>TD Average</div><div class='metric-value'>{td_avg:.0f}</div></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-box'><div class='metric-title'>Tempo Average</div><div class='metric-value'>{tempo_avg:.0f}</div></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-box'><div class='metric-title'>HSR Average</div><div class='metric-value'>{hsr_avg:.0f}</div></div>", unsafe_allow_html=True)
        col4.markdown(f"<div class='metric-box'><div class='metric-title'>Sprint Average</div><div class='metric-value'>{sprint_avg:.0f}</div></div>", unsafe_allow_html=True)
        col5.markdown(f"<div class='metric-box'><div class='metric-title'>ACC Average</div><div class='metric-value'>{acc_avg:.0f}</div></div>", unsafe_allow_html=True)
        col6.markdown(f"<div class='metric-box'><div class='metric-title'>DEC Average</div><div class='metric-value'>{dec_avg:.0f}</div></div>", unsafe_allow_html=True)

        st.divider()

        st.subheader("Visualización de Jugadores")
        fig = go.Figure()

        for metric, color in zip(['Distancia Total (m)', 'Distancia Tempo (m)', 'Distancia HSR (m)', 'Distancia Sprint (m)'],
                                  ['dodgerblue', 'coral', 'hotpink', 'goldenrod']):
            if metric in grouped.columns:
                fig.add_trace(go.Bar(
                    y=grouped['Player Name'],
                    x=grouped[metric],
                    name=metric,
                    orientation='h',
                    marker_color=color,
                    text=grouped[metric].round(0),
                    textposition='inside'
                ))

        fig.update_layout(
            barmode='stack',
            yaxis_title='Jugador',
            xaxis_title='Metros / Métrica',
            height=700,
            legend_title_text='Métricas',
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            yaxis={'categoryorder': 'total ascending'}
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tabla con Métricas por Jugador")
        st.dataframe(grouped, use_container_width=True)

else:
    st.info("Por favor, sube uno o más archivos CSV para comenzar.")
