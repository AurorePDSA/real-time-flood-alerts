import pandas as pd
import plotly.express as px
from meteofrance_api import MeteoFranceClient

file_path = "../coord_stations_exploitables.txt"

df = pd.read_csv(file_path, sep=',', names=['Latitude', 'Longitude'])
df = df.head(50)

# Initialisation du client MeteoFrance
client = MeteoFranceClient()

def get_precipitation(lat, lon, client):
    try:
        obs = client.get_rain(lat, lon)
        forecast = obs.forecast
        total_rain = sum(item['rain'] for item in forecast)
        avg = total_rain / len(forecast)
        return forecast, avg
    except Exception as e:
        print(f"Erreur lors de la récupération des données météorologiques : {e}")
        return [], 0


df['Forecast'], df['Precipitation'] = zip(
    *df.apply(lambda row: get_precipitation(row['Latitude'], row['Longitude'], client), axis=1))

fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", color="Precipitation",
                        color_continuous_scale=px.colors.sequential.Blues, zoom=4, center={'lat': 46.5, 'lon': 2.7274})
fig.update_layout(mapbox_style="open-street-map")
fig.show()