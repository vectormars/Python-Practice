import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import numpy as np
import pandas as pd

app = dash.Dash()

os.chdir('C:\\Users\\c257458\\Desktop\\Dash')
df = pd.read_csv('C:\\Users\\c257458\\Desktop\\Dash\\OldFaithful.csv')


app.layout = html.Div([
    dcc.Graph(
        id = 'image1',
        figure = {
            'data':[
                go.Scatter(
                    x = df['X'],
                    y = df['Y'],
                    mode = 'markers',
                    marker = {
                        'size': 12,
                        'color': 'rgb(51,204,153)',
                        'symbol': 'pentagon',
                        'line': {'width': 2}
                        }
                    )
                ],
            'layout': go.Layout(
                title = 'Old Faithful Eruption Intervals v Durations',
                xaxis = {'title': 'Duration of eruption (minutes)'},
                yaxis = {'title': 'Interval to next eruption (minutes)'},
                hovermode='closest'
            )
        }
        )
    ])
    
if __name__ == '__main__':
    app.run_server()