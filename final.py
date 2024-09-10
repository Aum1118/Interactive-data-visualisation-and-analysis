#!/usr/bin/env python
# coding: utf-8

# In[5]:


import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json

file_path = '/Users/meghapatel/Downloads/dc.csv'  # Update with your file path
data = pd.read_csv(file_path)

# Load GeoJSON for India
geojson_path = '/Users/meghapatel/Downloads/india_states.geojson' 
with open(geojson_path, 'r') as file:
    geojson_data = json.load(file)

# Ensure matching names between data and GeoJSON
data['State/ UT'] = data['State/ UT'].str.strip()

# Compute the correlation matrix
correlation_matrix = data.corr(numeric_only=True)

# Create a correlation heatmap using Plotly
corr_fig = px.imshow(
    correlation_matrix,
    text_auto=True,
    aspect='auto',
    color_continuous_scale='RdBu',
    title='Correlation Matrix of PHC Attributes',
    labels={'color': 'Correlation'}
)

corr_fig.update_layout(
    width=900, height=900,
    margin=dict(l=50, r=50, t=50, b=50),
    title_x=0.5
)

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("PHC Infrastructure and Functionality Analysis", className="text-center"), className="mb-4 mt-4")
    ]),
    dbc.Tabs([
        dbc.Tab(label="Descriptive Analysis", tab_id="tab-stats", children=[
            html.Div([
                dcc.Dropdown(
                    id="state-dropdown",
                    options=[{'label': state, 'value': state} for state in data['State/ UT'].unique()],
                    value=data['State/ UT'].unique()[0],
                    clearable=False,
                    style={'margin-bottom': '20px'}
                ),
                html.Div(id="stats-table"),
            ])
        ]),
        dbc.Tab(label="Correlation Analysis", tab_id="tab-correlation", children=[
            html.Div([
                dcc.Graph(figure=corr_fig),
            ], className="mb-4")
        ]),
        dbc.Tab(label="Comparative Analysis", tab_id="tab-comparison", children=[
            html.Div([
                dcc.Checklist(
                    id="attribute-checklist",
                    options=[{'label': col, 'value': col} for col in data.columns if col != 'State/ UT'],
                    value=[data.columns[2]],
                    inline=True,
                    style={'margin-bottom': '20px'}
                ),
                dcc.Graph(id="comparison-bar-chart"),
            ])
        ]),
        dbc.Tab(label="Scatter Plot Analysis", tab_id="tab-scatter", children=[
            html.Div([
                dcc.Dropdown(
                    id="x-axis-dropdown",
                    options=[{'label': col, 'value': col} for col in data.columns if col != 'State/ UT'],
                    value=data.columns[2],
                    style={'margin-bottom': '20px'}
                ),
                dcc.Dropdown(
                    id="y-axis-dropdown",
                    options=[{'label': col, 'value': col} for col in data.columns if col != 'State/ UT'],
                    value=data.columns[3],
                    style={'margin-bottom': '20px'}
                ),
                dcc.Graph(id="scatter-plot"),
            ])
        ]),
        dbc.Tab(label="Geographical Map of India", tab_id="tab-map", children=[
            html.Div([
                dcc.Dropdown(
                    id="map-attribute-dropdown",
                    options=[{'label': col, 'value': col} for col in data.columns if col not in ['State/ UT']],
                    value='Number of PHCs Functioning',  # Update default value if needed
                    style={'margin-bottom': '20px'}
                ),
                dcc.Graph(id="india-map")
            ])
        ])
    ])
], fluid=True)

