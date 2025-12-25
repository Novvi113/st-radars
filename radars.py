import streamlit as st
import pandas as pd
import numpy as np
from mplsoccer import PyPizza
from scipy import stats

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Сравнение Игроков", layout="wide")

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    file_path = 'Top5PlayerData202526.csv'
    try:
        df = pd.read_csv(file_path, encoding='latin1')
    except:
        df = pd.read_csv(file_path)
    
    # Очистка имен колонок
    df.columns = [c.strip() for c in df.columns]
    return df

# --- РАСЧЕТ ПРОЦЕНТИЛЕЙ ---
def calculate_percentile(val, array):
    if pd.isna(val):
        return 0
    return stats.percentileofscore(array, val)

# --- ГЛАВНАЯ ЧАСТЬ ---
def main():
    st.header("⚔️ Сравнение Игроков (Radars)")
    
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("Файл Top5PlayerData202526.csv не найден!")
        return

    # --- 1. ВЫБОР ИГРОКОВ ---
    col1, col2 = st.columns(2)
    
    # Фильтр позиций
    if 'Pos' in df.columns:
        all_positions = df['Pos'].unique().tolist()
        pos_filter = st.sidebar.multiselect("Фильтр позиций", all_positions, default=all_positions[:1])
        if pos_filter:
            df_filtered = df[df['Pos'].isin(pos_filter)]
        else:
            df_filtered = df
    else:
        df_filtered = df

    players_list = df_filtered['Player'].unique()
    
    with col1:
        p1 = st.selectbox("Игрок 1", players_list, index=0)
    with col2:
        remaining = [p for p in players_list if p != p1]
        p2 = st.selectbox("Игрок 2", remaining if remaining else ["Нет данных"], index=0)

    # --- 2. ВЫБОР МЕТРИК ---
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Исключаем технические колонки
    ignore = ['Rk', 'Age', 'Born', 'Matches', 'Starts', 'Mins', '90s'] 
    stats_cols = [c for c in numeric_cols if c not in ignore]
    
    st.sidebar.header("Настройки Радара")
    default_metrics = stats_cols[:6] if len(stats_cols) > 6 else stats_cols
    params = st.sidebar.multiselect("Выберите метрики", stats_cols, default=default_metrics)

    if len(params) < 3:
        st.warning("⚠️ Выберите минимум 3 метрики в меню слева.")
        return

    # --- 3. ПОДГОТОВКА ДАННЫХ ---
    p1_data = df[df['Player'] == p1].iloc[0]
    p2_data = df[df['Player'] == p2].iloc[0]

    p1_vals = []
    p2_vals = []

    for p in params:
        col_values = df_filtered[p].dropna()
        p1_vals.append(int(calculate_percentile(p1_data[p], col_values)))
        p2_vals.append(int(calculate_percentile(p2_data[p], col_values)))

    # --- 4. ОТРИСОВКА ---
    st.subheader(f"{p1} vs {p2}")

    # Создаем пиццу
    baker = PyPizza(
        params=params,
        background_color="#0E1117",
        straight_line_color="#EBEBEB",
        straight_line_lw=1,
        last_circle_lw=0,
        other_circle_lw=0,
        inner_circle_size=20
    )

    fig, ax = baker.make_pizza(
        p1_vals,
        compare_values=p2_vals,
        figsize=(8, 8),
        color_blank_root=None,
        slice_colors=["#1A78CF"] * len(params),
        kwargs_slices=dict(edgecolor="#F2F2F2", zorder=2, linewidth=1),
        kwargs_compare=dict(facecolor="#FF4B4B", edgecolor="#222222", zorder=3, alpha=0.5, linewidth=2),
    )

    # Подписи (без использования FontManager)
    fig.text(0.5, 0.97, f"{p1} vs {p2}", size=16, ha="center", color="#F2F2F2", fontweight='bold')
    fig.text(0.5, 0.93, "Сравнение процентилей", size=11, ha="center", color="#F2F2F2")
    
    # Легенда
    fig.text(0.25, 0.02, f"🟦 {p1}", size=12, color="#1A78CF", ha="center", fontweight='bold')
    fig.text(0.75, 0.02, f"🟥 {p2}", size=12, color="#FF4B4B", ha="center", fontweight='bold')

    fig.set_facecolor('#0E1117')
    st.pyplot(fig)

    # --- 5. ТАБЛИЦА ---
    with st.expander("Точные цифры"):
        st.dataframe(df[df['Player'].isin([p1, p2])][['Player'] + params].set_index('Player').T)

if __name__ == "__main__":
    main()


