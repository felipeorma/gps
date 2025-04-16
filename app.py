import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import re
import base64
import os
from fpdf import FPDF

# Configuración de imagen
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_width = 700
pio.kaleido.scope.default_height = 500

st.set_page_config(layout="wide")

# Idioma
lang = st.sidebar.selectbox("Language / Idioma", ["English", "Español"])

# Traducción de etiquetas
labels = { ... }  # [copia el bloque de traducciones que ya tenías aquí]

# Definiciones de métricas
metric_definitions = {
    labels["distance"]: "Total distance covered during the match.",
    labels["tempo"]: "Distance covered at moderate intensity (~15–20 km/h).",
    labels["hsr"]: "Distance covered between 20 and 25 km/h.",
    labels["sprint"]: "Distance covered above 25 km/h.",
    labels["sprint_count"]: "Number of sprints above 25 km/h lasting at least 1s.",
    labels["max_speed"]: "Maximum speed reached during the match.",
    labels["acc"]: "Number of effective accelerations (>1.5 m/s²).",
    labels["dec"]: "Number of effective decelerations (<-1.5 m/s²).",
    labels["load"]: "Cumulative load based on all movement intensities.",
    labels["rhie"]: "Repeated high-intensity efforts (sprint, acc, dec)."
}

# Estilo neón
st.markdown("""
    <style>
        .metric-box {
            background: linear-gradient(135deg, #1a0000, #330000);
            color: #ff0033;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            margin: 6px;
            box-shadow: 0 0 12px #ff0033;
        }
        .metric-title {
            font-size: 16px;
            font-weight: bold;
            color: white;
        }
        .metric-value {
            font-size: 26px;
            font-weight: bold;
            color: white;
        }
        .stApp {
            background-image: linear-gradient(to right, #0d0d0d 0%, #1a1a1a 100%);
        }
    </style>
""", unsafe_allow_html=True)

# Función de gráfico
def neon_bar_chart(df, label, column):
    fig = go.Figure(go.Bar(
        x=df[column],
        y=df['Player Name'],
        orientation='h',
        text=df[column].round(1),
        textposition='outside',
        marker=dict(color='rgba(255, 0, 51, 0.7)'),
        hovertemplate=f'%{{y}}<br>{label}: %{{x}}<br>{metric_definitions.get(label, "")}'
    ))
    fig.update_layout(
        height=400,
        xaxis_title=label,
        yaxis_title=labels["player"],
        plot_bgcolor='#0d0d0d',
        paper_bgcolor='#0d0d0d',
        font=dict(color='white', size=12)
    )
    return fig

# Función para crear PDF
def generate_pdf(title, summary, avg_data, bar_charts=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(13, 13, 13)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    for k, v in summary.items():
        k_translated = labels.get(k, k)
        pdf.cell(0, 10, f"{k_translated}: {v}", ln=True, align='C')

    for cat, items in avg_data.items():
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"{labels['avg_of']} {cat}", ln=True, align='C')
        pdf.set_font("Arial", size=11)
        for label, val in items:
            pdf.cell(0, 8, f"{label}: {val:.1f}", ln=True, align='C')

    if bar_charts:
        for chart in bar_charts:
            try:
                path = chart.get("path")
                title = chart.get("title")
                if path and os.path.exists(path):
                    pdf.add_page()
                    pdf.set_fill_color(13, 13, 13)
                    pdf.rect(0, 0, 210, 297, 'F')
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, title, ln=True, align='C')
                    pdf.image(path, x=25, w=160)
                    os.remove(path)
            except Exception as e:
                pdf.cell(0, 10, f"Chart error: {e}", ln=True)

    # Añadir definiciones al final
    pdf.add_page()
    pdf.set_fill_color(13, 13, 13)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Metric Definitions", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for label, definition in metric_definitions.items():
        pdf.multi_cell(0, 6, f"{label}: {definition}")

    return pdf.output(dest='S').encode('latin-1')

