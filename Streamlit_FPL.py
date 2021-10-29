######################
# Import libraries
######################
import numpy as np
import pandas as pd
import requests
import streamlit as st
import pickle
from collections import Counter
from collections import OrderedDict
from PIL import Image


st.set_page_config(layout="wide")

######################
# Custom function
######################

def rearrange_columns(column_names,positions, df):
    
    if len(column_names) != len(positions):
        print("The list of column_names and positions does not have equal number of items to iter through")
        
    else:
        for pos in positions: 
            if len(df.columns) < pos:
                print("The df will not have the positions given after columns are taken out")
                break
    
        else:
            for column, pos in zip(column_names, positions):
                x = df.pop(column)
                df.insert(pos, column, x)    

def team_code_name_mapping(df, column_name):
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    r = requests.get(url)
    json = r.json()
    teams_df = pd.DataFrame(json['teams'])
    teams_modified_df = teams_df[['id','name','short_name']]
    temp_dict = dict(zip(teams_modified_df.id, teams_modified_df.name))
    df[column_name] = df[column_name].map(temp_dict)

def cost_effective_players(position,count):
    
    best_value_df = players_df[['web_name','full_name','position','team','cost','form','total_points','bonus','goals_scored','assists','clean_sheets','saves','points_per_game']]
    best_value_df.drop(best_value_df[best_value_df.total_points < 1].index, inplace=True)
    
    best_value_df['points_per_game'] = best_value_df.points_per_game.astype(float)
    best_value_df['tp_value'] = best_value_df['cost'] / best_value_df['total_points']
    best_value_df['b_value'] = best_value_df['cost'] / best_value_df['bonus']
    best_value_df['gs_value'] = best_value_df['cost'] / best_value_df['goals_scored']
    best_value_df['a_value'] = best_value_df['cost'] / best_value_df['assists']
    best_value_df['cs_value'] = best_value_df['cost'] / best_value_df['clean_sheets']
    best_value_df['s_value'] = best_value_df['cost'] / best_value_df['saves']
    best_value_df['ppg_value'] = best_value_df['cost'] / best_value_df['points_per_game']

    if position == 'FWD':
        col_df = best_value_df[['tp_value','b_value','ppg_value','gs_value','a_value']]
    elif position == 'MID':
        col_df = best_value_df[['tp_value','b_value','ppg_value','gs_value','a_value']]
    elif position == 'DEF':
        col_df = best_value_df[['tp_value','b_value','ppg_value','gs_value','a_value','cs_value']]
    elif position == 'GKP':
        col_df = best_value_df[['tp_value','b_value','ppg_value','cs_value','s_value']]
    else:
        print ("error")
         
    players = []
    
    pos_df = best_value_df[best_value_df["position"] == position]
    for i in col_df:
        sorted_df = pos_df.sort_values(i, ascending=True).head(count)
        players.extend(sorted_df['full_name'].tolist())
    players_dict = dict(Counter(players))
    pos_df.insert(5,'score','')
    pos_df['score'] = pos_df['full_name'].map(players_dict, na_action='ignore')
    pos_df.drop(['full_name','position','tp_value','b_value','ppg_value','gs_value','a_value','cs_value','s_value'], axis=1, inplace=True)
    return pos_df.sort_values(['score','total_points','cost'], ascending=[False,False,True]).head(25)

def team_strength(team, pos_value):
    
    if pos_value == 'FULL':
        strength = players_df.loc[players_df['team'] == team, 'form'].sum().round(2)
    else:
        strength = players_df.loc[(players_df['team'] == team) & (players_df['position'] == pos_value), 'form'].sum().round(2)
    
    return strength

def winning_chance(team_1,team_2):
    
    winning_team = ''
    losing_team = ''
    
    strength_difference = strength_df.loc[strength_df['team'] == team_1].full_strength.values[0] - strength_df.loc[strength_df['team'] == team_2].full_strength.values[0]
    
    if strength_difference > 0:
        winning_team = team_1
        losing_team = team_2
    else: 
        winning_team = team_2
        losing_team = team_1
        
    winning_chance_team1 = "{0:.0f}%".format((strength_df.loc[strength_df['team'] == team_1].full_strength.values[0] / (strength_df.loc[strength_df['team'] == team_1].full_strength.values[0] + strength_df.loc[strength_df['team'] == team_2].full_strength.values[0])) * 100)
    winning_chance_team2 = "{0:.0f}%".format((strength_df.loc[strength_df['team'] == team_2].full_strength.values[0] / (strength_df.loc[strength_df['team'] == team_1].full_strength.values[0] + strength_df.loc[strength_df['team'] == team_2].full_strength.values[0])) * 100)    
    
    return winning_chance_team1

def goal_scoring_chance(team_1,team_2):
    
    team_1_gs_value = (strength_df.loc[strength_df['team'] == team_1].fwd_strength.values[0] + strength_df.loc[strength_df['team'] == team_1].mid_strength.values[0]) - (strength_df.loc[strength_df['team'] == team_2].def_strength.values[0] + strength_df.loc[strength_df['team'] == team_2].gkp_strength.values[0])

    team_2_gs_value = (strength_df.loc[strength_df['team'] == team_2].fwd_strength.values[0] + strength_df.loc[strength_df['team'] == team_2].mid_strength.values[0]) - (strength_df.loc[strength_df['team'] == team_1].def_strength.values[0] + strength_df.loc[strength_df['team'] == team_1].gkp_strength.values[0])
    
    if team_1_gs_value < 0:
        team_1_gsc = "{0:.0f}%".format(100)
        team_2_gsc = "{0:.0f}%".format(0)
    elif team_2_gs_value < 0: 
        team_1_gsc = "{0:.0f}%".format(0)
        team_2_gsc = "{0:.0f}%".format(100)
    else:
        team_1_gsc = "{0:.0f}%".format((team_1_gs_value / (team_1_gs_value + team_2_gs_value)) * 100)
        team_2_gsc = "{0:.0f}%".format((team_2_gs_value / (team_1_gs_value + team_2_gs_value)) * 100)
    return team_1_gsc

