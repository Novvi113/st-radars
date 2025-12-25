import streamlit as st
import pandas as pd
import numpy as np
from mplsoccer import PyPizza, FontManager
from scipy import stats

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Тест Нового Радара", layout="wide")

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    # Пытаемся прочитать твой файл
    file_path = 'Top5PlayerData202526.csv'
    try:
        df = pd.read_csv(file_path, encoding='latin1')
    except:
        df = pd.read_csv(file_path)
    
    # Очистка имен колонок от пробелов
    df.columns = [c.strip() for c in df.columns]
    return df

# --- РАСЧЕТ ПРОЦЕНТИЛЕЙ ---
def calculate_percentile(val, array):
    # Если значение NaN, возвращаем 0
    if pd.isna(val):
        return 0
    return stats.percentileofscore(array, val)

# --- ГЛАВНАЯ ЧАСТЬ ---
def main():
    st.header("🧪 Тест новой вкладки: Сравнение Игроков")
    
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("Файл Top5PlayerData202526.csv не найден. Проверь, лежит ли он в той же папке.")
        return

    # --- 1. ВЫБОР ИГРОКОВ ---
    col1, col2 = st.columns(2)
    
    # Фильтр по позиции (чтобы не сравнивать вратаря с нападающим)
    if 'Pos' in df.columns:
        all_positions = df['Pos'].unique().tolist()
        pos_filter = st.multiselect("Фильтр позиций", all_positions, default=all_positions[:1])
        if pos_filter:
            df_filtered = df[df['Pos'].isin(pos_filter)]
        else:
            df_filtered = df
    else:
        df_filtered = df

    with col1:
        # Список игроков
        players_list = df_filtered['Player'].unique()
        p1 = st.selectbox("Игрок 1", players_list, index=0)
    
    with col2:
        # Исключаем первого игрока из списка второго
        remaining = [p for p in players_list if p != p1]
        if not remaining: 
            remaining = ["Нет данных"]
        p2 = st.selectbox("Игрок 2", remaining, index=0)

    # --- 2. ВЫБОР ПАРАМЕТРОВ ---
    # Берем только числовые колонки
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    ignore = ['Rk', 'Age', 'Born', 'Matches', 'Starts', 'Mins', '90s', 'Goals', 'Assists'] 
    # Goals и Assists часто лучше убрать из радара, если там есть xG и xA, или оставить - на твой вкус.
    # Я оставил фильтрацию базовых служебных полей.
    
    stats_cols = [c for c in numeric_cols if c not in ignore]
    
    st.sidebar.header("Настройки Радара")
    # Выбираем 5 дефолтных метрик, если они есть
    default_metrics = stats_cols[:6] if len(stats_cols) > 6 else stats_cols
    params = st.sidebar.multiselect("Выберите метрики", stats_cols, default=default_metrics)

    if len(params) < 3:
        st.warning("⚠️ Выбери хотя бы 3 метрики в меню слева (стрелочка > вверху слева).")
        return

    # --- 3. ПОДГОТОВКА ДАННЫХ ---
    # Получаем данные игроков
    p1_data = df[df['Player'] == p1].iloc[0]
    p2_data = df[df['Player'] == p2].iloc[0]

    p1_vals = []
    p2_vals = []

    # Превращаем сырые числа в процентили (0-100)
    for p in params:
        col_values = df_filtered[p].dropna() # Берем колонку для сравнения с остальными
        
        val1 = p1_data[p]
        val2 = p2_data[p]
        
        pct1 = int(calculate_percentile(val1, col_values))
        pct2 = int(calculate_percentile(val2, col_values))
        
        p1_vals.append(pct1)
        p2_vals.append(pct2)

    # --- 4. РИСУЕМ ГРАФИК (MPLSOCCER) ---
    st.subheader(f"{p1} (Синий) vs {p2} (Красный)")
    
    # Шрифты для красоты
    font_normal = FontManager('https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto-Regular.ttf')
    
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
    
    # Легенда
    fig.text(0.5, 0.02, "Сравнение по процентилям (среди выбранной позиции)", color="#F2F2F2", ha="center", fontproperties=font_normal.prop, size=10)
    fig.set_facecolor('#0E1117')

    st.pyplot(fig)

    # --- 5. ТАБЛИЦА ЦИФР ---
    with st.expander("Посмотреть точные цифры"):
        st.write(df[df['Player'].isin([p1, p2])][['Player'] + params])

if __name__ == "__main__":
    main()




