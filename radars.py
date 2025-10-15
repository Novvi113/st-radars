#Loading packages
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from mplsoccer import Radar, grid
import matplotlib.pyplot as plt
import io

#Loading Data
@st.cache_data
def get_player_df():
    return pd.read_csv("PlayerDataTest.csv")

@st.cache_data
def get_team_df():
    return pd.read_csv("TeamDataTest.csv")

player_df = get_player_df()
team_df = get_team_df()

#Data cleaning and transformation
team_data = team_df[team_df["Team_or_Opponent"] == "team"]
team_data["Comp"] = team_df["Competition_Name"]
df = pd.merge(player_df, team_data[["Season_End_Year", "Comp", "Squad", "Poss"]], how="left", on=["Season_End_Year", "Comp", "Squad"])

#leagues without advanced data
leagues_to_drop = ["LaLiga2", "2.Bundesliga", "Ligue 2"]
df = df[~df["Comp"].isin(leagues_to_drop)]

#Function to convert to per 90
def to_per_90(metric, mins_per_90 = df["Mins_Per_90"]):
    return metric/mins_per_90


#Function to possession adjust
def poss_adj(metric, poss = df["Poss"]):
    return metric*(50/poss)

#Filtering out players without required minutes
df_clean = df[df["Min_Playing"] >= 100]

vars_to_90 = ["Touches_Touches", "Def Pen_Touches", "Def 3rd_Touches", "Mid 3rd_Touches", "Att 3rd_Touches", "Att Pen_Touches", "Live_Touches", "Att_Take", "Succ_Take", "Tkld_Take", "Carries_Carries", "TotDist_Carries", "PrgDist_Carries", "PrgC_Carries", "Final_Third_Carries", "CPA_Carries", "Mis_Carries", "Dis_Carries", "Rec_Receiving", "PrgR_Receiving", "Gls_Standard", "FK_Standard", "PK_Standard", "xG_Expected", "npxG_Expected", "G_minus_xG_Expected", "np:G_minus_xG_Expected", "Att", "Live_Pass", "Dead_Pass", "FK_Pass", "TB_Pass", "Sw_Pass", "Crs_Pass", "Off_Outcomes", "Blocks_Outcomes", "Cmp_Total", "Att_Total", "TotDist_Total", "PrgDist_Total", "Cmp_Short", "Att_Short", "Cmp_Medium", "Att_Medium", "Cmp_Long", "Att_Long", "Ast", "xAG", "xA_Expected", "A_minus_xAG_Expected", "KP", "Final_Third", "PPA", "CrsPA", "PrgP", "PassLive_SCA", "PassDead_SCA", "TO_SCA", "Sh_SCA", "Fld_SCA", "Def_SCA", "Fls", "Fld", "Off", "Crs", "TklW", "PKwon", "PKcon", "OG", "Recov", "Won_Aerial", "Lost_Aerial", "Def 3rd_Tackles", "Mid 3rd_Tackles", "Att 3rd_Tackles", "Tkl_Challenges", "Att_Challenges", "Lost_Challenges", "Blocks_Blocks", "Sh_Blocks", "Pass_Blocks", "Int", "Tkl+Int", "Clr", "Err"]

vars_to_padj = ["TklW", "PKcon", "Recov", "Def 3rd_Tackles", "Mid 3rd_Tackles", "Att 3rd_Tackles", "Tkl_Challenges", "Att_Challenges", "Lost_Challenges", "Blocks_Blocks", "Sh_Blocks", "Pass_Blocks", "Int", "Tkl+Int", "Clr", "Err"]

df_clean["xA_per_KP"] = np.where(df_clean["KP"] != 0, df_clean["xA_Expected"]/df_clean["KP"], 0)
df_clean["Att_Aerial"] = df_clean["Won_Aerial"] + df_clean["Lost_Aerial"]
df_clean["Sh_per_100_Touches"] =np.where(df_clean["Touches_Touches"] != 0, 100*df_clean["Sh_Standard"]/df_clean["Touches_Touches"], 0)
df_clean["PA_Touches_per_Sh"] = np.where(df_clean["Sh_Standard"] != 0, df_clean["Att Pen_Touches"]/df_clean["Sh_Standard"], df_clean["Att Pen_Touches"]/(df_clean["Sh_Standard"].max() + 1))


