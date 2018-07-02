# -*- coding: utf-8 -*-

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State


import plotly
import plotly.graph_objs as go


import numpy as np
import math

T = np.arange(20)


app = dash.Dash()
app.layout = html.Div([
    dcc.Slider(
        id='my-slider',
        min=-88,
        max=88,
        step=1,
        value=0,
        marks={
            -88: {'label': '-88'},
            -80: {'label': '-80'},
            -70: {'label': '-70'},
            -60: {'label': '-60'},
            -50: {'label': '-50'},
            -40: {'label': '-40'},
            -30: {'label': '-30'},
            -20: {'label': '-20'},
            -10: {'label': '-10'},
            0: {'label': '0'},
            10: {'label': '10'},
            20: {'label': '20'},
            30: {'label': '30'},
            40: {'label': '40'},
            50: {'label': '50'},
            60: {'label': '60'},
            70: {'label': '70'},
            80: {'label': '80'},
            88: {'label': '88'}
        },
        included=False
    ),
    html.Br(),
    html.Div(id='slider-output-container'),

    html.Br(),
    html.Div([dcc.Graph(id='graph-1')]),

    html.Br(),
    html.Div([dcc.Graph(id='graph-2')]),

    html.Br(),
    html.Div([dcc.Graph(id='graph-3')])
])


@app.callback(
    Output('graph-1', 'figure'),
    [Input('my-slider', 'value')])
def update_figure(angle):
    y0 = math.tan(angle/180*math.pi)*0.08*T
    y1 = y0 + np.random.normal(0, 0.08,len(T))
    
    traces=[]
    traces.append(go.Scatter(
        x=T,
        y=y0,
        mode = 'markers',
        name = 'Actual value'
        )
    )
    traces.append(go.Scatter(
        x=T,
        y=y1,
        mode = 'markers',
        name = 'Noisy value'
        )
    )
    return{
        'data': traces,
        'layout': go.Layout(
            title = 'Slope data (angle = {})'.format(angle),
            xaxis = dict(title = 'itr'),
            yaxis = dict(title = 'Value')
            )
    }
    
    
    


if __name__ == '__main__':
    app.run_server()