# Callbacks for Descriptive Analysis
@app.callback(
    Output("stats-table", "children"),
    Input("state-dropdown", "value")
)
def update_stats_table(selected_state):
    state_data = data[data['State/ UT'] == selected_state]

    # Benchmark against national average
    national_avg = data.mean(numeric_only=True)

    # Identify best and worst performers
    best_states = data.idxmax(numeric_only=True)
    worst_states = data.idxmin(numeric_only=True)

    # Target Achievement (assuming we have a government target for each attribute)
    targets = {'Number of PHCs Functioning': 500, 'Staff Shortage': 100}  # Example targets
    target_achievement = {col: (state_data[col].values[0] / targets.get(col, 1)) * 100 if col in targets else 'N/A'
                          for col in state_data.columns if col != 'State/ UT'}

    # Critical Thresholds
    critical_thresholds = {col: 'Critical' if state_data[col].values[0] < national_avg[col] * 0.5 else 'Safe'
                           for col in state_data.columns if col != 'State/ UT'}

    return html.Div([
        html.H4(f"Descriptive Analysis for {selected_state}", className="mb-3"),
        html.Table([
            html.Tr([html.Th("Attribute"), html.Th("Value"), html.Th("National Avg"), html.Th("Best State"), html.Th("Worst State"), html.Th("Target Achievement (%)"), html.Th("Critical Status")]),
            html.Tbody([
                html.Tr([
                    html.Td(col),
                    html.Td(state_data[col].values[0]),
                    html.Td(round(national_avg[col], 2)),
                    html.Td(best_states[col]),
                    html.Td(worst_states[col]),
                    html.Td(target_achievement.get(col, 'N/A')),
                    html.Td(critical_thresholds[col])
                ]) for col in state_data.columns if col != 'State/ UT'
            ])
        ], className="table table-striped"),
        dcc.Graph(figure=create_box_plot(state_data)),
        dcc.Graph(figure=create_histogram(state_data))
    ])

# Helper functions to create additional visualizations
def create_box_plot(state_data):
    """Create a box plot to show distribution and outliers."""
    fig = px.box(state_data, y=state_data.columns[1:], points='outliers', title='Box Plot of PHC Attributes')
    fig.update_layout(
        yaxis_title='Value',
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor='#f9f9f9'
    )
    return fig

def create_histogram(state_data):
    """Create a histogram to show the distribution of each attribute."""
    fig = px.histogram(state_data, x=state_data.columns[1], nbins=10, title=f'Distribution of {state_data.columns[1]}')
    fig.update_layout(
        xaxis_title=state_data.columns[1],
        yaxis_title='Count',
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor='#f9f9f9'
    )
    return fig

# Callbacks for Comparative Analysis
@app.callback(
    Output("comparison-bar-chart", "figure"),
    Input("attribute-checklist", "value")
)
def update_comparison_bar_chart(selected_attributes):
    if not selected_attributes:
        selected_attributes = [data.columns[2]]
    fig = px.bar(
        data, 
        x='State/ UT', 
        y=selected_attributes, 
        barmode='group',
        title='Average PHC Attributes by State/UT'
    )
    fig.update_layout(
        xaxis_title='State/UT', 
        yaxis_title='Average Values', 
        title_x=0.5,
        bargap=0.2,
        plot_bgcolor='#f9f9f9'
    )
    return fig

# Callbacks for Scatter Plot Analysis
@app.callback(
    Output("scatter-plot", "figure"),
    [Input("x-axis-dropdown", "value"), Input("y-axis-dropdown", "value")]
)
def update_scatter_plot(x_attr, y_attr):
    fig = px.scatter(
        data,
        x=x_attr,
        y=y_attr,
        color='State/ UT',
        title=f'{x_attr} vs {y_attr}'
    )
    fig.update_layout(xaxis_title=x_attr, yaxis_title=y_attr, title_x=0.5)
    return fig

# Callbacks for Map Visualization
@app.callback(
    Output("india-map", "figure"),
    Input("map-attribute-dropdown", "value")
)
def update_india_map(selected_attribute):
    fig = px.choropleth(
        data_frame=data,
        geojson=geojson_data,
        locations='State/ UT',
        featureidkey='properties.st_nm',
        color=selected_attribute,
        color_continuous_scale='Viridis',
        scope='asia',
        title=f'{selected_attribute} Distribution Across India'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, title_x=0.5)
    return fig

# Run app
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)


# In[6]:


pip install pipreqs


# In[7]:


pip list


# In[ ]:




