import datetime
import streamlit as st
import requests
import pandas as pd
from geopy.distance import geodesic
import requests
import concurrent.futures


st.set_page_config(layout="centered")

home_tab, stations_tab, observations_tab = st.tabs(["Home", "Stations", "Observations"])

regions_codes = {'GRAND EST': "44", 'HAUTS-DE-FRANCE': "32", 'BOURGOGNE-FRANCHE-COMTE': "27", 'ILE-DE-FRANCE': "11",
                 'CENTRE-VAL DE LOIRE': "24", 'NORMANDIE': "28", 'BRETAGNE': "53", 'PAYS DE LA LOIRE': "52",
                 'AUVERGNE-RHONE-ALPES': "84", 'OCCITANIE': "76", 'NOUVELLE-AQUITAINE': "75",
                 "PROVENCE-ALPES-COTE D'AZUR": "93", 'CORSE': "94"}


@st.cache_data
def get_stations(working, regions, selected_location=None, distance=None):
    url_stations = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/stations"
    params = {"size": 6000}

    if working:
        params["en_service"] = 1

    if regions and len(regions) > 0:
        params["code_region"] = regions

    response_stations = requests.get(url_stations, params=params)
    print(response_stations.url)

    if response_stations.status_code in (200, 206):
        data_stations = response_stations.json()
        data_stations = pd.DataFrame(data_stations["data"])

        data_stations = data_stations[(data_stations["longitude_station"] > -15) &
                                      (data_stations["longitude_station"] < 40)]
        data_stations = data_stations.rename(columns={"latitude_station": "latitude", "longitude_station": "longitude"})

        if selected_location and distance is not None:
            # Filtrer les stations à une distance du point central
            central_point = (selected_location["latitude"], selected_location["longitude"])
            data_stations["distance"] = data_stations.apply(
                lambda row: geodesic((row["latitude"], row["longitude"]), central_point).kilometers,
                axis=1
            )
            data_stations = data_stations[data_stations["distance"] <= distance]
        return data_stations[["latitude", "longitude", "code_station"]]

    st.write("Erreur lors de la récupération des données depuis l'API")
    return None



# Chargez les seuils à partir des fichiers txt
with open('limites_H.txt', 'r') as file:
    limites_H_lines = file.readlines()

with open('limites_Q.txt', 'r') as file:
    limites_Q_lines = file.readlines()

# Créez des dictionnaires pour stocker les seuils
limites_H = {}
for line in limites_H_lines:
    code_station, seuil = map(str.strip, line.split(':'))
    limites_H[code_station] = float(seuil)

limites_Q = {}
for line in limites_Q_lines:
    code_station, seuil = map(str.strip, line.split(':'))
    limites_Q[code_station] = float(seuil)

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

with stations_tab:
    st.markdown("<h1 style='text-align: center;'>Stations</h1>", unsafe_allow_html=True)
    regions_selected = st.multiselect("Choose a region", list(regions_codes.keys()))
    working_stations = st.checkbox("Working stations only", value=True)
    code_regions_selected = [regions_codes[region] for region in regions_selected ]if len(regions_selected)<len(regions_codes) else []
    data = get_stations(working_stations, code_regions_selected)
    st.write(data.shape[0], "stations found")
    st.map(data)


def fetch_data(params):
    response = []
    try:
        response = requests.get("http://hubeau.eaufrance.fr/api/v1/hydrometrie/observations_tr", params=params)
        return response.status_code, response.json()["data"]

    except Exception as e:
        print(response.text, response.status_code)
        print(f'error here response: {e}')
    return 0,response



