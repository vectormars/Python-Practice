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



app = dash.Dash()

# Set base case
df_base = pd.read_excel('C:\\Users\\c257458\\Desktop\\Artificial pancreas review\\Insulin Reservoir\\Capacitive Sensor\\Data\\2018 May 29 Tue\\FDC1004\\Test1\\14_52-no-noise-on-cloth-labcoat.xlsx', usecols = [0,3,4,5])
df_base.columns = ['t', 'Volume', 'Sensor', 'Ref']
df_base['round t'] = df_base['t'].apply(round, ndigits=0)
df_base = df_base.groupby('round t').mean().reset_index()
df_base_Spline = df_base.groupby('Volume').mean().reset_index().sort_values(by=['Volume'])
spl = UnivariateSpline(df_base_Spline['Volume'], df_base_Spline['Sensor'])
spl.set_smoothing_factor(0.34)

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
    html.Div(id='intermediate-value', style={'display': 'none'}),

    
    html.Button(
        id='submit-button',
        n_clicks=0,
        children='Submit',
        style={'fontSize':28}
    ),
    
    html.Br(),
    html.Div([
        html.H5("Experimental data"),
        html.Div(dte.DataTable(rows=[{}], id='table'))
        ]),
    
    html.Br(),
    html.Div([
        html.H5("Down-sampled data"),
        html.Div(dte.DataTable(rows=[{}], id='table-ds'))
        ]),
    
    html.Br(),
    html.Div([
        dcc.Graph(id='graph-1')
        ]),
    
    html.Br(),
    html.Div([
        dcc.Graph(id='graph-2')
        ])
           
])


# Functions

# file upload function
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), usecols = [0,3,4,5])
            df.columns = ['t', 'Volume', 'Sensor', 'Ref']
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded), usecols = [0,3,4,5])
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


# Define downSample function
def downSample(data):
    data['round t'] = data['t'].apply(round, ndigits=0)
    data = data.groupby('round t').mean().reset_index()
    data = data.drop('t', axis=1)
    
    return data

# callback Storing Data in the Browser with a Hidden Div
@app.callback(Output('intermediate-value', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def clean_data(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            df = downSample(df)
            return df.to_json(date_format='iso', orient='split')


# callback table creation (downsampled data)
@app.callback(Output('table-ds', 'rows'), [Input('submit-button', 'n_clicks')], [State('intermediate-value', 'children')])
def update_table(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        return dff.to_dict('records')
    else:
        return [{}]


# callback figure creation (downsampled data explore 1)
@app.callback(Output('graph-1', 'figure'), [Input('submit-button', 'n_clicks')], [State('intermediate-value', 'children')])
def update_graph_1(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        traces = []
        traces.append(go.Scatter(
            x = dff['round t'],
            y = dff['Sensor'],
            mode = 'markers',
            marker={'size': 3},
            name = 'Capacitance sensor')
            )
        traces.append(go.Scatter(
            x = dff['round t'],
            y = dff['Ref'],
            mode = 'markers',
            marker={'size': 3},
            name = 'Reference sensor')
            )
    
        return{
            'data': traces,
            'layout': go.Layout(
                title = 'Sensor Measurement vs. Time',
                xaxis = dict(title = 'Time (s)'),
                yaxis = dict(title = 'Capacitance (pF)')  
            )
        }
    else:
        return {'data': []}


# callback figure creation (downsampled data explore2)
@app.callback(Output('graph-2', 'figure'), [Input('submit-button', 'n_clicks')], [State('intermediate-value', 'children')])
def update_graph_2(n_clicks, jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')        
        df = pd.DataFrame(columns=['text1','text2'])
        df['text1']=pd.Series(dff['Sensor'].round(2),dtype=str)
        df['text2']=pd.Series(dff['Volume'].round(2),dtype=str)+"uL, "+df['text1']+"pF"
        traces = []
        traces.append(go.Scatter(
            x = dff['Volume'],
            y = dff['Sensor'],
            hoverinfo = "text",
            text = df['text2'],
            mode = 'markers',
            name = 'Noisy data',
            marker={'size': 3}
            )
        )
        traces.append(go.Scatter(
            x = df_base['Volume'],
            y = df_base['Sensor'],
            mode = 'markers',
            name = 'Noise data',
            marker={'size': 3}
            )
        )
        traces.append(go.Scatter(
            x = df_base['Volume'],
            y = spl(df_base['Volume']),
            name = 'Actual value (Spline)',
            line = dict(
                color = ('rgb(0, 0, 0)'),
                width = 2,
                dash='dash')
            )
        )

        return{
            'data': traces,
            'layout': go.Layout(
                title = 'Sensor Measurement vs. Volume',
                xaxis = dict(title = 'Volume in reservior (uL)'),
                yaxis = dict(title = 'Capacitance (pF)')  
            )
        }
    else:
        return {'data': []}    
        
        
        
        
        
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

if __name__ == '__main__':
    app.run_server()
