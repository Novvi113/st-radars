import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

# ==========================================
# 1. НАСТРОЙКИ И ЗАГРУЗКА
# ==========================================
st.set_page_config(page_title="Football Analytics Hub", layout="wide")

# Файлы данных (из твоего скриншота)
FILES = {
    "Players": "Top5PlayerData202526.csv",
    "Teams": "Top5TeamData202526.csv"
}

@st.cache_data
def load_csv(file_path):
    """Универсальная функция загрузки CSV"""
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')
        
        # Убираем пробелы в именах колонок
        df.columns = [c.strip() for c in df.columns]
        return df
    except FileNotFoundError:
        return None

def get_percentile(val, array):
    """Расчет процентиля (0-100)"""
    if pd.isna(val): return 0
    return int(stats.percentileofscore(array, val))

# ==========================================
# 2. ВКЛАДКА: MATCH ANALYSIS (КОМАНДЫ)
# ==========================================
def render_match_analysis():
    st.header("⚽ Match Analysis (Team Stats)")
    
    # Загружаем данные команд
    df = load_csv(FILES["Teams"])
    if df is None:
        st.error(f"❌ File '{FILES['Teams']}' not found. Check file name.")
        return

    # Фильтры
    st.sidebar.header("🏆 Match Filters")
    
    # Поиск лиги
    league_col = 'Comp' if 'Comp' in df.columns else 'League' if 'League' in df.columns else None
    if league_col:
        leagues = sorted(df[league_col].unique().astype(str))
        sel_league = st.sidebar.selectbox("Select League (Teams)", leagues)
        df = df[df[league_col] == sel_league]

    teams = sorted(df['Squad'].unique()) if 'Squad' in df.columns else sorted(df['Team'].unique())
    
    # Выбор команд
    c1, c2 = st.columns(2)
    t1 = c1.selectbox("Home Team", teams, index=0)
    remaining = [t for t in teams if t != t1]
    t2 = c2.selectbox("Away Team", remaining, index=0)

    # Статистика
    st.subheader(f"📊 {t1} vs {t2}")
    
    # Находим строки команд
    team_col = 'Squad' if 'Squad' in df.columns else 'Team'
    row1 = df[df[team_col] == t1].iloc[0]
    row2 = df[df[team_col] == t2].iloc[0]

    # Выбираем основные метрики для сравнения
    # (Берем числовые колонки, исключаем лишнее)
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    ignore = ['Rk', '# Pl', 'Age', 'Poss']
    metrics = [c for c in numeric if c not in ignore][:8] # Берем первые 8 метрик
    
    # Строим таблицу сравнения
    data = {
        "Metric": metrics,
        f"{t1}": [row1[m] for m in metrics],
        f"{t2}": [row2[m] for m in metrics],
        "Diff": [row1[m] - row2[m] for m in metrics]
    }
    st.dataframe(pd.DataFrame(data).style.format(precision=2), use_container_width=True, hide_index=True)

# ==========================================
# 3. ВКЛАДКА: PLAYER COMPARISON (РАДАР)
# ==========================================
def render_player_comparison():
    st.header("⚔️ Player Comparison (Radars)")

    # Загружаем игроков
    df = load_csv(FILES["Players"])
    if df is None:
        st.error(f"❌ File '{FILES['Players']}' not found.")
        return

    st.sidebar.divider()
    st.sidebar.header("👤 Player Filters")

    # Лига
    league_col = 'Comp' if 'Comp' in df.columns else 'League' if 'League' in df.columns else None
    if league_col:
        leagues = sorted(df[league_col].unique().astype(str))
        sel_league = st.sidebar.selectbox("Select League (Players)", leagues)
        df_filtered = df[df[league_col] == sel_league]
    else:
        df_filtered = df

    # Позиция
    if 'Pos' in df_filtered.columns:
        positions = sorted(df_filtered['Pos'].unique().astype(str))
        sel_pos = st.sidebar.multiselect("Filter Position", positions, default=positions[:1] if positions else None)
        if sel_pos:
            df_filtered = df_filtered[df_filtered['Pos'].isin(sel_pos)]

    # Игроки
    players = df_filtered['Player'].unique()
    if len(players) == 0:
        st.warning("No players found.")
        return

    c1, c2 = st.columns(2)
    p1 = c1.selectbox("Player 1", players, index=0)
    rem = [p for p in players if p != p1]
    p2 = c2.selectbox("Player 2", rem if rem else ["N/A"], index=0)

    # Метрики
    nums = df.select_dtypes(include=[np.number]).columns.tolist()
    ignore = ['Rk', 'Age', 'Born', 'Matches', 'Starts', 'Mins', '90s']
    avail_metrics = [c for c in nums if c not in ignore]
    
    st.sidebar.subheader("Radar Metrics")
    sel_metrics = st.sidebar.multiselect("Choose Metrics", avail_metrics, default=avail_metrics[:6] if len(avail_metrics)>6 else avail_metrics)

    if len(sel_metrics) < 3:
        st.warning("⚠️ Select at least 3 metrics.")
        return

    # Данные для графика
    row1 = df[df['Player'] == p1].iloc[0]
    row2 = df[df['Player'] == p2].iloc[0]

    vals1, vals2 = [], [] # Процентили
    raw1, raw2 = [], []   # Числа

    for m in sel_metrics:
        # Считаем процентиль относительно отфильтрованной базы (например, среди всех нападающих)
        pop = df_filtered[m].dropna()
        vals1.append(get_percentile(row1[m], pop))
        vals2.append(get_percentile(row2[m], pop))
        raw1.append(row1[m])
        raw2.append(row2[m])

    # Замыкаем
    vals1 += [vals1[0]]
    vals2 += [vals2[0]]
    raw1 += [raw1[0]]
    raw2 += [raw2[0]]
    theta = sel_metrics + [sel_metrics[0]]

    # Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=theta, fill='toself', name=p1,
        line=dict(color='#00F0FF', width=3), fillcolor='rgba(0, 240, 255, 0.3)',
        hovertemplate="Rank: %{r}%<br>Val: %{customdata}", customdata=raw1
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=theta, fill='toself', name=p2,
        line=dict(color='#FF0055', width=3), fillcolor='rgba(255, 0, 85, 0.3)',
        hovertemplate="Rank: %{r}%<br>Val: %{customdata}", customdata=raw2
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
        margin=dict(t=40, b=40),
        legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Таблица
    st.divider()
    res = pd.DataFrame({
        "Metric": sel_metrics,
        f"{p1}": [row1[m] for m in sel_metrics],
        f"{p2}": [row2[m] for m in sel_metrics],
        "Diff": [row1[m] - row2[m] for m in sel_metrics]
    })
    st.dataframe(res.style.background_gradient(cmap="RdBu", subset=['Diff']), use_container_width=True, hide_index=True)

# ==========================================
# 4. MAIN (ЗАПУСК)
# ==========================================
def main():
    st.title("⚽ Football Data Hub 2025/26")
    
    tab1, tab2 = st.tabs(["📊 Match Analysis", "⚔️ Player Comparison"])
    
    with tab1:
        render_match_analysis()
        
    with tab2:
        render_player_comparison()

if __name__ == "__main__":
    main()