df_clean[vars_to_90] = df_clean[vars_to_90].apply(to_per_90, axis = 0)
df_clean[vars_to_padj] = df_clean[vars_to_padj].apply(poss_adj, axis = 0)
df_clean["Season_Start_Year"] = df_clean["Season_End_Year"] - 1
df_clean["Season"] = df_clean["Season_Start_Year"].astype(str).str[2:] + "/" + df_clean["Season_End_Year"].astype(str).str[2:]

st.title("Player Comparison Radar Tool")
st.markdown("""Use this tool to generate player comparison radars. Select two players and one of the four attribute groups, then click the "Download Viz" button below to save the graphic!""")



#Sidebar Header
st.sidebar.header("Choose Your Players!")

#Player 1 Selection
#Subheader
st.sidebar.subheader("Player 1")

#League Selection
p1_league_selection = st.sidebar.selectbox(label =  "League",
                                           options = df_clean["Comp"].unique(),
                                           placeholder= "Select league...",
                                           key = "P1_League")

p1_available_seasons = df_clean["Season"].loc[df_clean["Comp"] == p1_league_selection].unique()

#Season Selection
p1_season_selection = st.sidebar.selectbox(label = "Season",
                     options = p1_available_seasons,
                     placeholder = "Select season...",
                     key = "P1_Season")

p1_available_squads = df_clean["Squad"].loc[(df_clean["Comp"] == p1_league_selection) & (df_clean["Season"] == p1_season_selection)].unique()
#Team Selection
p1_squad_selection = st.sidebar.selectbox(label = "Squad",
                                         options = p1_available_squads,
                                         placeholder = "Select squad...",
                                         key = "P1_Squad")

#getting available players from season selection
p1_available_players = df_clean["Player"].loc[(df_clean["Squad"] == p1_squad_selection) & (df_clean["Season"] == p1_season_selection)].unique()

#Player Selection
p1_name_selection = st.sidebar.selectbox(label = "Player Name",
                     options = p1_available_players,
                     placeholder = "Select player...",
                     key = "P1_Name")

#Player 2 Selection
#Subheader
st.sidebar.subheader("Player 2")

#League Selection
p2_league_selection = st.sidebar.selectbox(label =  "League",
                                           options = df_clean["Comp"].unique(),
                                           placeholder= "Select league...",
                                           key = "P2_League")

p2_available_seasons = df_clean["Season"].loc[df_clean["Comp"] == p2_league_selection].unique()

#Season Selection
p2_season_selection = st.sidebar.selectbox(label = "Season",
                     options = p2_available_seasons,
                     placeholder = "Select season...",
                     key = "P2_Season")

p2_available_squads = df_clean["Squad"].loc[(df_clean["Comp"] == p2_league_selection) & (df_clean["Season"] == p2_season_selection)].unique()
#Team Selection
p2_squad_selection = st.sidebar.selectbox(label = "Squad",
                                         options = p2_available_squads,
                                         placeholder = "Select squad...",
                                         key = "P2_Squad")

#getting available players from season selection
p2_available_players = df_clean["Player"].loc[(df_clean["Squad"] == p2_squad_selection) & (df_clean["Season"] == p2_season_selection)].unique()

#Player Selection
p2_name_selection = st.sidebar.selectbox(label = "Player Name",
                     options = p2_available_players,
                     placeholder = "Select player...",
                     key = "P2_Name")

# type selection
#sidebar header
st.sidebar.header("Choose Radar Category!")

#sidebar
radar_category = st.sidebar.selectbox(label = "Category",
                                         options = ["Creating", "Possession", "Defense", "Shooting"],
                                         placeholder = "Select category...",
                                         key = "Radar_Cat")

#grabbing badges
def get_p1_badge():
    return plt.imread(f"ClubBadges/{p1_squad_selection}.png")

p1_badge = get_p1_badge()

def get_p2_badge():
    return plt.imread(f"ClubBadges/{p2_squad_selection}.png")

p2_badge = get_p2_badge()