def add_color_to_data(data):
    url = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/observations_tr"
    stations = data['code_station'].tolist()

    date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=60)
    date = date.strftime("%Y-%m-%dT%H:%M:%S")

    data_hydro = pd.DataFrame()
    nombre_requetes = 0

    # Function to process each batch of requests
    def process_batch(batch_stations):
        nonlocal nombre_requetes

        batch_params = {
            "code_entite": batch_stations,
            "date_debut_obs": date,
            "grandeur_hydro": ['Q', 'H'],
            "size": 20000
        }
        print('new request')

        response = fetch_data(batch_params)

        nombre_requetes += 1
        print(f"Requete {nombre_requetes} : status code:", response[0])
        return response


    # Use ThreadPoolExecutor for multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        ##submit all tasks
        for i in range(0, len(stations), 300):
            batch_stations = stations[i:i + 300]
            future=executor.submit(process_batch, batch_stations)
            futures.append(future)
        ##process as they come in
        for future in concurrent.futures.as_completed(futures):
            try:
                response_code, response_data = future.result()
                if response_code in (200, 206):
                    data_hydro_temp = pd.DataFrame(response_data)
                    data_hydro = pd.concat([data_hydro, data_hydro_temp], ignore_index=True)
                    print(len(data_hydro_temp))
                else:
                    print(f"La requête {nombre_requetes} a échoué avec le code d'état {response_code}")
            except Exception as e:
                print(f'issue with future : {e}')


    for index, row in data.iterrows():
        for grandeur_hydro in "HQ":
            code_station = row["code_station"]

            # Trouver la ligne correspondante dans la réponse API
            matching_row = data_hydro[
                (data_hydro['code_station'] == code_station) & (data_hydro['grandeur_hydro'] == grandeur_hydro)]

            # Si la ligne correspondante existe, ajouter la valeur de resultat_obs à la colonne correspondante dans le DataFrame initial
            if not matching_row.empty:
                value = matching_row.iloc[0]["resultat_obs"]
                if grandeur_hydro == "H":
                    data.at[index, "resultat_obs_hydro"] = value
                elif grandeur_hydro == "Q":
                    data.at[index, "resultat_obs_Q"] = value

    data["color"] = ""
    data['size'] = 1.0

    for index, row in data.iterrows():
        code_station = row["code_station"]
        hauteur = row["resultat_obs_hydro"]
        debit = row["resultat_obs_Q"]

        # Comparez la hauteur aux seuils
        if code_station in limites_H:
            if hauteur > limites_H[code_station]:
                data.at[index, "color"] = "#DD0000"
                data.at[index, "size"] = 2.0
            elif hauteur > 0.75 * limites_H[code_station]:
                data.at[index, "color"] = "#FFA500"
                data.at[index, "size"] = 1.5
            else:
                data.at[index, "color"] = "#00DD00"
        else:
            data.at[index, "color"] = "#0000DD"

        # Comparez le débit aux seuils
        if code_station in limites_Q:
            if debit > limites_Q[code_station]:
                data.at[index, "color"] = "#DD0000"
                data.at[index, "size"] = 2.0
            elif debit > 0.75 * limites_Q[code_station]:
                if data.at[index, "color"] != "#DD0000":
                    data.at[index, "color"] = "#FFA500"
                    data.at[index, "size"] = 1.5
            else:
                if data.at[index, "color"] not in ["#DD0000", "#FFA500"]:
                    data.at[index, "color"] = "#00DD00"
    data.reset_index(inplace=True)


with observations_tab:
    st.markdown("<h1 style='text-align: center;'>Observations</h1>", unsafe_allow_html=True)
    search_option = st.radio("Choisissez une option de recherche", ["Aucun", "Par région", "Autour d'un point central"])

    if search_option == "Par région":
        regions_selected = st.multiselect("Choisissez une région", list(regions_codes.keys()))
        working_stations_checkbox = st.checkbox("Stations en service uniquement", value= True)
        code_regions_selected = [regions_codes[region] for region in regions_selected]
        data = get_stations(working_stations_checkbox, code_regions_selected)
        st.write(data.shape[0], "stations trouvées")
        if len(data) <= 75 * 20 or True:
            add_color_to_data(data)
            st.map(data, latitude="latitude", longitude="longitude", color="color", size='size')
        else:
            st.map(data)
    elif search_option == "Autour d'un point central":
        selected_location_input = st.text_input(
            "Entrez les coordonnées (latitude, longitude) du point central, ex: 47.037186, -0.388035")
        distance_input = st.number_input("Entrez la distance en kilomètres", min_value=0.1, max_value=100.0, step=1.0,
                                         value=40.0)

        if selected_location_input:
            selected_location = [float(coord.strip()) for coord in selected_location_input.split(',')]
            st.write(f"Point central sélectionné : {selected_location}")
            data = get_stations(st.checkbox("Stations en service uniquement", value=True), None,
                                {"latitude": selected_location[0], "longitude": selected_location[1]},
                                distance=distance_input)

            if data is not None:
                add_color_to_data(data)
                st.write(data.shape[0], "stations trouvées")
                st.map(data, latitude="latitude", longitude="longitude", color="color", size='size')
            else:
                st.warning("Aucune donnée de station disponible.")
        else:
            st.warning("Veuillez entrer les coordonnées du point central.")







