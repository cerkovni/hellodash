# coding=utf-8

import dash
import dash_core_components as dcc
import dash_table_experiments as dt
import dash_html_components as html
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from pandas.io import gbq
from flask import Flask
from google.cloud import bigquery

server = Flask(__name__)
app = dash.Dash(__name__, server=server)
app.scripts.config.serve_locally = True
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# df = pd.read_feather('hellodash_medicare_ds1.feather')
client = bigquery.Client()
sql = """
SELECT
  OP.provider_state AS State,
  OP.provider_city AS City,
  OP.provider_id AS Provider_ID,
  ROUND(OP.average_OP_cost) AS Average_OP_Cost,
  ROUND(IP.average_IP_cost) AS Average_IP_Cost,
  ROUND(OP.average_OP_cost + IP.average_IP_cost) AS Combined_Average_Cost
FROM (
  SELECT
    provider_state,
    provider_city,
    provider_id,
    SUM(average_total_payments*outpatient_services)/SUM(outpatient_services) AS average_OP_cost
  FROM
    `bigquery-public-data.medicare.outpatient_charges_2014`
  GROUP BY
    provider_state,
    provider_city,
    provider_id ) AS OP
INNER JOIN (
  SELECT
    provider_state,
    provider_city,
    provider_id,
    SUM(average_medicare_payments*total_discharges)/SUM(total_discharges) AS average_IP_cost
  FROM
    `bigquery-public-data.medicare.inpatient_charges_2014`
  GROUP BY
    provider_state,
    provider_city,
    provider_id ) AS IP
ON
  OP.provider_id = IP.provider_id
  AND OP.provider_state = IP.provider_state
  AND OP.provider_city = IP.provider_city
ORDER BY
  combined_average_cost DESC
LIMIT
  10000;
"""
df = client.query(sql).to_dataframe()
app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),
    dcc.Graph(
        id='IP vs OP ',
        figure={
            'data': [
                go.Scatter(
                    x=df[df['City'] == i]['Average_IP_Cost'],
                    y=df[df['City'] == i]['Average_OP_Cost'],
                    text=df[df['City'] == i]['State'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 3,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                ) for i in df.City.unique()
            ],
            'layout': go.Layout(
                xaxis={ 'title': 'Average_IP_Cost'},
                yaxis={'title': 'Average_OP_Cost'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                legend={'x': 1, 'y': 1},
                hovermode='closest'
            )
        }
    ), 
	
    dt.DataTable(
        rows= df.to_dict('records'),
        columns=sorted(df.columns),  # optional - sets the order of columns
        row_selectable=True,
        filterable=True,
        sortable=True,
        selected_row_indices=[],
        id='datatable-df'
    )

])

# app.layout = html.Div(...)
# @app.callback(...)
# def update_figure():


if __name__ == '__main__':
	app.run_server()
