import dash_html_components as html
import dash_core_components as dcc
import dash

import plotly
import plotly.graph_objs as go
import dash_table_experiments as dte
from dash.dependencies import Input, Output, State

import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline

import json
import datetime
import operator
import os

import base64
import io

from collections import namedtuple

app = dash.Dash()

# Set base case
df_base = pd.read_excel(
    'C:\\Users\\c257458\\Desktop\\Artificial pancreas review\\Insulin Reservoir\\Capacitive Sensor\\Data\\2018 May 29 Tue\\FDC1004\\Test1\\14_52-no-noise-on-cloth-labcoat.xlsx',
    usecols=[0, 3, 4, 5])
df_base.columns = ['t', 'Volume', 'Sensor', 'Ref']
df_base['round t'] = df_base['t'].apply(round, ndigits=0)
df_base = df_base.groupby('round t').mean().reset_index()

# Apply spline for base case (find true value)
df_base_Spline = df_base.groupby('Volume').mean().reset_index().sort_values(by=['Volume'])
spl = UnivariateSpline(df_base_Spline['Volume'], df_base_Spline['Sensor'])
spl.set_smoothing_factor(0.34)


# Noise remove
def noise_removal(data):
    ref_max = 0.9000520706176756
    ref_min = 0.7775897979736323
    sense_max = 0.7217592511504041
    sense_min = -0.00010679833326410204
    k = 0.55880274

    data['Ref_MinMax'] = (data['Ref'] - ref_min) / (ref_max - ref_min)
    adjust = (data['Ref_MinMax'] * k) * (sense_max - sense_min) + sense_min
    return data['Sensor'] - adjust


def noise_removal_sample(obs, ref):
    ref_max = 0.9000520706176756
    ref_min = 0.7775897979736323
    sense_max = 0.7217592511504041
    sense_min = -0.00010679833326410204
    k = 0.55880274

    ref_min_max = (ref - ref_min) / (ref_max - ref_min)
    adjust = (ref_min_max * k) * (sense_max - sense_min) + sense_min

    return obs - adjust


# Sample
Volume_True = np.arange(3100, 400, -100)
itr = np.arange(1, len(Volume_True) + 1, 1)
LookUp_Volume = np.arange(0, 3500, 1)
LookUp_pf = spl(LookUp_Volume)
pf_True = spl(Volume_True)


def find_obs(data, value):
    # Find obs
    idx = (np.abs(data['Volume'] - value)).idxmin()
    return data['Sensor'][idx]


def find_ref(data, value):
    # Find ref
    idx = (np.abs(data['Volume'] - value)).idxmin()
    return data['Ref'][idx]


def find_volume(pf):
    idx = (np.abs(LookUp_pf-pf)).argmin()
    return LookUp_Volume[idx]


# Kalman filter
gaussian = namedtuple('Gaussian', ['mean', 'var'])


def predict(volume, d):
    # Prediction
    return gaussian(volume.mean - d, volume.var)


def gaussian_multiply(g1, g2):
    # Update
    mean = (g1.var * g2.mean + g2.var * g1.mean) / (g1.var + g2.var)
    variance = (g1.var * g2.var) / (g1.var + g2.var)
    return gaussian(mean, variance)


def update(prior, likelihood):
    posterior = gaussian_multiply(likelihood, prior)
    return posterior


# APP Setting
app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([

    html.H5("Upload Files"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False),
    html.Div(id='down_sample_value', style={'display': 'none'}),

    html.Button(
        id='submit-button',
        n_clicks=0,
        children='Submit',
        style={'fontSize': 28}
    ),

    html.Br(),
    html.Div([
        html.H5("Experimental data"),
        html.Div(dte.DataTable(rows=[{}], id='table'))
    ]),

    html.Br(),
    html.Div([
        html.H5("Down-Sampled data"),
        html.Div(dte.DataTable(rows=[{}], id='table-ds'))
    ]),

    # Data explore
    html.Br(),
    html.Div(children=[
        html.Div(dcc.Graph(id='graph-1'), className="six columns"),
        html.Div(dcc.Graph(id='graph-2'), className="six columns"),
    ], style={'width': '100%', 'display': 'inline-block'}),

    # Data reduce noise
    html.Br(),
    html.Div([
        dcc.Graph(id='graph-3')
    ]),

    html.Div(id='practical_sample_value', style={'display': 'none'}),

    # Data sample
    html.Br(),
    html.Div([
        dcc.Graph(id='graph-4')
    ]),

])


