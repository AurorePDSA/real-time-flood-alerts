import requests
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
from geopandas import GeoDataFrame
import plotly.express as px
import plotly.io as pio
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
for code in codes:
    url = f"https://www.hydro.eaufrance.fr/stationhydro/{code}/synthese"
    requesting = requests.get(url)
    soup = BeautifulSoup(requesting.content, "lxml")

    paragraph_tags = soup.find_all('td')
    try:
        text = paragraph_tags[1].text        
        text2 = text.replace(' ', '')
        text3 = re.search(r'\d+ l/s', text2).group(0)
        text4 = text3[:-4]
        debit = int(text4)        
        dict_limites[code] = debit
        with open('stations.txt', 'a') as file:
            file.write(code+':'+str(debit)+'\n')
        #if hauteur < 50000:  # on élimine les valeurs abérantes ou les stations qui n'ont pas de données pour la crue de 2018
            
    except (IndexError, AttributeError):
        print("station", code, "ne peut pas fournir les données désirées")


