import dash_html_components as html
import dash_core_components as dcc
import dash

import plotly
import dash_table_experiments as dte
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np

import json
import datetime
import operator
import os

import base64
import io



app = dash.Dash()

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

    html.Br(),
    html.Div([
        html.H5("Experimental data"),
        html.Div(dte.DataTable(rows=[{}], id='table'))
        ]),
    
    html.Br(),
    html.Div([
        html.H5("Downsampled data"),
        html.Div(dte.DataTable(rows=[{}], id='table_ds'))
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







# callback table creation (downsampled data)
@app.callback(Output('table_ds', 'rows'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')])
def update_output_2(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            df['round t'] = df['t'].apply(round, ndigits=0)
            df = df.groupby('round t').mean().reset_index()
            df = df.drop('t', axis=1)
            return df.to_dict('records')
        else:
            return [{}]
    else:
        return [{}]
        



app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

if __name__ == '__main__':
    app.run_server()