@st.cache(allow_output_mutation=True)
def get_fixture_detail(event):
    
    url = "https://fantasy.premierleague.com/api/fixtures?future=1"
    r = requests.get(url)
    json = r.json()
    
    initial_fixtures_df = pd.DataFrame(json)
    fixtures_df = initial_fixtures_df[['event','team_h','team_a','team_h_difficulty','team_a_difficulty']]
    team_code_name_mapping(fixtures_df,'team_h')
    team_code_name_mapping(fixtures_df,'team_a')

    fixtures_df['team_h_win%'] = fixtures_df.apply(lambda row: winning_chance(row['team_h'],row['team_a']), axis=1)
    fixtures_df['team_a_win%'] = fixtures_df.apply(lambda row: winning_chance(row['team_a'],row['team_h']), axis=1)
    fixtures_df['team_h_gsc%'] = fixtures_df.apply(lambda row: goal_scoring_chance(row['team_h'],row['team_a']), axis=1)
    fixtures_df['team_a_gsc%'] = fixtures_df.apply(lambda row: goal_scoring_chance(row['team_a'],row['team_h']), axis=1)

    show_fixture = fixtures_df[fixtures_df["event"] == event]
    show_fixture.drop(['event','team_h_difficulty','team_a_difficulty',], axis=1, inplace=True)
    
    return show_fixture

######################
# Base Code
######################

url = "https://fantasy.premierleague.com/api/bootstrap-static/"
r = requests.get(url)
json = r.json()
    
elements_df = pd.DataFrame(json['elements'])
players_df = elements_df[['id', 'web_name', 'element_type', 'team_code', 'first_name', 'second_name','form', 'total_points', 'bonus', 'now_cost', 'goals_scored', 'assists', 'clean_sheets','saves','points_per_game','selected_by_percent','chance_of_playing_this_round','chance_of_playing_next_round']]

teams_df = pd.DataFrame(json['teams'])
teams_modified_df = teams_df[['code','name','short_name']]
teams_modified_df.rename(columns={'code': 'team_code'}, inplace=True)

players_df = pd.merge(players_df, teams_modified_df, on ='team_code', how ='left')
players_df['element_type'] = players_df['element_type'].map({1:'GKP', 2:'DEF', 3:'MID', 4:'FWD'})
players_df['now_cost'] = (players_df['now_cost'] / 10).astype(float)
players_df['form'] = players_df['form'].astype(float)
players_df['full_name'] = players_df["first_name"] + ' , '+ players_df["second_name"]
players_df.rename(columns={'name': 'team', 'short_name': 'team_abv', 'element_type': 'position', 'now_cost': 'cost', 'id': 'player_id'}, inplace=True)
rearrange_columns(['full_name', 'position', 'team', 'team_abv','cost'],[3,4,5,6,7],players_df)
players_df.drop(['first_name','second_name','team_code'], axis=1, inplace=True)

player_database = players_df[['web_name','position','team_abv','cost','form','total_points','bonus','goals_scored','assists','clean_sheets','saves','points_per_game','selected_by_percent','chance_of_playing_this_round','chance_of_playing_next_round']]
player_database.rename(columns={'team_abv': 'team', 'chance_of_playing_this_round': 'playing_this_round', 'chance_of_playing_next_round': 'playing_next_round'}, inplace=True)

team_list = OrderedDict.fromkeys(players_df['team'].tolist())

full_strength = []
fwd_strength = []
mid_strength = []
def_strength = []
gkp_strength = []

for i in team_list:
    full_strength.append(team_strength(i,'FULL'))
    fwd_strength.append(team_strength(i,'FWD'))
    mid_strength.append(team_strength(i,'MID'))
    def_strength.append(team_strength(i,'DEF'))
    gkp_strength.append(team_strength(i,'GKP'))

strength_df = pd.DataFrame({'team':list(team_list.keys()),'full_strength':full_strength,'fwd_strength':fwd_strength,'mid_strength':mid_strength,'def_strength':def_strength,'gkp_strength':gkp_strength})

######################
# Page Title
######################

image = Image.open('FPL.png')

st.image(image, use_column_width=400)

st.write("""
# FPL Analysis Web App

This app helps you with analyzing a lot of things FPL related!

""")

######################
# (Side Panel)
######################

st.sidebar.header('User Input Features')

st.sidebar.subheader('Player Database')

filter_team = st.sidebar.selectbox('Team',OrderedDict.fromkeys(player_database['team'].tolist()))

st.sidebar.subheader('Cost Effective Players')

pos = st.sidebar.selectbox('Position', list(['FWD','MID','DEF','GKP']))
count_range = st.sidebar.slider('Range', 5, 100, 50)

st.sidebar.subheader('Fixture Details')

event_selector = st.sidebar.selectbox('Gameweek', [x for x in [json['events'][i]['id'] if json['events'][i]['finished'] == False else 'str used to skip' for i in range(len(json['events']))] if isinstance(x, int)])

######################
# (Main Area)
######################

st.header('Player Database') 

st.dataframe(player_database[player_database['team'] == filter_team].style.format({'cost': '{:.1f}','form': '{:.1f}'}))

st.header('Cost Effective Players')
st.dataframe(cost_effective_players(pos,count_range).style.format({'cost': '{:.1f}','points_per_game': '{:.1f}','score': '{:.0f}','form': '{:.1f}'}))

st.header('Fixture Details')
st.dataframe(get_fixture_detail(event_selector))