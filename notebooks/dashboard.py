# Aplicativo Streamlit House Rocket

import folium
import geopandas
import webbrowser
import numpy          as np
import pandas         as pd
import streamlit      as st
import plotly_express as px

from matplotlib        import pyplot as plt
from datetime          import datetime
from streamlit_folium  import folium_static
from folium.plugins    import MarkerCluster

#layout page
#============
st.set_page_config(page_title = 'Dashboard - House Rocket',page_icon=':cityscape:',layout='wide') 

# Introduction page
#===================
st.markdown("<h1 style='text-align: center; color: black;'>Project House Rocket</h1>",unsafe_allow_html=True)


# Functions
#===============
@st.cache(allow_output_mutation=True)
def get_data(path):
    data_raw = pd.read_csv(path)

    return data_raw


def get_geofile( url ):
     geofile = geopandas.read_file( url )

     return geofile

def set_features(data):
    
    # Format of date
    #data['date'] = pd.to_datetime(data['date'])
    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
   

    #add new feature
    data['price_m2'] = data['price']/ data['sqft_lot']
    #data['sqft_living'] = data['sqft_living'] *0.93  

    #st.write(data.dtypes)
  
    return data


# Region Overview
#===============

def portfolio_density(data,geofile):

    st.title('Region Overview')
    st.markdown('In this step we will see how the House Rocket dataset it is distributed by zipcode and by region.')
   
    c1,c2 = st.beta_columns((1,1))
    
    #Base Map - Folium
    density_map = folium.Map(location=[data['lat'].mean(),
                data['long'].mean()],
                default_zoom_start=10)

    marker_cluster = MarkerCluster().add_to(density_map)
    for name, row in data.iterrows():
        folium.Marker([row['lat'],row['long']],
            popup='Sold R${0} on: {1}, Features:{2} m2, {3} bedrooms, {4} bathrooms,zipcode:{5} County: {6}, Town:{7}'.format(row['price'],
                    row['date'],
                    row['sqft_living'],
                    row['bedrooms'],
                    row['bathrooms_real'],
                    row['zipcode'],
                    row['county'],
                    row['town']),
                    parse_html=True).add_to(marker_cluster)
    
    with c2:
        folium_static(density_map)

    #Avarage metrics
    df1 = data[['price','zipcode']].groupby('zipcode').count().reset_index() 
    df2 = np.round(data[['price_m2','zipcode']].groupby('zipcode').mean(),1).reset_index()
    df3 = np.round(data[['price_m2','zipcode']].groupby('zipcode').std(),1).reset_index()
    df4 = np.round(data[['bedrooms','zipcode']].groupby('zipcode').mean(),1).reset_index()
    df5 = np.round(data[['bathrooms_real','zipcode']].groupby('zipcode').mean(),1).reset_index()
    
    #merge
    m1 = pd.merge(df1,df2,on='zipcode', how='inner')
    m2 = pd.merge(m1,df3,on='zipcode', how='inner')
    m3 = pd.merge(m2,df4,on='zipcode', how='inner')
    df = pd.merge(m3,df5,on='zipcode', how='inner')


    df.columns = ['Zipcode','Total Houses','Mean Price/m2','Std Price/m2','Mean Bedromms','Mean Bathrooms']
  
    
    with c1:
        st.dataframe(df,width= 650,height=500)
    


# Analysis per Town
#====================

def region_town(data):
    
    st.title('Analysis per City')
    st.markdown('In this step I collected the data from an API, so that the user can identify the median by region.')

    c1, c2 = st.beta_columns(2)

    df = data[['zipcode','town','price','condition_type']]   

    aux03 = df[['town','price']].groupby('town').count().reset_index()
    aux03 = aux03[['town','price']].sort_values('price',ascending=False).reset_index(drop= True)

    fig = px.bar(aux03, y='price', x='town',width=500, height=500,template="plotly_white")
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide',xaxis = {'title': 'city'},
                   yaxis = {'title': 'quantity of houses'},xaxis_tickangle=-45)
    fig.update_traces(marker_color='rgb(0,0,139)')

    with c1:
        st.header('Count per city')
        st.plotly_chart(fig)

    aux04 = df[['town','price']].groupby('town').median().reset_index()
    aux04 = aux04[['town','price']].sort_values('price',ascending=False).reset_index(drop= True)

    fig = px.bar(aux04, y='price', x='town',width=500, height=500,template="plotly_white")
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide',xaxis = {'title': 'city'},
                   yaxis = {'title': 'median price'},xaxis_tickangle=-45)
    fig.update_traces(marker_color='rgb(0,0,139)', col=1)

    with c2:
        st.header('Median per city')
        st.plotly_chart(fig)