#player posiition

p1_position = df_clean["Pos"].loc[(df_clean["Squad"] == p1_squad_selection) & (df_clean["Season"] == p1_season_selection) & (df_clean["Player"] == p1_name_selection)].unique()
p2_position = df_clean["Pos"].loc[(df_clean["Squad"] == p2_squad_selection) & (df_clean["Season"] == p2_season_selection) & (df_clean["Player"] == p2_name_selection)].unique()

position_filter = [p1_position[:2], p2_position[:2]]
position_filter = [arr.item() for arr in position_filter]

df_players = df_clean[df_clean["Pos"].str.startswith(tuple(position_filter))]

#creating score dataframes
creating_vars = ["CPA_Carries", "PPA", "Att Pen_Touches", "KP", "xA_per_KP", "SCA90_SCA", "xA_Expected", "CrsPA", "TB_Pass"]
creating_weights = [0.11, 0.11, 0.08, 0.11, 0.11, 0.16, 0.16, 0.08, 0.08]

defending_vars = ["Recov", "Def 3rd_Tackles", "Mid 3rd_Tackles", "Att 3rd_Tackles", "Tkl_percent_Challenges", "Att_Challenges", "Blocks_Blocks", "Int", "Clr", "Att_Aerial", "Won_percent_Aerial"]
defending_weights = [0.08, 0.07, 0.07, 0.1, 0.13, 0.1, 0.08, 0.08, 0.08, 0.08, 0.13]

poss_vars = ["Cmp_percent_Total", "Cmp_Total", "PrgP", "PrgDist_Total", "PrgR_Receiving", "Final_Third", "PrgC_Carries", "PrgDist_Carries", "Final_Third_Carries", "Att_Take", "Succ_percent_Take", "Touches_Touches"]
poss_weights = [0.0825, 0.0825, 0.0825, 0.0625, 0.0825, 0.0825, 0.0825, 0.0825, 0.0825, 0.0825, 0.0825, 0.0725]

shooting_vars = ["np:G_minus_xG_Expected", "npxG_Expected", "npxG_per_Sh_Expected", "Dist_Standard", "Sh_per_90_Standard", "Sh_per_100_Touches", "PA_Touches_per_Sh"]
shooting_weights = [0.17, 0.16, 0.145, -0.135, 0.14, 0.125, -0.125]

creating_var_names = ["Carries into PA", "Passes into PA", "PA Touches", "Key Passes", "xA per KP", "SCA", "xA", "Crosses into PA", "Through Balls"]
defending_var_names = ["Recoveries", "Def 3rd Tackles", "Mid 3rd Tackles", "Final 3rd Tackles", "Ground Duel Success", "Ground Duels", "Blocks", "interceptions", "Clearances", "Aerial Duels", "Aerial Duel Success"]
poss_var_names = ["Pass Completion", "Passes", "Prog Passes", "Prog Pass Dist", "Prog Pass Receptions", "Passes into FT", "Prog Carries", "Prog Carry Dist", "Final Third Carries", "Take-Ons", "Take-On Success", "Touches"]
shooting_var_names = ["npG - xG", "npxG", "npxG per Shot", "Avg. Shot Distance", "Shots per 90", "Propensity to Shoot", "PA Touches per Shot"]

creating_df = df_players[["Season", "Squad", "Comp", "Player"] + creating_vars]
defending_df = df_players[["Season", "Squad", "Comp", "Player"] + defending_vars]
poss_df = df_players[["Season", "Squad", "Comp", "Player"] + poss_vars]
shooting_df = df_players[["Season", "Squad", "Comp", "Player"] + shooting_vars]


#variable standardisation (Z Scores)
for var in creating_vars:
    creating_df[var] =np.log(creating_df[var] + 0.1)
    creating_df[var] = StandardScaler().fit_transform(creating_df[var].values.reshape(-1, 1))
    
for var in defending_vars:
    defending_df[var] =np.log(defending_df[var] + 0.1)
    defending_df[var] = StandardScaler().fit_transform(defending_df[var].values.reshape(-1, 1))
    
