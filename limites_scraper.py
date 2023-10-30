import requests
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
from geopandas import GeoDataFrame
import plotly.express as px
import plotly.io as pio
from urllib.error import HTTPError

# Set notebook mode to work in offline
pio.renderers.default = 'iframe'

url_stations = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/stations"

response_stations = requests.get(url_stations, params={"size": 6000})
if response_stations.status_code == '200' or '206': # status codes are detailed on the website
    data_stations = response_stations.json()
    data_stations = pd.DataFrame(data_stations["data"])
else:
    print(f"La requête a échoué avec le code d'état {response_stations.status_code}")

# We check the names of the columns that contain at least 50% of null values
data_stations.isnull().sum()

# We remove the columns that contain at least 50% of null values
data_stations = data_stations.dropna(axis=1, thresh=int(0.5*len(data_stations)))

# We remove every row that is not in metropolitan france
regions_in_metropolitan_france = ['GRAND EST', 'HAUTS-DE-FRANCE', 'BOURGOGNE-FRANCHE-COMTE', 'ILE-DE-FRANCE', 'CENTRE-VAL DE LOIRE', 'NORMANDIE', 'BRETAGNE', 'PAYS DE LA LOIRE', 'AUVERGNE-RHONE-ALPES', 'OCCITANIE', 'NOUVELLE-AQUITAINE', "PROVENCE-ALPES-COTE D'AZUR", 'CORSE']
data_stations = data_stations[data_stations["libelle_region"].isin(regions_in_metropolitan_france)]

# Next, we remove every row where the corresponding station is not active
data_stations = data_stations[data_stations["en_service"] == True]

# We remove every row where the longitude is between -15 and 40
data_stations = data_stations[(data_stations["longitude_station"] > -15) & (data_stations["longitude_station"] < 40)]

list_codes = data_stations['code_station'].tolist()
codes = set(list_codes)

import re
from bs4 import BeautifulSoup

# WebScrapping pour récupérer les limites de chaque station (Crue du 29/01/2018)
dict_limites = {}
url = "https://www.hydro.eaufrance.fr/stationhydro/R608001003/synthese"
coutn = 0

for code in codes:
    url = f"https://www.hydro.eaufrance.fr/stationhydro/{code}/synthese"
    
    try:
        data_limites = pd.read_html(url, match='Janvier', flavor='lxml')[0]
        data_limites = data_limites.rename(columns={'Unnamed: 0':'Mois'})
        data_limites.to_csv(f'/home/louiscockenpot/Documents/real-time-flood-alerts/data_limites/data_limites_{code}',columns=['Mois','QmM  Débit moyen mensuel (en l/s)','Qsp  Débit spécifique (en l/s/km²)','Lame d\'eau  (en mm)'],index=False)
        print(f"{code} table saved")
        coutn = coutn+1
    except (ValueError, HTTPError):
        print(f'no limits found for {code}')

print("Total",coutn)

    


