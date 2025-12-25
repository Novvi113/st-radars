import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Сравнение Игроков", layout="wide")

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    file_path = 'Top5PlayerData202526.csv'
    # Пытаемся прочитать в разных кодировках, чтобы имена (Iñigo) были нормальными
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin1')
    
    # Чистим пробелы в названиях колонок
    df.columns = [c.strip() for c in df.columns]
    return df

# --- РАСЧЕТ ПРОЦЕНТИЛЕЙ (0-99) ---
def get_percentile(val, array):
    if pd.isna(val): return 0
    return int(stats.percentileofscore(array, val))

# --- ГЛАВНАЯ ЧАСТЬ ---
def main():
    # Стиль заголовка
    st.markdown("""
        <h1 style='text-align: center; color: #fff;'>⚔️ PRO PLAYER COMPARISON</h1>
    """, unsafe_allow_html=True)

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("❌ Файл Top5PlayerData202526.csv не найден!")
        return

    # --- 1. ФИЛЬТРЫ И ВЫБОР ---
    st.sidebar.header("🔍 Настройки поиска")
    
    # Фильтр позиций
    if 'Pos' in df.columns:
        positions = df['Pos'].unique().tolist()
        selected_pos = st.sidebar.multiselect("Позиция", positions, default=positions[:1])
        if selected_pos:
            df_filtered = df[df['Pos'].isin(selected_pos)]
        else:
            df_filtered = df
    else:
        df_filtered = df

    # Выбор игроков
    col1, col2 = st.columns(2)
    players = df_filtered['Player'].unique()
    
    if len(players) == 0:
        st.error("Нет игроков с выбранной позицией.")
        return

    with col1:
        p1 = st.selectbox("🔷 Игрок 1", players, index=0)
    with col2:
        # Убираем первого из списка второго
        others = [p for p in players if p != p1]
        p2 = st.selectbox("🔶 Игрок 2", others if others else ["Нет данных"], index=0)

    # --- 2. МЕТРИКИ ---
    # Только числа
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    ignore = ['Rk', 'Age', 'Born', 'Matches', 'Starts', 'Mins', '90s']
    metrics = [c for c in numeric_cols if c not in ignore]

    st.sidebar.subheader("📊 Параметры радара")
    # Дефолтные метрики (первые 6)
    selected_metrics = st.sidebar.multiselect("Метрики", metrics, default=metrics[:6])

    if len(selected_metrics) < 3:
        st.warning("⚠️ Выбери минимум 3 метрики.")
        return

    # --- 3. ПОДГОТОВКА ДАННЫХ ---
    p1_row = df[df['Player'] == p1].iloc[0]
    p2_row = df[df['Player'] == p2].iloc[0]

    p1_vals = []
    p2_vals = []
    p1_raw = [] # Реальные цифры для тултипа
    p2_raw = []

    for m in selected_metrics:
        col_data = df_filtered[m].dropna()
        # Считаем ранг (0-100)
        p1_vals.append(get_percentile(p1_row[m], col_data))
        p2_vals.append(get_percentile(p2_row[m], col_data))
        # Сохраняем реальные значения
        p1_raw.append(p1_row[m])
        p2_raw.append(p2_row[m])

    # Замыкаем круг для Plotly Radar
    p1_vals.append(p1_vals[0])
    p2_vals.append(p2_vals[0])
    p1_raw.append(p1_raw[0])
    p2_raw.append(p2_raw[0])
    metrics_cyclic = selected_metrics + [selected_metrics[0]]

    # --- 4. РИСУЕМ КРАСИВЫЙ РАДАР (PLOTLY) ---
    fig = go.Figure()

    # Игрок 1
    fig.add_trace(go.Scatterpolar(
        r=p1_vals,
        theta=metrics_cyclic,
        fill='toself',
        name=p1,
        line=dict(color='#00F0FF', width=3), # Неоновый голубой
        fillcolor='rgba(0, 240, 255, 0.3)',  # Прозрачный голубой
        customdata=p1_raw,
        hovertemplate="<b>%{theta}</b><br>Ранг: %{r}%<br>Значение: %{customdata}<extra></extra>"
    ))

    # Игрок 2
    fig.add_trace(go.Scatterpolar(
        r=p2_vals,
        theta=metrics_cyclic,
        fill='toself',
        name=p2,
        line=dict(color='#FF0055', width=3), # Неоновый розовый/красный
        fillcolor='rgba(255, 0, 85, 0.3)',   # Прозрачный красный
        customdata=p2_raw,
        hovertemplate="<b>%{theta}</b><br>Ранг: %{r}%<br>Значение: %{customdata}<extra></extra>"
    ))

    # Настройки дизайна
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False, # Скрываем цифры оси 0-100, чтобы не засорять
                linecolor='rgba(255,255,255,0.2)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            angularaxis=dict(
                linecolor='rgba(255,255,255,0.2)',
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(size=11, color="white")
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)', # Прозрачный фон
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=80, r=80, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 5. ТАБЛИЦА СРАВНЕНИЯ ---
    st.divider()
    st.markdown("### 📋 Детальная статистика")
    
    # Красивая таблица
    compare_df = pd.DataFrame({
        'Metric': selected_metrics,
        f'{p1}': [p1_row[m] for m in selected_metrics],
        f'{p2}': [p2_row[m] for m in selected_metrics],
        f'Разница': [p1_row[m] - p2_row[m] for m in selected_metrics]
    })
    
    # Форматирование таблицы
    st.dataframe(
        compare_df.style.background_gradient(cmap="RdBu", subset=['Разница']),
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()