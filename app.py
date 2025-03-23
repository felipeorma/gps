import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os

# Cargar múltiples archivos CSV
st.sidebar.header("Carga de datos")
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

    # Lista de partidos únicos
    partidos = full_df['Period Name'].dropna().unique().tolist()
    partido_seleccionado = st.sidebar.selectbox("Selecciona un partido", partidos)

    # Filtrar por partido
    df = full_df[full_df['Period Name'] == partido_seleccionado].copy()

    # Título con formato limpio y resultado
    pattern = re.compile(r"F\d+_\w+_(.+?) VS (.+)", re.IGNORECASE)
    match = pattern.search(partido_seleccionado)
    equipo_1, equipo_2 = match.groups() if match else ("Equipo 1", "Equipo 2")
    resultado_match = re.search(r"(.+?) (\d+-\d+)$", equipo_2.strip())
    if resultado_match:
        equipo_2_nombre, resultado = resultado_match.groups()
        titulo_partido = f"{equipo_1.strip()} vs {equipo_2_nombre.strip()} ({resultado})"
    else:
        titulo_partido = f"{equipo_1.strip()} vs {equipo_2.strip()}"

    st.title(f"Dashboard GPS - {titulo_partido}")

    # Selección de jugador
    player_list = ['Todos'] + sorted(df['Player Name'].unique())
    selected_player = st.sidebar.selectbox("Selecciona un jugador", player_list)

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

    first_half = df[df['Period Number'] == 1]
    second_half = df[df['Period Number'] == 2]

    st.subheader("Promedios de Jugador(es)")

    if selected_player == 'Todos':
        display_df = df[['Player Name', 'Fecha CSV'] + list(selected_metrics.values())].copy()
        display_df = display_df.rename(columns={v: k for k, v in selected_metrics.items()})

        st.dataframe(display_df)

        st.subheader("Comparativa entre jugadores")
        selected_chart_metric = st.selectbox("Selecciona una métrica para comparar", list(selected_metrics.keys()))
        col_name = selected_metrics[selected_chart_metric]

        # Total por jugador
        total_df = df.groupby('Player Name')[col_name].sum().reset_index(name='Total')
        total_df = total_df.sort_values(by='Total', ascending=False)

        fig_total = px.bar(total_df, x='Player Name', y='Total', text='Total', title=f"{selected_chart_metric} Total por Jugador")
        fig_total.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig_total)

    else:
        player_df = df[df['Player Name'] == selected_player].copy()
        st.subheader(f"Métricas de {selected_player}")

        selected_chart_metric = st.selectbox("Selecciona una métrica para el jugador", list(selected_metrics.keys()))
        col_name = selected_metrics[selected_chart_metric]

        resumen = player_df.groupby('Fecha CSV')[col_name].agg(["mean", "sum"]).reset_index()
        resumen.columns = ['Fecha', 'Promedio', 'Total']
        st.dataframe(resumen)

        # Por tiempos en una sola barra
        first = player_df[player_df['Period Number'] == 1][col_name].sum()
        second = player_df[player_df['Period Number'] == 2][col_name].sum()
        total = first + second

        fig_player = go.Figure()
        fig_player.add_trace(go.Bar(
            x=[selected_player],
            y=[first],
            name='1er Tiempo',
            marker_color='lightskyblue',
            text=[f"{first:.2f}"],
            textposition='none'
        ))
        fig_player.add_trace(go.Bar(
            x=[selected_player],
            y=[second],
            name='2do Tiempo',
            marker_color='tomato',
            text=[f"{second:.2f}"],
            textposition='none'
        ))
        fig_player.update_layout(
            barmode='stack',
            title=f"{selected_chart_metric} - {selected_player} (Total: {total:.2f})",
            yaxis_title=selected_chart_metric,
            annotations=[
                dict(x=selected_player, y=total, text=f"Total: {total:.2f}", showarrow=False, yshift=10)
            ]
        )
        st.plotly_chart(fig_player)

else:
    st.info("Por favor, sube uno o más archivos CSV para comenzar.")