for var in poss_vars:
    poss_df[var] =np.log(poss_df[var] + 0.1)
    poss_df[var] = StandardScaler().fit_transform(poss_df[var].values.reshape(-1, 1))

for var in shooting_vars:
    if var != "np:G_minus_xG_Expected":
        shooting_df[var] =np.log(shooting_df[var] + 0.1)
        shooting_df[var] = StandardScaler().fit_transform(shooting_df[var].values.reshape(-1, 1))
    else:
        shooting_df[var] = StandardScaler().fit_transform(shooting_df[var].values.reshape(-1, 1))
        

#creating weighted averages from weights
creating_df["Weighted_Avg"] = creating_df[creating_vars].values @ creating_weights
defending_df["Weighted_Avg"] = defending_df[defending_vars].values @ defending_weights
poss_df["Weighted_Avg"] = poss_df[poss_vars].values @ poss_weights
shooting_df["Weighted_Avg"] = shooting_df[shooting_vars].values @ shooting_weights

#creating scores from the weighted averages
creating_df["Score"] = MinMaxScaler(feature_range=(0, 100)).fit_transform(creating_df[["Weighted_Avg"]])
defending_df["Score"] = MinMaxScaler(feature_range=(0, 100)).fit_transform(defending_df[["Weighted_Avg"]])
poss_df["Score"] = MinMaxScaler(feature_range=(0, 100)).fit_transform(poss_df[["Weighted_Avg"]])
shooting_df["Score"] = MinMaxScaler(feature_range=(0, 100)).fit_transform(shooting_df[["Weighted_Avg"]])


#building the radars

#adding upper and lower bounds
creating_lower_bounds = []
creating_upper_bounds = []

defending_lower_bounds = []
defending_upper_bounds = []

poss_lower_bounds = []
poss_upper_bounds = []

shooting_upper_bounds = []
shooting_lower_bounds = []

for var in creating_vars:
    creating_lower_bounds.append(creating_df[var].min())
    creating_upper_bounds.append(creating_df[var].max())

for var in defending_vars:
    defending_lower_bounds.append(defending_df[var].min())
    defending_upper_bounds.append(defending_df[var].max())
    
for var in poss_vars:
    poss_lower_bounds.append(poss_df[var].min())
    poss_upper_bounds.append(poss_df[var].max())
    
for var in shooting_vars:
    shooting_lower_bounds.append(shooting_df[var].min())
    shooting_upper_bounds.append(shooting_df[var].max())
    
creating_score = creating_df[(creating_df["Player"] == p1_name_selection) & (creating_df["Season"] == p1_season_selection)]["Score"].values.tolist()[0]
creating_score2 = creating_df[(creating_df["Player"] == p2_name_selection) & (creating_df["Season"] == p2_season_selection)]["Score"].values.tolist()[0]

defending_score = defending_df[(defending_df["Player"] == p1_name_selection) & (defending_df["Season"] == p1_season_selection)]["Score"].values.tolist()[0]
defending_score2 = defending_df[(defending_df["Player"] == p2_name_selection) & (defending_df["Season"] == p2_season_selection)]["Score"].values.tolist()[0]

poss_score = poss_df[(poss_df["Player"] == p1_name_selection) & (poss_df["Season"] == p1_season_selection)]["Score"].values.tolist()[0]
poss_score2 = poss_df[(poss_df["Player"] == p2_name_selection) & (poss_df["Season"] == p2_season_selection)]["Score"].values.tolist()[0]

shooting_score = shooting_df[(shooting_df["Player"] == p1_name_selection) & (shooting_df["Season"] == p1_season_selection)]["Score"].values.tolist()[0]
shooting_score2 = shooting_df[(shooting_df["Player"] == p2_name_selection) & (shooting_df["Season"] == p2_season_selection)]["Score"].values.tolist()[0]

creating1 = creating_df[(creating_df["Player"] == p1_name_selection) & (creating_df["Season"] == p1_season_selection)][creating_vars].values.tolist()[0]
creating2 = creating_df[(creating_df["Player"] == p2_name_selection) & (creating_df["Season"] == p2_season_selection)][creating_vars].values.tolist()[0]

