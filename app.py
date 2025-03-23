import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# Cargar archivo CSV
st.sidebar.header("Carga de datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo del partido (.csv)", type=["csv"])

if uploaded_file:
    # Leer el archivo con separador ; y limpiar nombres de columnas
    df = pd.read_csv(uploaded_file, delimiter=';')
    df.columns = df.columns.str.strip()

    # Obtener nombre del partido desde el archivo
    raw_name = df['Period Name'].iloc[0] if 'Period Name' in df.columns else "Partido 1"

    # Extraer nombre limpio y resultado
    pattern = re.compile(r"F\d+_\w+_(.+?) VS (.+)", re.IGNORECASE)
    match = pattern.search(raw_name)
    equipo_1, equipo_2 = match.groups() if match else ("Equipo 1", "Equipo 2")

    resultado_match = re.search(r"(.+?) (\d+-\d+)$", equipo_2.strip())
    if resultado_match:
        equipo_2_nombre, resultado = resultado_match.groups()
        titulo_partido = f"{equipo_1.strip()} vs {equipo_2_nombre.strip()} ({resultado})"
    else:
        titulo_partido = f"{equipo_1.strip()} vs {equipo_2.strip()}"

    st.title(f"Dashboard GPS - {titulo_partido}")
    st.sidebar.success("Archivo cargado exitosamente")
    st.sidebar.write(titulo_partido)

    player_list = ['Todos'] + sorted(df['Player Name'].unique())
    selected_player = st.sidebar.selectbox("Selecciona un jugador", player_list)

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

    full_df = df.copy()
    display_df = full_df[['Player Name'] + list(selected_metrics.values())].copy()
    display_df = display_df.rename(columns={v: k for k, v in selected_metrics.items()})

    st.subheader("Promedios de Jugador(es)")
    first_half = full_df[full_df['Period Number'] == 1]
    second_half = full_df[full_df['Period Number'] == 2]

    col1, col2, col3 = st.columns(3)
    col1.metric("Distancia Total Promedio (m) - Total", round(display_df['Distancia Total (m)'].mean(), 2))
    col2.metric("1er Tiempo", round(first_half['Work Rate Total Dist'].mean(), 2))
    col3.metric("2do Tiempo", round(second_half['Work Rate Total Dist'].mean(), 2))

    col1.metric("Carga de Aceleración Promedio - Total", round(display_df['Carga de Aceleración'].mean(), 2))
    col2.metric("1er Tiempo", round(first_half['Acceleration Load'].mean(), 2))
    col3.metric("2do Tiempo", round(second_half['Acceleration Load'].mean(), 2))

    col1.metric("Velocidad Máxima (m/s) Promedio - Total", round(display_df['Velocidad Máxima (m/s)'].mean(), 2))
    col2.metric("1er Tiempo", round(first_half['Max Velocity [ Per Max ]'].mean(), 2))
    col3.metric("2do Tiempo", round(second_half['Max Velocity [ Per Max ]'].mean(), 2))

    st.divider()

    if selected_player != 'Todos':
        player_data = full_df[full_df['Player Name'] == selected_player]
        player_display = player_data[['Player Name'] + list(selected_metrics.values())].copy()
        player_display = player_display.rename(columns={v: k for k, v in selected_metrics.items()})
        st.dataframe(player_display)

        radar_data = player_display.set_index('Player Name').T.reset_index()
        radar_data.columns = ['Métrica', 'Valor']

        fig = px.line_polar(radar_data, r='Valor', theta='Métrica', line_close=True,
                            title=f"Perfil Físico - {selected_player}")
        st.plotly_chart(fig)

    if selected_player == 'Todos':
        st.dataframe(display_df)

        st.subheader("Comparativa entre jugadores")
        selected_chart_metric = st.selectbox("Selecciona una métrica para comparar", list(selected_metrics.keys()))

        # Comparación total por jugador
        sorted_df = display_df.sort_values(by=selected_chart_metric, ascending=False)
        fig_total = px.bar(
            sorted_df,
            x='Player Name',
            y=selected_chart_metric,
            text=sorted_df[selected_chart_metric].round(2),
            title=f"{selected_chart_metric} por jugador (Total)"
        )
        fig_total.update_traces(textposition='inside')
        fig_total.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_total)

        # Comparación por tiempos (solo para métricas que están en el dataframe por Period)
        st.subheader(f"{selected_chart_metric} por jugador (1T vs 2T)")
        col_name = selected_metrics[selected_chart_metric]
        first = first_half.groupby('Player Name')[col_name].mean().reset_index(name='1T')
        second = second_half.groupby('Player Name')[col_name].mean().reset_index(name='2T')
        merged = pd.merge(first, second, on='Player Name')
        merged['Total'] = merged['1T'] + merged['2T']
        merged = merged.sort_values(by='Total', ascending=False)

        fig_split = go.Figure()
        fig_split.add_trace(go.Bar(
            x=merged['Player Name'],
            y=merged['1T'],
            name='1er Tiempo',
            marker_color='lightskyblue',
            text=[f"{v:.2f}" for v in merged['1T']],
            textposition='inside'
        ))
        fig_split.add_trace(go.Bar(
            x=merged['Player Name'],
            y=merged['2T'],
            name='2do Tiempo',
            marker_color='tomato',
            text=[f"{v:.2f}" for v in merged['2T']],
            textposition='inside'
        ))
        fig_split.update_layout(
            barmode='stack',
            xaxis_title='Jugador',
            yaxis_title=selected_chart_metric,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig_split)

else:
    st.info("Por favor, sube un archivo CSV para comenzar.")
