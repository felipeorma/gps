import streamlit as st
import pandas as pd
import plotly.express as px

# Título principal
st.title("🏀 Dashboard GPS - Deportivo Garcilazo")

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
    match_result = st.sidebar.text_input("Resultado del partido", value="Garcilazo vs Comerciantes Unidos 2-1")

    # Lista de jugadores
    player_list = ['Todos'] + sorted(df['Player Name'].unique())
    selected_player = st.sidebar.selectbox("Selecciona un jugador", player_list)

    # Filtrar jugador si aplica
    if selected_player != 'Todos':
        df = df[df['Player Name'] == selected_player]

    # Mostrar resultado del partido
    st.subheader(f"Resultado del Partido: {match_result}")

    # Métricas a mostrar
    st.subheader("🔢 Estadísticas GPS del partido")
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

    # Crear tabla resumen con métricas seleccionadas
    display_df = df[['Player Name'] + list(selected_metrics.values())].copy()
    display_df = display_df.rename(columns={v: k for k, v in selected_metrics.items()})

    # Mostrar KPIs en tarjetas
    st.subheader("Promedios del equipo")
    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        st.metric("Distancia Total Promedio (m)", round(display_df['Distancia Total (m)'].mean(), 1))
        st.metric("Carga Aceleración Promedio", round(display_df['Carga de Aceleración'].mean(), 1))
    with kpi_cols[1]:
        st.metric("Velocidad Máxima Promedio (m/s)", round(display_df['Velocidad Máxima (m/s)'].mean(), 2))
        st.metric("Aceleraciones Altas Promedio", round(display_df['Aceleraciones Altas'].mean(), 1))
    with kpi_cols[2]:
        st.metric("Deceleraciones Altas Promedio", round(display_df['Deceleraciones Altas'].mean(), 1))
        st.metric("Aceleraciones Bajas Promedio", round(display_df['Aceleraciones Bajas'].mean(), 1))

    st.divider()
    st.dataframe(display_df)

    # Gráfico radar por jugador (solo si no está seleccionado 'Todos')
    if selected_player != 'Todos':
        radar_data = display_df.set_index('Player Name').T.reset_index()
        radar_data.columns = ['Métrica', 'Valor']

        fig = px.line_polar(radar_data, r='Valor', theta='Métrica', line_close=True,
                            title=f"Perfil Físico - {selected_player}")
        st.plotly_chart(fig)

else:
    st.info("Por favor, sube un archivo CSV para comenzar.")