defending1 = defending_df[(defending_df["Player"] == p1_name_selection) & (defending_df["Season"] == p1_season_selection)][defending_vars].values.tolist()[0]
defending2 = defending_df[(defending_df["Player"] == p2_name_selection) & (defending_df["Season"] == p2_season_selection)][defending_vars].values.tolist()[0]

poss1 = poss_df[(poss_df["Player"] == p1_name_selection) & (poss_df["Season"] == p1_season_selection)][poss_vars].values.tolist()[0]
poss2 = poss_df[(poss_df["Player"] == p2_name_selection) & (poss_df["Season"] == p2_season_selection)][poss_vars].values.tolist()[0]

shooting1 = shooting_df[(shooting_df["Player"] == p1_name_selection) & (shooting_df["Season"] == p1_season_selection)][shooting_vars].values.tolist()[0]
shooting2 = shooting_df[(shooting_df["Player"] == p2_name_selection) & (shooting_df["Season"] == p2_season_selection)][shooting_vars].values.tolist()[0]

player1_season = creating_df[(creating_df["Player"] == p1_name_selection) & (creating_df["Season"] == p1_season_selection)]["Season"].values.tolist()[0]
player2_season = creating_df[(creating_df["Player"] == p2_name_selection) & (creating_df["Season"] == p2_season_selection)]["Season"].values.tolist()[0]

players = [name.upper() for name in [p1_name_selection, p2_name_selection]]

p1_squad_selection = p1_squad_selection.upper()
p2_squad_selection = p2_squad_selection.upper()

p1_league_selection = p1_league_selection.upper()
p2_league_selection = p2_league_selection.upper()