# Functions
# file upload function
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), usecols=[0, 3, 4, 5])
            df.columns = ['t', 'Volume', 'Sensor', 'Ref']
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded), usecols=[0, 3, 4, 5])
            df.columns = ['t', 'Volume', 'Sensor', 'Ref']
    except Exception as e:
        print(e)
        return None

    return df


# callback table creation (origin data)
@app.callback(Output('table', 'rows'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def update_output_1(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            return df.to_dict('records')
        else:
            return [{}]
    else:
        return [{}]


# Define down_sample function
def down_sample(data):
    data['round t'] = data['t'].apply(round, ndigits=0)
    data = data.groupby('round t').mean().reset_index()
    data = data.drop('t', axis=1)

    return data


# callback Storing Data in the Browser with a Hidden Div
@app.callback(Output('down_sample_value', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def clean_data(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            df = down_sample(df)
            return df.to_json(date_format='iso', orient='split')


# callback table creation (down_sampled data)
@app.callback(Output('table-ds', 'rows'), [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def update_table(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        return dff.to_dict('records')
    else:
        return [{}]


# callback figure creation (down_sampled data explore 1)
@app.callback(Output('graph-1', 'figure'), [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def update_graph_1(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        traces = []
        traces.append(go.Scatter(
            x=dff['round t'],
            y=dff['Sensor'],
            mode='markers',
            marker={'size': 3},
            name='Capacitance sensor')
        )
        traces.append(go.Scatter(
            x=dff['round t'],
            y=dff['Ref'],
            mode='markers',
            marker={'size': 3},
            name='Reference sensor')
        )

        return {
            'data': traces,
            'layout': go.Layout(
                title='Sensor Measurement vs. Time',
                xaxis=dict(title='Time (s)'),
                yaxis=dict(title='Capacitance (pF)'),
                legend=dict(orientation="h", xanchor="center", x=0.5, y=1.1)
            )
        }
    else:
        return {'data': []}


# callback figure creation (down_sampled data explore2)
@app.callback(Output('graph-2', 'figure'), [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def update_graph_2(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        df = pd.DataFrame(columns=['text1', 'text2'])
        df['text1'] = pd.Series(dff['Sensor'].round(2), dtype=str)
        df['text2'] = pd.Series(dff['Volume'].round(2), dtype=str) + "uL, " + df['text1'] + "pF"
        traces = []
        traces.append(go.Scatter(
            x=dff['Volume'],
            y=dff['Sensor'],
            hoverinfo="text",
            text=df['text2'],
            mode='markers',
            name='Noisy data',
            marker={'size': 3}
        )
        )
        traces.append(go.Scatter(
            x=df_base['Volume'],
            y=df_base['Sensor'],
            mode='markers',
            name='No noise data',
            marker={'size': 3}
        )
        )
        traces.append(go.Scatter(
            x=df_base['Volume'],
            y=spl(df_base['Volume']),
            name='Actual value (Spline)',
            line=dict(
                color='rgb(0, 0, 0)',
                width=2,
                dash='dash')
        )
        )

        return {
            'data': traces,
            'layout': go.Layout(
                title='Sensor Measurement vs. Volume',
                xaxis=dict(title='Volume in reservior (uL)'),
                yaxis=dict(title='Capacitance (pF)'),
                legend=dict(orientation="h", xanchor="center", x=0.5, y=1.1)
            )
        }
    else:
        return {'data': []}

    # callback figure creation (Noise removal data)


@app.callback(Output('graph-3', 'figure'), [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def update_graph_3(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        traces = []
        traces.append(go.Scatter(
            x=dff['Volume'],
            y=dff['Sensor'],
            mode='markers',
            name='Noisy data',
            marker={'size': 3}
        )
        )
        traces.append(go.Scatter(
            x=df_base['Volume'],
            y=df_base['Sensor'],
            mode='markers',
            name='No noise data',
            marker={'size': 3}
        )
        )
        traces.append(go.Scatter(
            x=df_base['Volume'],
            y=spl(df_base['Volume']),
            name='Actual value (Spline)',
            line=dict(
                color='rgb(0, 0, 0)',
                width=2,
                dash='dash')
        )
        )
        traces.append(go.Scatter(
            x=dff['Volume'],
            y=noise_removal(dff),
            mode='markers',
            name='Noise reduced data',
            marker={'size': 3}
        )
        )

        return {
            'data': traces,
            'layout': go.Layout(
                title='Noise Reduction Comparison',
                xaxis=dict(title='Volume in reservior (uL)'),
                yaxis=dict(title='Capacitance (pF)'),
                hovermode='closest',
                legend=dict(orientation="v", xanchor="center", x=0.1, y=1)
            )
        }
    else:
        return {'data': []}

    # callback figure creation (Sample data)


@app.callback(Output('practical_sample_value', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def sample_table(n_clicks, jsonified_cleaned_data):
    # callback Storing Data in the Browser with a Hidden Div (sampled data, per 10 units)
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        dff_1 = dff.copy()
        pf_obs = [find_obs(dff_1, x) for x in Volume_True]
        dff_2 = dff.copy()
        pf_ref = [find_ref(dff_2, x) for x in Volume_True]

        pf_adjust_obs = []
        for i in np.arange(len(pf_obs)):
            pf_adjust_obs.append(noise_removal_sample(pf_obs[i], pf_ref[i]))

        volume_adj = [find_volume(x) for x in pf_adjust_obs]

        df = pd.DataFrame({'pf Obs': pf_obs})

        df['pf Adj'] = pf_adjust_obs
        df['vol Adj'] = volume_adj
        df['vol Act'] = Volume_True
        df['pf Act'] = pf_True

        return df.to_json(date_format='iso', orient='split')


@app.callback(Output('graph-4', 'figure'),
              [Input('submit-button', 'n_clicks')],
              [State('down_sample_value', 'children')])
def update_graph_4(n_clicks, jsonified_cleaned_data):
    # Figure for sampled data (10 units each)
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        dff_1 = dff.copy()
        pf_obs = [find_obs(dff_1, x) for x in Volume_True]
        dff_2 = dff.copy()
        pf_ref = [find_ref(dff_2, x) for x in Volume_True]

        adjust_obs = []
        for i in np.arange(len(pf_obs)):
            adjust_obs.append(noise_removal_sample(pf_obs[i], pf_ref[i]))

        traces = []
        # Obs Data
        traces.append(go.Scatter(
            x=dff['Volume'],
            y=dff['Sensor'],
            mode='markers',
            name='Observed value',
            marker={'size': 3, 'color': 'rgb(70, 130, 180)'}
        )
        )
        traces.append(go.Scatter(
            x=Volume_True,
            y=pf_obs,
            mode='markers',
            name='Observed value (Sample)',
            marker={'size': 10, 'color': 'rgb(70, 130, 180)'}
        )
        )

        # Adjusted Data
        traces.append(go.Scatter(
            x=dff['Volume'],
            y=noise_removal(dff),
            mode='markers',
            name='Noise reduced data',
            marker={'size': 3, 'color': 'rgb(11, 120, 35)'}
        )
        )
        traces.append(go.Scatter(
            x=Volume_True,
            y=adjust_obs,
            mode='markers',
            name='Noise reduced data',
            marker={'size': 10, 'color': 'rgb(11, 120, 35)'}
        )
        )

        # Actual Data
        traces.append(go.Scatter(
            x=Volume_True,
            y=pf_True,
            mode='markers',
            name='Actual value (Sample)',
            marker={'size': 10, 'color': 'rgb(0, 0, 0)'}
        )
        )
        traces.append(go.Scatter(
            x=df_base['Volume'],
            y=spl(df_base['Volume']),
            name='Actual value (Spline)',
            line=dict(
                color='rgb(0, 0, 0)',
                width=2,
                dash='dash')
        )
        )

        return {
            'data': traces,
            'layout': go.Layout(
                title='Noise Reduction Comparison',
                xaxis=dict(title='Volume in reservoir (uL)'),
                yaxis=dict(title='Capacitance (pF)'),
                hovermode='closest',
                legend=dict(orientation="v", xanchor="center", x=0.1, y=1)
            )
        }
    else:
        return {'data': []}


app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

if __name__ == '__main__':
    app.run_server()
