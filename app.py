import streamlit as st
import pandas as pd
import plotly.express as px

# Título principal sin emojis para evitar UnicodeEncodeError
st.title("Dashboard GPS - Cavalry FC")

# Cargar archivo CSV
st.sidebar.header("Carga de datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo del partido (.csv)", type=["csv"])

if uploaded_file:
    # Leer el archivo con separador ;
    df = pd.read_csv(uploaded_file, delimiter=';')

    # Mostrar info general
    st.sidebar.success("Archivo cargado exitosamente")
    st.sidebar.write("Partido 1")

    # Resultado del partido (entrada manual)
    match_result = st.sidebar.text_input("Resultado del partido", value="Cavalry FC vs Comerciantes Unidos 2-1")

    # Lista de jugadores
    player_list = ['Todos'] + sorted(df['Player Name'].unique())
    selected_player = st.sidebar.selectbox("Selecciona un jugador", player_list)

    # Métricas a mostrar
    selected_metrics = {
        'Distancia Total (m)': ' Work Rate Total Dist',
        'Carga de Aceleración': ' Acceleration Load',
        'Velocidad Máxima (m/s)': 'Max Velocity [ Per Max ]',
        'Aceleraciones Altas': 'Acc3 Eff (Gen2)',
        'Aceleraciones Medias': 'Acc2 Eff (Gen2)',
        'Aceleraciones Bajas': 'Acc1 Eff (Gen2)',
        'Deceleraciones Altas': 'Dec3 Eff (Gen2)',
        'Deceleraciones Medias': 'Dec2 Eff (Gen2)',
        'Deceleraciones Bajas': 'Dec1 Eff (Gen2)'
    }

    # Crear tabla resumen con métricas seleccionadas (solo para totales)
    full_df = df.copy()
    display_df = full_df[['Player Name'] + list(selected_metrics.values())].copy()
    display_df = display_df.rename(columns={v: k for k, v in selected_metrics.items()})

    # Mostrar resultado del partido
    st.subheader(f"Resultado del Partido: {match_result}")

    # Mostrar KPIs por periodos
    st.subheader("Promedios de Jugador(es)")
    first_half = full_df[full_df['Period Number'] == 1]
    second_half = full_df[full_df['Period Number'] == 2]

    col1, col2, col3 = st.columns(3)
    col1.metric("Distancia Total Promedio (m) - Total", round(display_df['Distancia Total (m)'].mean(), 1))
    col2.metric("1er Tiempo", round(first_half[' Work Rate Total Dist'].mean(), 1))
    col3.metric("2do Tiempo", round(second_half[' Work Rate Total Dist'].mean(), 1))

    col1.metric("Carga Aceleración Promedio - Total", round(display_df['Carga de Aceleración'].mean(), 1))
    col2.metric("1er Tiempo", round(first_half[' Acceleration Load'].mean(), 1))
    col3.metric("2do Tiempo", round(second_half[' Acceleration Load'].mean(), 1))

    col1.metric("Velocidad Máxima Promedio - Total", round(display_df['Velocidad Máxima (m/s)'].mean(), 2))
    col2.metric("1er Tiempo", round(first_half['Max Velocity [ Per Max ]'].mean(), 2))
    col3.metric("2do Tiempo", round(second_half['Max Velocity [ Per Max ]'].mean(), 2))

    st.divider()

    # Mostrar tabla si se selecciona un jugador específico
    if selected_player != 'Todos':
        player_data = full_df[full_df['Player Name'] == selected_player]
        player_display = player_data[['Player Name'] + list(selected_metrics.values())].copy()
        player_display = player_display.rename(columns={v: k for k, v in selected_metrics.items()})
        st.dataframe(player_display)

        # Gráfico radar
        radar_data = player_display.set_index('Player Name').T.reset_index()
        radar_data.columns = ['Métrica', 'Valor']

        fig = px.line_polar(radar_data, r='Valor', theta='Métrica', line_close=True,
                            title=f"Perfil Físico - {selected_player}")
        st.plotly_chart(fig)

    # Mostrar tabla completa si se seleccionan todos
    if selected_player == 'Todos':
        st.dataframe(display_df)

        st.subheader("Comparativa entre jugadores")
        metric_to_plot = st.selectbox("Selecciona la métrica para comparar", list(selected_metrics.keys()))

        sorted_df = display_df.sort_values(by=metric_to_plot, ascending=False)
        fig_bar = px.bar(sorted_df, x='Player Name', y=metric_to_plot, text=metric_to_plot,
                         title=f"{metric_to_plot} por jugador (ordenado)")
        fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='inside')
        fig_bar.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_bar)

else:
    st.info("Por favor, sube un archivo CSV para comenzar.")