def season_sale(data):

    st.title('Sales Analysis per Season')
    st.markdown('In this step an analysis of the quantity of sales per season and we demonstrate median of monthly sales')

    c1, c2 = st.beta_columns(2)

    df1 = data[['id','zipcode','month','price','season']]
    aux = df1[['season','price']].groupby('season').count().reset_index()
    aux = aux[['season','price']].sort_values('price',ascending=False).reset_index(drop= True)

    #plot the graph
    fig = px.bar(aux, y='season', x='price',width=600, height=500,template="plotly_white")
    fig.update_layout(uniformtext_minsize=12,xaxis = {'title': 'quantity of houses'}, uniformtext_mode='show')
    fig.update_traces(marker_color='rgb(0,0,139)')
    
    with c1:
        st.header('Count per season')
        st.plotly_chart(fig)

    aux2 = data[['month','price']].groupby('month').median().reset_index()
    fig = px.bar(aux2, y='price', x='month',width=600, height=500,template="plotly_white",color='price')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='show',yaxis = {'title': 'median price'})
    #fig.update_xaxes(range =[1,12])
    
    with c2:
        st.header('Median per month')
        st.plotly_chart(fig)

# Simulation sales
#====================
def sales_simulation(data):

    st.title('Sales Analysis')
    st.markdown('In this step you can simulate the best and worst scenario for selling a house. Which we calculate from the region and the choice of season.')    

    c1, c2 = st.beta_columns(2)

    st.sidebar.title('Sales Analysis')

    #Filters
    f_zipcode=st.sidebar.selectbox('Select Zipcode',sorted(set(data['zipcode'].unique())))
    f_price=st.sidebar.number_input('Select Price')
    f_season= st.sidebar.selectbox('Select Season',options=['summer', 'autumn', 'winter','spring'])

    # Calculate median of price per region
    df = data[['id','zipcode','month','price','season']]

    for i in range(len(df)):  
        price_median = df.loc[df['zipcode'] == f_zipcode, 'price'].median() 

    
    if (f_price <= price_median) & (f_season == 'winter') or (f_season == 'autumn'):
        #status = 'Yes'
        worst_scene = f_price + (f_price * 0.10)
        best_scene = f_price + (f_price * 0.15)
        

    elif (f_price <= price_median) & (f_season == 'summer') or (f_season == 'spring'):  
        worst_scene = f_price +(f_price * 0.20)
        best_scene = f_price + (f_price * 0.30)
       

    else:
        status = 'No' 
        best_scene = 0.0
        worst_scene = 0.0
    
    if (best_scene <= price_median) & (worst_scene <= price_median): 
        status = 'Yes'
    else:
        status = 'No'
    

   
    with c1:
        df2 = pd.DataFrame({   
        'Zipcode': [f_zipcode],
        'Price': [f_price],
        'Season': [f_season],
        'Price Median': [price_median],
        'Best Scene': [best_scene],
        'Worst Scene': [worst_scene],
        'Purchase Status': [status]}).T
        df2.columns = ['results']
        
        st.write(df2)
    

    fig = px.bar(y=[f_price,price_median,best_scene,worst_scene],x=['Price','Price Median','Best Scene','Worst Scene'],width=600, height=500,template='plotly_white',labels={'x':'','y':''})
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide',xaxis_tickangle=-45)
    fig.update_traces(marker_color='rgb(0,0,139)')

    with c2:
        st.plotly_chart(fig)

if __name__ == '__main__':

    # get data
    path= 'streamlit_house_rocket.csv'
    data_raw = get_data(path)

    #get geofile 
    url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'

    geofile = get_geofile(url)

    data = set_features(data_raw)

    #overview_data(data)

    portfolio_density(data,geofile)

    region_town(data)

    season_sale(data)

    sales_simulation(data)

   













