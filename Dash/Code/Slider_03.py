import dash
import dash_html_components as html
import dash_core_components as dcc

app = dash.Dash()
app.layout = html.Div([
    dcc.Slider(
        id='my-slider',
        min=-88,
        max=88,
        step=1,
        value=0,
        marks = {
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
    html.Div(id='slider-output-container')
])


@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('my-slider', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)


if __name__ == '__main__':
    app.run_server()