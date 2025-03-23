import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os

# Cargar archivo CSV
st.sidebar.header("Carga de datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo del partido (.csv)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, delimiter=';')
    df.columns = df.columns.str.strip()

    # Extraer fecha desde nombre del archivo si no está en el contenido
    file_name = uploaded_file.name
    fecha_csv = pd.to_datetime(uploaded_file.name.split('_')[-3:], errors='coerce').strftime('%Y-%m-%d') if '_' in uploaded_file.name else 'Sin Fecha'
    df['Fecha CSV'] = fecha_csv

    raw_name = df['Period Name'].iloc[0] if 'Period Name' in df.columns else "Partido 1"
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
    st.sidebar.caption(f"Fecha del archivo: {fecha_csv}")

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
    first_half = full_df[full_df['Period Number'] == 1]
    second_half = full_df[full_df['Period Number'] == 2]

    st.subheader("Promedios de Jugador(es)")

    if selected_player == 'Todos':
        display_df = full_df[['Player Name'] + list(selected_metrics.values())].copy()
        display_df = display_df.rename(columns={v: k for k, v in selected_metrics.items()})

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
        st.dataframe(display_df)

        st.subheader("Comparativa entre jugadores")
        selected_chart_metric = st.selectbox("Selecciona una métrica para comparar", list(selected_metrics.keys()))

        sorted_df = display_df.sort_values(by=selected_chart_metric, ascending=False)
        fig_total = px.bar(
            sorted_df,
            x='Player Name',
            y=selected_chart_metric,
            text=sorted_df[selected_chart_metric].round(2),
            title=f"{selected_chart_metric} por jugador (Total)"
        )
        fig_total.update_traces(textposition='outside')
        fig_total.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_total)

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
            textposition='outside'
        ))
        fig_split.add_trace(go.Bar(
            x=merged['Player Name'],
            y=merged['2T'],
            name='2do Tiempo',
            marker_color='tomato',
            text=[f"{v:.2f}" for v in merged['2T']],
            textposition='outside'
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
        player_data = full_df[full_df['Player Name'] == selected_player]
        st.subheader(f"Promedios de {selected_player}")

        selected_player_metric = st.selectbox("Selecciona una métrica para el jugador", list(selected_metrics.keys()))
        col_name = selected_metrics[selected_player_metric]

        player_first = player_data[player_data['Period Number'] == 1][col_name].mean()
        player_second = player_data[player_data['Period Number'] == 2][col_name].mean()
        total = player_first + player_second

        fig_player = go.Figure()
        fig_player.add_trace(go.Bar(
            x=[selected_player],
            y=[player_first],
            name='1er Tiempo',
            marker_color='lightskyblue',
            text=[f"{player_first:.2f}"],
            textposition='none'
        ))
        fig_player.add_trace(go.Bar(
            x=[selected_player],
            y=[player_second],
            name='2do Tiempo',
            marker_color='tomato',
            text=[f"{player_second:.2f}"],
            textposition='none'
        ))
        fig_player.update_layout(
            barmode='stack',
            title=f"{selected_player_metric} - {selected_player} (Total: {total:.2f})",
            yaxis_title=selected_player_metric,
            showlegend=True,
            annotations=[
                dict(
                    x=selected_player,
                    y=total,
                    text=f"Total: {total:.2f}",
                    showarrow=False,
                    yshift=10
                )
            ]
        )
        st.plotly_chart(fig_player)

        st.caption(f"Fecha del partido: {fecha_csv}")

else:
    st.info("Por favor, sube un archivo CSV para comenzar.")

