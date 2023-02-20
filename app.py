import streamlit as st
import pandas as pd
import numpy as np
import gspread
import random
import requests
import altair as alt
from PIL import Image


logo_url = "https://www.gradina-slavu.ro/"
logo_path = "https://static.wixstatic.com/media/268e9b_fb1da1f5fc304d15beee1d2e581d5d0c~mv2.png/v1/fill/w_134,h_62,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/nume.png"

# Display the logo with a black background and centered alignment
st.markdown(
    f"""
    <div style='background-color: rgba(128,128,128,0.4); text-align: center;'>
        <a href='{logo_url}' target='_blank'>
            <img src='{logo_path}' width='150'>
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title('RETETE - Selecteaza produs din sidebar')
st.write(' ')

sa= gspread.service_account(filename='creds.json')
# Open the Google Sheets file
sh = sa.open_by_url("https://docs.google.com/spreadsheets/d/1GZjbDLYTgRhKHtvgT868ursHYzXXmHF23w86-3KNZN0/edit#gid=489241774")

worksheet=sh.get_worksheet(0)
worksheet1=sh.get_worksheet(1)
worksheet2=sh.get_worksheet(2)

rows = worksheet.get_all_values()
rows1 = worksheet1.get_all_values()
rows2 = worksheet2.get_all_values()
df=pd.DataFrame(rows)
df1=pd.DataFrame(rows1)
df2=pd.DataFrame(rows2)
df2=df2.iloc[1:]


options=['stevie','rosii cherry','rosii tocate','suc de rosii','rosii cherry uscate','pesto de busuioc','carne vegetala','pate de ciuperci','zacusca de vinete','zacusca de peste','zacusca de fasole','magiun de prune','hrean in otet','legume uscate']
valori_optime=['2000','280','25','50','70','20','1600','17000','50','5000','75','5','10','80','1.4','1.6','18','2','400','6','6','550','12','1000','15','350','1000','3500','2400','15','2','5','35','3.5','300','2']
selected_option = st.sidebar.selectbox("Selecteaza un produs", options)


def select_random_value(df, selected_option):
    # Select a random item from the list
    selected_item = selected_option 
    
    # Find the corresponding values in the dataframe
    matching_rows = df[df[3] == selected_item]
    corresponding_values = matching_rows[0].tolist()
    
    # Select a random value from the corresponding values
    if corresponding_values:
        selected_value = random.choice(corresponding_values)
        return selected_value
    else:
        return None

reteta_selectata=select_random_value(df1,selected_option)

d2 = df2.set_index(0).to_dict('index')
d2 = {k: {k2: float(v2) for k2, v2 in v.items()} for k, v in d2.items()}

discarded_keys=['Zaharuri','Grasimi saturate','Omega-6','Vit A','Vit C','Vit D','Vit E','Vit K','Pantothenic acid-B5','Choline-B4','Betaine','Sodiu','Cupru','Mangan','Seleniu','Fluor','Cholesterol','Phytosterols']

def select_optimized_keys(d, value, optimals, discarded_keys):
    optimals = [float(x) for x in optimals]
    
    # Normalize the values for all keys except discarded ones
    normalized = {}
    for k, v in d.items():
        if k not in discarded_keys:
            values = [v2 for k2, v2 in v.items() if k2 not in discarded_keys]
            min_value, max_value = min(values), max(values)
            normalized[k] = {k2: (v2 - min_value) / (max_value - min_value) for k2, v2 in v.items() if k2 not in discarded_keys}

    matching_key = [k for k, v in d.items() if k == value][0]
    other_keys = [k for k in d.keys() if k != matching_key]
    
    # Choose a random second key
    second_key = random.choice(other_keys)
    
    # Pick the 6 parameters with bigger gaps for optimizing the third key
    gaps = {}
    for k, v in normalized.items():
        if k != matching_key and k != second_key:
            gaps[k] = max(v.values()) - min(v.values())
    sorted_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)
    third_keys = [x[0] for x in sorted_gaps][:8]
    
    def difference(key):
        return sum(np.abs(sum([normalized[k][j] for k in [second_key, key]]) * 4 - optimals[i]) for i, j in enumerate(normalized[matching_key].keys()))

    # Optimize the third key with the 6 parameters with bigger gaps
    optimized_key = min(third_keys, key=difference)
    
    return [second_key, optimized_key, matching_key]
selected_keys=select_optimized_keys(d2, reteta_selectata, valori_optime,discarded_keys)
selected_keys=list(selected_keys)
selected_keys.reverse()


def search_values(lst, dct):
    result = {}
    for item in lst:
        for key, value in dct.items():
            if item == key:
                result[item] = value
    return result

# create a dictionary to hold the new dataframes
dfs = {}

# loop through the categories and create a new dataframe for each one
for reteta in selected_keys:
    dfs[reteta] = df1[df1[0] == reteta]

dfs2={}
for reteta in selected_keys:
    dfs2[reteta] = df1[df1[0] == reteta].iloc[:,6:]


def make_clickable(url):
    return f'<a href="{url}" target="_blank">{url}</a>'

for i in range(len(selected_keys)):
    dfs1 = dfs[selected_keys[i]]
    dfs1 = pd.DataFrame(dfs1)
    images_displayed = False
    # update 'path' column with formatted URLs
    dfs1[6] = dfs1[6].apply(make_clickable)
    for index, row in dfs1.iterrows():
        image_path = row[6]
        if not image_path:
            continue
        # extract URL from formatted string
        url = image_path.split('"')[1]
        if not url.startswith('http'):
            continue
        try:
            image = Image.open(requests.get(url, stream=True).raw)
            image = image.resize((300,300))
            with st.container():
              col1, col2, col3 = st.columns([1, 2, 1])
              col2.image(image, caption=selected_keys[i], width=300, use_column_width=True)
              images_displayed = True
        except:
            continue
    if images_displayed:
        dfs1 = dfs1.iloc[:,3:6]
        dfs1 = dfs1.reset_index(drop=True)
        indexcol = ['Ingrediente', 'Gramaj', 'Preparare']
        dfs1.columns = indexcol
        st.subheader(selected_keys[i])
        st.write(dfs1,index=False)
        
    else:
        st.warning(f"No image found for {selected_keys[i]}")
    
   
    

final_result=search_values(selected_keys,d2)

Finaldf=pd.DataFrame(final_result)
Finaldf=Finaldf.round(0)
new_index=['Calorii','Carbohidrati','Fibre dietetice','Zaharuri','Grasimi','Grasimi saturate','Omega-3','Omega-6','Proteina','Vit A','Vit C','Vit D','Vit E','Vit K','Thiamin-B1','Riboflavin-B2','Niacin-B3','Vitamina-B6','Folate-B9','Vitamina-B12','Pantothenic acid-B5','Choline-B4','Betaine','Calciu','Fier','Magneziu','Fosfor','Potasiu','Sodiu','Zinc','Cupru','Mangan','Seleniu','Fluor','Cholesterol','Phytosterols']
Finaldf = Finaldf.set_index(pd.Index(new_index))

def add_dict_values(d):
    result = {}
    keys = set().union(*(d[key].keys() for key in d))
    for key in keys:
        result[key] = sum(d[k].get(key, 0) for k in d)
    return result

valori_meniu_d=add_dict_values(final_result)
valori_meniu=list(valori_meniu_d.values())

def subtract_lists(list1, list2):
    result = [max(0,float(i) - float(j)*3.5) for i, j in zip(list1, list2)]
    return result

Valori_ramase=subtract_lists(valori_optime,valori_meniu)

Finaldf['valori ramase dupa portii de 350g']=Valori_ramase
Finaldf['Valori mediu portii de 350g']=valori_meniu
Finaldf['Valori mediu portii de 350g']=Finaldf['Valori mediu portii de 350g'].apply(lambda x: float(x) * 3.5)
Finaldf['Valori Optime']=valori_optime
st.write(Finaldf)

Valori_normate = [(float(valori_optime[i]) - Valori_ramase[i]) / float(valori_optime[i]) for i in range(len(valori_optime))]
Valori_ramase_normate=[ Valori_ramase[i] / float(valori_optime[i]) for i in range(len(valori_optime))]
chartdf = pd.DataFrame({
    'Procente ramase de consumat':pd.Categorical(new_index, categories=new_index),
    'max_values':Valori_normate,
    'Procente': Valori_ramase_normate,
})

# Create a Categorical datatype for the x-axis
x_scale = alt.Scale(domain=new_index, zero=False)
# Define the chart using Altair
chart = alt.Chart(chartdf).mark_bar().encode(
    x=alt.X('Procente ramase de consumat:O', scale=x_scale),
    y='Procente',
    color=alt.condition(
        alt.datum.results > alt.datum.max_values,
        alt.value('red'),  # Set the color to red if the result is greater than the max value
        alt.value('blue'),  # Set the color to blue if the result is less than or equal to the max value
    )
).properties(
    width=alt.Step(40),  # Set the width of each bar
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

#sidebar for categories

# Define columns to display and exclude
all_columns = new_index
df.iloc[0, 2:] = new_index
# set the column names to the values in the first row
df = df.set_axis(df.iloc[0], axis=1)

# remove the first row from the dataframe
df = df.iloc[1:]
# Define sidebar widgets
sort_col = st.sidebar.selectbox('Selecteaza o categorie', all_columns)
st.sidebar.write("Optiunea suplimentare, !!!va genera noi retete cu fiecare selectie!!!, foloseste-o separat de optiunea principala pentru a gasi cele mai bogate ingrediente intr-o anumita categorie! (/100g)")

# Filter and sort dataframe
df[sort_col] = df[sort_col].astype(float)
display_df = df[[df.columns[0], sort_col]].sort_values(by=sort_col, ascending=False)

# Display dataframe
st.write(display_df)