# Filtros y carga de archivos
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

    st.title(f"{labels['title']} - {jugador if jugador != labels['all'] else ''} {('| ' + partido) if partido != labels['all'] else ''}")

    if not df.empty:
        columns_exist = [v for v in metrics.values() if v in df.columns]
        df[columns_exist] = df[columns_exist].apply(pd.to_numeric, errors='coerce')
        df_grouped = df.groupby('Player Name')[columns_exist].mean().reset_index()

        st.subheader(f"{labels['averages']}: {jugador}" if jugador != labels["all"] else labels['averages'])

        grouped_metrics = {
            labels["Carga"]: [labels["load"]],
            labels["Velocidad e Intensidad"]: [labels["max_speed"]],
            labels["Aceleración y Desaceleración"]: [labels["acc"], labels["dec"]],
            labels["Distancias"]: [labels["distance"], labels["tempo"], labels["hsr"], labels["sprint"], labels["sprint_count"]],
            labels["Esfuerzos Repetidos"]: [labels["rhie"]]
        }

        if st.button(labels["create_pdf"]):
            resumen = {"Partido": partido, "Fecha": df['Fecha CSV'].iloc[0], "Jugador": jugador}
            resumen_avg = {}
            for group, keys in grouped_metrics.items():
                items = []
                for k in keys:
                    col_key = metrics.get(k)
                    if col_key in df_grouped.columns:
                        val = df_grouped[col_key].mean()
                        if not pd.isna(val) and val != 0:
                            items.append((k, val))
                if items:
                    resumen_avg[group] = items

            bar_chart_images = []
            for group, keys in grouped_metrics.items():
                for k in keys:
                    if k in metrics and metrics[k] in df.columns:
                        chart_df = df.groupby('Player Name')[metrics[k]].sum().reset_index().sort_values(metrics[k], ascending=True)
                        fig = neon_bar_chart(chart_df, k, metrics[k])
                        safe_group = re.sub(r'[^\w\-]', '_', group)
                        safe_k = re.sub(r'[^\w\-]', '_', k)
                        image_path = f"bar_chart_{safe_group}_{safe_k}.png"
                        try:
                            fig.write_image(image_path)
                            bar_chart_images.append({"path": image_path, "title": f"{group} - {k}"})
                        except Exception as e:
                            st.warning(f"No se pudo guardar la imagen para {k}: {e}")

            pdf_bytes = generate_pdf(labels["pdf_title"], resumen, resumen_avg, bar_charts=bar_chart_images)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{labels["pdf_file"]}">{labels["download_pdf"]}</a>'
            st.markdown(href, unsafe_allow_html=True)

        for group, keys in grouped_metrics.items():
            st.markdown(f"### {labels['avg_of']} {group}")
            metric_items = [(k, metrics[k]) for k in keys if k in metrics and metrics[k] in df_grouped.columns]
            for i in range(0, len(metric_items), 4):
                metric_cols = st.columns(4)
                for j, (k, v) in enumerate(metric_items[i:i+4]):
                    avg = df_grouped[v].mean()
                    if not pd.isna(avg) and avg != 0:
                        definition = metric_definitions.get(k, "")
                        metric_cols[j].markdown(f"""
                            <div class='metric-box'>
                                <div class='metric-title'>{k}</div>
                                <div class='metric-value'>{avg:.0f}</div>
                                <div style='font-size:10px; color:#bbb;'>{definition}</div>
                            </div>
                        """, unsafe_allow_html=True)

        st.divider()

        for k, v in metrics.items():
            if v in df.columns:
                st.subheader(k)
                if k in metric_definitions:
                    with st.expander("¿Qué significa esta métrica?"):
                        st.markdown(metric_definitions[k])
                chart_df = df.groupby('Player Name')[v].sum().reset_index().sort_values(v, ascending=True)
                fig = neon_bar_chart(chart_df, k, v)
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Cargue uno o más archivos CSV para comenzar / Upload one or more CSV files to begin.")
