import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="centered")
home_tab, observations_tab, stations_tab = st.tabs(["Home", "Observations", "Stations"])

regions_codes = {'GRAND EST': "44", 'HAUTS-DE-FRANCE': "32", 'BOURGOGNE-FRANCHE-COMTE': "27", 'ILE-DE-FRANCE': "11",
                 'CENTRE-VAL DE LOIRE': "24", 'NORMANDIE': "28", 'BRETAGNE': "53", 'PAYS DE LA LOIRE': "52",
                 'AUVERGNE-RHONE-ALPES': "84", 'OCCITANIE': "76", 'NOUVELLE-AQUITAINE': "75",
                 "PROVENCE-ALPES-COTE D'AZUR": "93", 'CORSE': "94"}


@st.cache_data
def get_stations(working, regions):
    url_stations = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/stations"
    params = {"size": 6000}
    if working:  # If the user has selected to only display working stations
        params["en_service"] = 1
    if len(regions) > 0:  # If the user has selected some specific regions
        params["code_region"] = regions
    response_stations = requests.get(url_stations, params=params)
    if response_stations.status_code == '200' or '206':
        data_stations = response_stations.json()
        data_stations = pd.DataFrame(data_stations["data"])
        data_stations = data_stations[(data_stations["longitude_station"] > -15) &
                                      (data_stations["longitude_station"] < 40)]
        data_stations = data_stations.rename(columns={"latitude_station": "latitude", "longitude_station": "longitude"})
        return data_stations[["latitude", "longitude"]]
    st.write("Error while retrieving data from API")
    return None


with home_tab:
    st.markdown('<h1 style="text-align: center;">Flood visualisation using <a '
                'href="https://hubeau.eaufrance.fr/page/api-hydrometrie">Hub\'Eau\'s Hydrométrie API</a></h1>',
                unsafe_allow_html=True)
    left_col, middle_col, right_col = st.columns(3)
    with left_col:
        st.write("")
    with middle_col:
        st.image("https://api.gouv.fr/images/api-logo/hub-eau.png")
    with right_col:
        st.write("")

with observations_tab:
    st.markdown("<h1 style='text-align: center;'>Observations</h1>", unsafe_allow_html=True)

with stations_tab:
    st.markdown("<h1 style='text-align: center;'>Stations</h1>", unsafe_allow_html=True)
    regions_selected = st.multiselect("Choose a region", list(regions_codes.keys()))
    working_stations = st.checkbox("Working stations only")
    code_regions_selected = [regions_codes[region] for region in regions_selected]
    data = get_stations(working_stations, code_regions_selected)
    st.write(data.shape[0], "stations found")
    st.map(data)
