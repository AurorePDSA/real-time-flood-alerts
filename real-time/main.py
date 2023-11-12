import pandas as pd
import plotly.express as px
from meteofrance_api import MeteoFranceClient
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

file_path = "../coord_stations_exploitables.txt"

df = pd.read_csv(file_path, sep=',', names=['Latitude', 'Longitude'])

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
                        color_continuous_scale=px.colors.sequential.Blues, size_max=15, zoom=5)
fig.update_layout(mapbox_style="open-street-map")

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    dcc.Graph(id='map', figure=fig),
    html.Div(id='precipitation-graph')
])

# Callback pour mettre à jour le graphique des prévisions
@app.callback(
    Output('precipitation-graph', 'children'),
    Input('map', 'clickData')
)
def display_precipitation(clickData):
    if clickData is not None:
        lat = clickData['points'][0]['lat']
        lon = clickData['points'][0]['lon']

        # Trouver la prévision la plus proche
        closest_forecast = df.iloc[((df['Latitude'] - lat)**2 + (df['Longitude'] - lon)**2).argmin()]['Forecast']
        df_precip = pd.DataFrame(closest_forecast)
        fig_precip = px.line(df_precip, x='dt', y='rain', title='Prévisions de précipitations')
        return dcc.Graph(figure=fig_precip)

    return "Cliquez sur un point pour voir les prévisions de précipitations."


# Lancement de l'application
if __name__ == '__main__':
    app.run_server(debug=True)