#radar
if radar_category == "Creating":
    radar = Radar(
    params = creating_var_names, min_range = creating_lower_bounds, max_range =creating_upper_bounds,
    round_int = [False] * len(creating_lower_bounds), num_rings = 4, ring_width = 1, center_circle_radius = 1
    )

    fig,  axs = grid(figheight = 14, grid_height =0.9, title_height = 0.06, endnote_height = 0.025, title_space = 0.015, endnote_space = 0, grid_key = "radar", axis = False)

    radar.setup_axis(ax = axs["radar"])
    rings_inner = radar.draw_circles(ax = axs["radar"], facecolor = "#fffefb", edgecolor = "#efe6d8")
    radar_output = radar.draw_radar_compare(creating1, creating2, ax = axs["radar"],
                                        kwargs_radar = {"facecolor": "#1c56a5", "alpha":0.8},
                                        kwargs_compare = {"facecolor": "#06402B", "alpha":0.8})
    radar_poly1, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax = axs["radar"])
    param_labels = radar.draw_param_labels(ax = axs["radar"], fontproperties = {"weight": "bold"}, fontsize = 15)
    axs["radar"].scatter(vertices1[:,0], vertices1[:,1], c = "#1c56a5", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)
    axs["radar"].scatter(vertices2[:,0], vertices2[:,1], c = "#06402B", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)

    #Badge and Logo
    newax = fig.add_axes([-0.035, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax.imshow(p1_badge)
    newax.axis("off")

    newax2 = fig.add_axes([0.975, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax2.imshow(p2_badge)
    newax2.axis("off")

    endnote_text = axs["endnote"].text(1, 0.5, "Viz by @TheNumbers_Game via the BB Radars App. Metrics log-transformed and Z-scored. Data from Opta.", fontsize = 10, ha = "right", va = "center")
    title1_text = axs["title"].text(0.01, 0.65, players[0], fontsize = 30, ha = "left", va = "center", fontproperties = {"weight": "bold"})
    title2_text = axs["title"].text(0.99, 0.65, players[1], fontsize = 30, ha = "right", va = "center", fontproperties = {"weight": "bold"})
    subtitle1_text = axs["title"].text(0.01, 0.25, f"{p1_squad_selection} - {p1_league_selection} - {player1_season}", fontsize = 17 , ha = "left", va = "center")
    subtitle1_text = axs["title"].text(0.99, 0.25, f"{p2_squad_selection} - {p2_league_selection} - {player2_season}", fontsize = 17 , ha = "right", va = "center")
    category_text = axs["endnote"].text(0.05, 0.5, "CREATING", fontsize = 26, ha = "center", va = "center", fontproperties = {"weight": "bold"})

    rectange1 = axs["title"].add_patch(plt.Rectangle((0.01, 0), 0.4, 0.1, facecolor = "#1c56a5", lw = 2, zorder = 1))
    rectange2 = axs["title"].add_patch(plt.Rectangle((0.59, 0), 0.4, 0.1, facecolor = "#06402B", lw = 2, zorder = 1))

    creating_score_text = axs["title"].text(0.02, -0.55, f"{creating_score:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff" ,fontproperties = {"weight": "bold"})
    creating_score_text2 = axs["title"].text(0.95, -0.55, f"{creating_score2:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff", fontproperties = {"weight": "bold"})

    creating_score_text.set_bbox(dict(facecolor = "#1c56a5", edgecolor = "none", boxstyle = "round,pad=0.3"))
    creating_score_text2.set_bbox(dict(facecolor = "#06402B", edgecolor = "none", boxstyle = "round,pad=0.3"))

    plt.tight_layout()

elif radar_category == "Defense":
    radar = Radar(
        params = defending_var_names, min_range = defending_lower_bounds, max_range = defending_upper_bounds,
        round_int = [False] * len(defending_lower_bounds), num_rings = 4,  ring_width = 1, center_circle_radius = 1
    )

    fig,  axs = grid(figheight = 14, grid_height =0.9, title_height = 0.06, endnote_height = 0.025, title_space = 0.015, endnote_space = 0, grid_key = "radar", axis = False)

    radar.setup_axis(ax = axs["radar"])
    rings_inner = radar.draw_circles(ax = axs["radar"], facecolor = "#fffefb", edgecolor = "#efe6d8")
    radar_output = radar.draw_radar_compare(defending1, defending2, ax = axs["radar"],
                                            kwargs_radar = {"facecolor": "#1c56a5", "alpha":0.8},
                                            kwargs_compare = {"facecolor": "#06402B", "alpha":0.8})
    radar_poly1, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax = axs["radar"])
    param_labels = radar.draw_param_labels(ax = axs["radar"], fontproperties = {"weight": "bold"}, fontsize = 15)
    axs["radar"].scatter(vertices1[:,0], vertices1[:,1], c = "#1c56a5", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)
    axs["radar"].scatter(vertices2[:,0], vertices2[:,1], c = "#06402B", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)

    #Badge and Logo
    newax = fig.add_axes([-0.035, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax.imshow(p1_badge)
    newax.axis("off")

    newax2 = fig.add_axes([0.975, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax2.imshow(p2_badge)
    newax2.axis("off")

    endnote_text = axs["endnote"].text(1, 0.5, "Viz by @TheNumbers_Game via the BB Radars App. Metrics log-transformed and Z-scored. Data from Opta.", fontsize = 10, ha = "right", va = "center")
    title1_text = axs["title"].text(0.01, 0.65, players[0], fontsize = 30, ha = "left", va = "center", fontproperties = {"weight": "bold"})
    title2_text = axs["title"].text(0.99, 0.65, players[1], fontsize = 30, ha = "right", va = "center", fontproperties = {"weight": "bold"})
    subtitle1_text = axs["title"].text(0.01, 0.25, f"{p1_squad_selection} - {p1_league_selection} - {player1_season}", fontsize = 17 , ha = "left", va = "center")
    subtitle1_text = axs["title"].text(0.99, 0.25, f"{p2_squad_selection} - {p2_league_selection} - {player2_season}", fontsize = 17 , ha = "right", va = "center")
    category_text = axs["endnote"].text(0.05, 0.5, "DEFENDING", fontsize = 26, ha = "center", va = "center", fontproperties = {"weight": "bold"})

    rectange1 = axs["title"].add_patch(plt.Rectangle((0.01, 0), 0.4, 0.1, facecolor = "#1c56a5", lw = 2, zorder = 1))
    rectange2 = axs["title"].add_patch(plt.Rectangle((0.59, 0), 0.4, 0.1, facecolor = "#06402B", lw = 2, zorder = 1))

    score_text = axs["title"].text(0.02, -0.55, f"{defending_score:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff" ,fontproperties = {"weight": "bold"})
    score_text2 = axs["title"].text(0.95, -0.55, f"{defending_score2:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff", fontproperties = {"weight": "bold"})

    score_text.set_bbox(dict(facecolor = "#1c56a5", edgecolor = "none", boxstyle = "round,pad=0.3"))
    score_text2.set_bbox(dict(facecolor = "#06402B", edgecolor = "none", boxstyle = "round,pad=0.3"))

    plt.tight_layout()
    
elif radar_category == "Possession":
    radar = Radar(
        params = poss_var_names, min_range = poss_lower_bounds,
        max_range = poss_upper_bounds, round_int = [False] * len(poss_lower_bounds),
        num_rings = 4, ring_width = 1,
        center_circle_radius = 1
    )

    fig,  axs = grid(figheight = 14, grid_height =0.9, title_height = 0.06, endnote_height = 0.025, title_space = 0.015, endnote_space = 0, grid_key = "radar", axis = False)

    radar.setup_axis(ax = axs["radar"])
    rings_inner = radar.draw_circles(ax = axs["radar"], facecolor = "#fffefb", edgecolor = "#efe6d8")
    radar_output = radar.draw_radar_compare(poss1, poss2, ax = axs["radar"],
                                            kwargs_radar = {"facecolor": "#1c56a5", "alpha":0.8},
                                            kwargs_compare = {"facecolor": "#06402B", "alpha":0.8})
    radar_poly1, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax = axs["radar"])
    param_labels = radar.draw_param_labels(ax = axs["radar"], fontproperties = {"weight": "bold"}, fontsize = 15)
    axs["radar"].scatter(vertices1[:,0], vertices1[:,1], c = "#1c56a5", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)
    axs["radar"].scatter(vertices2[:,0], vertices2[:,1], c = "#06402B", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)

    #Badge and Logo
    newax = fig.add_axes([-0.035, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax.imshow(p1_badge)
    newax.axis("off")

    newax2 = fig.add_axes([0.975, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax2.imshow(p2_badge)
    newax2.axis("off")

    endnote_text = axs["endnote"].text(1, 0.5, "Viz by @TheNumbers_Game via the BB Radars App. Metrics log-transformed and Z-scored. Data from Opta.", fontsize = 10, ha = "right", va = "center")
    title1_text = axs["title"].text(0.01, 0.65, players[0], fontsize = 30, ha = "left", va = "center", fontproperties = {"weight": "bold"})
    title2_text = axs["title"].text(0.99, 0.65, players[1], fontsize = 30, ha = "right", va = "center", fontproperties = {"weight": "bold"})
    subtitle1_text = axs["title"].text(0.01, 0.25, f"{p1_squad_selection} - {p1_league_selection} - {player1_season}", fontsize = 17 , ha = "left", va = "center")
    subtitle1_text = axs["title"].text(0.99, 0.25, f"{p2_squad_selection} - {p2_league_selection} - {player2_season}", fontsize = 17 , ha = "right", va = "center")
    category_text = axs["endnote"].text(0.05, 0.5, "POSSESSION", fontsize = 26, ha = "center", va = "center", fontproperties = {"weight": "bold"})

    rectange1 = axs["title"].add_patch(plt.Rectangle((0.01, 0), 0.4, 0.1, facecolor = "#1c56a5", lw = 2, zorder = 1))
    rectange2 = axs["title"].add_patch(plt.Rectangle((0.59, 0), 0.4, 0.1, facecolor = "#06402B", lw = 2, zorder = 1))

    score_text = axs["title"].text(0.02, -0.55, f"{poss_score:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff" ,fontproperties = {"weight": "bold"})
    score_text2 = axs["title"].text(0.95, -0.55, f"{poss_score2:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff", fontproperties = {"weight": "bold"})

    score_text.set_bbox(dict(facecolor = "#1c56a5", edgecolor = "none", boxstyle = "round,pad=0.3"))
    score_text2.set_bbox(dict(facecolor = "#06402B", edgecolor = "none", boxstyle = "round,pad=0.3"))

    plt.tight_layout()
    
elif radar_category == "Shooting":
    radar = Radar(
        params = shooting_var_names, min_range = shooting_lower_bounds,
        max_range = shooting_upper_bounds,
        round_int = [False] * len(shooting_lower_bounds),
        num_rings = 4, ring_width = 1, center_circle_radius = 1
    )

    fig,  axs = grid(figheight = 14, grid_height =0.9, title_height = 0.06, endnote_height = 0.025, title_space = 0.015, endnote_space = 0, grid_key = "radar", axis = False)

    radar.setup_axis(ax = axs["radar"])
    rings_inner = radar.draw_circles(ax = axs["radar"], facecolor = "#fffefb", edgecolor = "#efe6d8")
    radar_output = radar.draw_radar_compare(shooting1, shooting2, ax = axs["radar"],
                                            kwargs_radar = {"facecolor": "#1c56a5", "alpha":0.8},
                                            kwargs_compare = {"facecolor": "#06402B", "alpha":0.8})
    radar_poly1, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax = axs["radar"])
    param_labels = radar.draw_param_labels(ax = axs["radar"], fontproperties = {"weight": "bold"}, fontsize = 15)
    axs["radar"].scatter(vertices1[:,0], vertices1[:,1], c = "#1c56a5", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)
    axs["radar"].scatter(vertices2[:,0], vertices2[:,1], c = "#06402B", edgecolors = "#6d6c6d", marker = "o", s = 150, zorder = 2)

    #Badge and Logo
    newax = fig.add_axes([-0.035, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax.imshow(p1_badge)
    newax.axis("off")

    newax2 = fig.add_axes([0.975, 0.94, 0.055, 0.055], anchor = "C", zorder = 10)
    newax2.imshow(p2_badge)
    newax2.axis("off")

    endnote_text = axs["endnote"].text(1, 0.5, "Viz by @TheNumbers_Game via the BB Radars App. Metrics log-transformed and Z-scored. Data from Opta.", fontsize = 10, ha = "right", va = "center")
    title1_text = axs["title"].text(0.01, 0.65, players[0], fontsize =30, ha = "left", va = "center", fontproperties = {"weight": "bold"})
    title2_text = axs["title"].text(0.99, 0.65, players[1], fontsize = 30, ha = "right", va = "center", fontproperties = {"weight": "bold"})
    subtitle1_text = axs["title"].text(0.01, 0.25, f"{p1_squad_selection} - {p1_league_selection} - {player1_season}", fontsize = 17 , ha = "left", va = "center")
    subtitle1_text = axs["title"].text(0.99, 0.25, f"{p2_squad_selection} - {p2_league_selection} - {player2_season}", fontsize = 17 , ha = "right", va = "center")
    category_text = axs["endnote"].text(0.05, 0.5, "SHOOTING", fontsize = 26, ha = "center", va = "center", fontproperties = {"weight": "bold"})

    rectange1 = axs["title"].add_patch(plt.Rectangle((0.01, 0), 0.4, 0.1, facecolor = "#1c56a5", lw = 2, zorder = 1))
    rectange2 = axs["title"].add_patch(plt.Rectangle((0.59, 0), 0.4, 0.1, facecolor = "#06402B", lw = 2, zorder = 1))

    score_text = axs["title"].text(0.02, -0.55, f"{shooting_score:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff" ,fontproperties = {"weight": "bold"})
    score_text2 = axs["title"].text(0.95, -0.55, f"{shooting_score2:.0f}", fontsize = 25, ha = "left", va = "center", color = "#ffffff", fontproperties = {"weight": "bold"})

    score_text.set_bbox(dict(facecolor = "#1c56a5", edgecolor = "none", boxstyle = "round,pad=0.3"))
    score_text2.set_bbox(dict(facecolor = "#06402B", edgecolor = "none", boxstyle = "round,pad=0.3"))
    
    plt.tight_layout()

    
        

st.pyplot(fig)

filename = "radar.png"

buf = io.BytesIO()
fig.savefig(buf, format = "png", bbox_inches = "tight")


st.download_button(
    label = "Download Viz",
    data = buf,
    file_name = filename,
    mime = "image/png"
)





