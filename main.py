# coding=utf-8

import dash
import dash_core_components as dcc
import dash_table_experiments as dt
import dash_html_components as html
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from pandas.io import gbq
from flask_session import Session
from flask import Flask, render_template
import sys
import traceback
import datetime

from flask_login import UserMixin
from flask_login_auth import FlaskLoginAuth
from google.cloud import bigquery

from sklearn.linear_model import enet_path
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.cross_validation import train_test_split
from sklearn.externals import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error


server = Flask(__name__)
app = dash.Dash(__name__, url_base_pathname='/', server=server)
app.scripts.config.serve_locally = True
auth = FlaskLoginAuth(app, use_default_views=True)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# df = pd.read_feather('hellodash_medicare_ds2.feather')



rf  = joblib.load('hellodash_rf.pkl')
df_x = df.drop(columns=['provider_type', 'average_medicare_payment_amt'])
df_x = pd.get_dummies(df_x)
df['predicted_average_medicare_payment_amt'] = rf.predict(df_x.values)
# df = df.drop(columns=['provider_type'])
df = df[['predicted_average_medicare_payment_amt',
         'average_medicare_payment_amt', 
         'nppes_provider_state'
		 ]]
client = bigquery.Client()
sql = """
SELECT 
    line_srvc_cnt, 
    bene_unique_cnt,
    bene_day_srvc_cnt,
    provider_type,
    nppes_provider_state,
    average_medicare_allowed_amt,
    average_submitted_chrg_amt,
    average_medicare_payment_amt,
    average_medicare_standard_amt
FROM
    `bigquery-public-data.medicare.physicians_and_other_supplier_2014`
WHERE
    provider_type = "Nephrology"
Limit 
    1000000;
"""
# sql = """
# SELECT
#   OP.provider_state AS State,
#   OP.provider_city AS City,
#   OP.provider_id AS Provider_ID,
#   ROUND(OP.average_OP_cost) AS Average_OP_Cost,
#   ROUND(IP.average_IP_cost) AS Average_IP_Cost,
#   ROUND(OP.average_OP_cost + IP.average_IP_cost) AS Combined_Average_Cost
# FROM (
#   SELECT
#     provider_state,
#     provider_city,
#     provider_id,
#     SUM(average_total_payments*outpatient_services)/SUM(outpatient_services) AS average_OP_cost
#   FROM
#     `bigquery-public-data.medicare.outpatient_charges_2014`
#   GROUP BY
#     provider_state,
#     provider_city,
#     provider_id ) AS OP
# INNER JOIN (
#   SELECT
#     provider_state,
#     provider_city,
#     provider_id,
#     SUM(average_medicare_payments*total_discharges)/SUM(total_discharges) AS average_IP_cost
#   FROM
#     `bigquery-public-data.medicare.inpatient_charges_2014`
#   GROUP BY
#     provider_state,
#     provider_city,
#     provider_id ) AS IP
# ON
#   OP.provider_id = IP.provider_id
#   AND OP.provider_state = IP.provider_state
#   AND OP.provider_city = IP.provider_city
# ORDER BY
#   combined_average_cost DESC
# LIMIT
#   10000;
# """
df = client.query(sql).to_dataframe()
app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.

		This demonstrates a simple Google App Engine example where data is pulled from big query and a machine learning model
		is ran on the query with results displayed. Approximately 100k data points are queried and predicted when server boots up. 
		Most of time spent waiting is due to data query and rendering 100000 points. Dataset is for 2014 Medicare payments for nephrologists.
    '''),
   	html.Div([
    dcc.Graph(
        id='IP vs OP ',
        figure={
            'data': [
                go.Scattergl(
                    x=df[df['nppes_provider_state'] ==
                         i]['average_medicare_payment_amt'],
                    y=df[df['nppes_provider_state'] ==
                         i]['predicted_average_medicare_payment_amt'],
                    text=df[df['nppes_provider_state']
                            == i]['nppes_provider_state'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 5,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                )for i in df.nppes_provider_state.unique()

                # go.Scatter(
                #     x=df[df['nppes_provider_state'] == i]['average_medicare_payment_amt'],
                #     y=df[df['nppes_provider_state'] ==
                #          i]['predicted_average_medicare_payment_amt'],
                #     text=df[df['nppes_provider_state']
                #             == i]['nppes_provider_state'],
                #     mode='markers',
                #     opacity=0.7,
                #     marker={
                #         'size': 5,
                #         'line': {'width': 0.5, 'color': 'white'}
                #     },
                #     name=i
                # ) for i in df.nppes_provider_state.unique()
            ],
            'layout': go.Layout(
                xaxis={ 'title': 'Actual_Average_Medicare_Payment_Amount'},
                yaxis={'title': 'Preidicted_Average_Medicare_Payment_Amount'},
                margin={'l': 100, 'b': 100, 't': 100, 'r': 100, 'pad':4},
                legend={'x': 1, 'y': 1},
                hovermode='closest',
            	autosize=True
            )
        }
    ), 
	], className="ten columns", style={'margin': 20}),

    dt.DataTable(
        rows= df.to_dict('records'),
        # columns=sorted(df.columns),  # optional - sets the order of columns
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
