# -*- coding: utf-8 -*-

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import plotly
import plotly.graph_objs as go

import numpy as np
import math
import pandas as pd

T = np.arange(20)

act_slope = []
est_slope = []
angles = np.arange(-89, 90, 1)


def estimate_coef(x, y):
    # number of observations/points
    n = np.size(x)

    # mean of x and y vector
    m_x, m_y = np.mean(x), np.mean(y)

    # calculating cross-deviation and deviation about x
    SS_xy = np.sum(y * x - n * m_y * m_x)
    SS_xx = np.sum(x * x - n * m_x * m_x)

    # calculating regression coefficients
    b_1 = SS_xy / SS_xx
    b_0 = m_y - b_1 * m_x

    return b_0, b_1


def method_1(y_0):
    y_1 = y_0 * T + np.random.normal(0, 0.08, len(T))
    b = estimate_coef(T, y_1)
    return b[1]


for angle in angles:
    y0 = math.tan(angle / 180 * math.pi) * 0.08
    act_slope.append(y0)
    est_slope.append(method_1(y0))

# Simulations
angles_rand = np.random.uniform(-88, 88, size=10000)
df = pd.DataFrame({'angles': angles_rand})
df['Act'] = df['angles'].apply(lambda x: math.tan(x / 180 * math.pi) * 0.08)
df['Est 1'] = df['Act'].apply(lambda x: method_1(x))
df['Error 1'] = df['Act'] - df['Est 1']

app = dash.Dash()
app.layout = html.Div([
    dcc.Slider(
        id='my-slider',
        min=-88,
        max=88,
        step=1,
        value=0,
        marks={
            -89: {'label': '-89', 'style': {'color': 'rgb(70, 130, 180)'}},
            -80: {'label': '-80', 'style': {'color': 'rgb(70, 130, 180)'}},
            -70: {'label': '-70', 'style': {'color': 'rgb(70, 130, 180)'}},
            -60: {'label': '-60', 'style': {'color': 'rgb(70, 130, 180)'}},
            -50: {'label': '-50', 'style': {'color': 'rgb(70, 130, 180)'}},
            -40: {'label': '-40', 'style': {'color': 'rgb(70, 130, 180)'}},
            -30: {'label': '-30', 'style': {'color': 'rgb(70, 130, 180)'}},
            -20: {'label': '-20', 'style': {'color': 'rgb(70, 130, 180)'}},
            -10: {'label': '-10', 'style': {'color': 'rgb(70, 130, 180)'}},
            0: {'label': '0', 'style': {'color': 'rgb(70, 130, 180)'}},
            10: {'label': '10', 'style': {'color': 'rgb(70, 130, 180)'}},
            20: {'label': '20', 'style': {'color': 'rgb(70, 130, 180)'}},
            30: {'label': '30', 'style': {'color': 'rgb(70, 130, 180)'}},
            40: {'label': '40', 'style': {'color': 'rgb(70, 130, 180)'}},
            50: {'label': '50', 'style': {'color': 'rgb(70, 130, 180)'}},
            60: {'label': '60', 'style': {'color': 'rgb(70, 130, 180)'}},
            70: {'label': '70', 'style': {'color': 'rgb(70, 130, 180)'}},
            80: {'label': '80', 'style': {'color': 'rgb(70, 130, 180)'}},
            89: {'label': '89', 'style': {'color': 'rgb(70, 130, 180)'}}
        },
        included=False
    ),
    html.Br(),
    html.Div(id='slider-output-container'),

    html.Br(),
    html.Div([dcc.Graph(id='graph-1')]),

    html.Br(),
    html.Div([dcc.Graph(
        id='graph-2',
        figure={
            'data': [
                {'x': angles, 'y': act_slope, 'mode': 'markers', 'name': 'Act'},
                {'x': angles, 'y': est_slope, 'mode': 'markers', 'name': 'Est'}, ],
            'layout': {
                'title': 'Slope Comparison',
                'xaxis': dict(title='Degree'),
                'yaxis': dict(title='Slope'),
            }
        }
    )]),

    html.Br(),
    html.Div([dcc.Graph(
        id='graph-3',
        figure={
            'data': [
                {'y': df['Error 1'], 'type': 'box', 'name': 'Act',
                 'boxpoints': 'all',
                 'jitter': 0.3,
                 "pointpos": -1.8}],
            'layout': {
                'title': 'Slope Comparison'
            }
        }
    )]),

])


@app.callback(
    Output('graph-1', 'figure'),
    [Input('my-slider', 'value')])
def update_figure(angle):
    y_0 = math.tan(angle / 180 * math.pi) * 0.08 * T
    y_1 = y_0 + np.random.normal(0, 0.08, len(T))

    traces = []
    traces.append(go.Scatter(
        x=T,
        y=y_0,
        mode='markers',
        name='Actual value'
    )
    )
    traces.append(go.Scatter(
        x=T,
        y=y_1,
        mode='markers',
        name='Noisy value'
    )
    )
    return {
        'data': traces,
        'layout': go.Layout(
            title='Slope data (angle = {})'.format(angle),
            xaxis=dict(title='itr'),
            yaxis=dict(title='Value')
        )
    }


if __name__ == '__main__':
    app.run_server()
