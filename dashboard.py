import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
import json

# load and flatten data
try:
    with open('tcas_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.json_normalize(data)
except FileNotFoundError:
    print("Error: 'tcas_data.json' not found.")
    exit()

# clean tuition
df['tuition_per_semester'] = pd.to_numeric(df['tuition_fee'], errors='coerce')

# get filter values
all_keywords = sorted(list(df['keywords'].explode().dropna().unique()))
all_program_types = sorted(df['program_type'].dropna().unique())
round_columns = [col for col in df.columns if col.startswith("admission_rounds.")]
round_names = [col.split("admission_rounds.")[1] for col in round_columns]

# initialize app
external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap',
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css'
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Layout 
app.layout = html.Div(className='main-container', children=[

    html.H1("TCAS Program Analysis Dashboard", className='header'),

    # Filters
    html.Div(className='row', children=[
        html.Div(className='card chart-card full-width', children=[
            html.H4("Filter Data", style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(className='row', children=[
                html.Div(style={'flex': 1, 'marginRight': '10px'}, children=[
                    html.Label("Keyword"),
                    dcc.Dropdown(
                        id='keyword-dropdown',
                        options=[{'label': k, 'value': k} for k in all_keywords],
                        multi=True,
                        placeholder="Select keywords..."
                    )
                ]),
                html.Div(style={'flex': 1, 'marginRight': '10px'}, children=[
                    html.Label("Program Type"),
                    dcc.Dropdown(
                        id='type-dropdown',
                        options=[{'label': t, 'value': t} for t in all_program_types],
                        multi=True,
                        placeholder="Select program types..."
                    )
                ]),
                html.Div(style={'flex': 1}, children=[
                    html.Label("Admission Round"),
                    dcc.Dropdown(
                        id='round-dropdown',
                        options=[{'label': r, 'value': r} for r in round_names],
                        multi=True,
                        placeholder="Select admission rounds (with 'รับ')..."
                    )
                ])
            ])
        ])
    ]),

    html.Div(className='row', id='kpi-row'),

    html.Div(className='row', children=[
        html.Div(dcc.Graph(id='avg-tuition-bar'), className='card chart-card two-thirds'),
        html.Div(dcc.Graph(id='program-type-donut'), className='card chart-card one-third')
    ]),

    html.Div(className='row', children=[
        html.Div(dcc.Graph(id='tuition-dist-hist'), className='card chart-card full-width')
    ]),

    # Download
    html.Div(className='row', style={'margin': '20px 0'}, children=[
        html.A("Download Filtered Data as CSV", id="download-link", download="filtered_programs.csv",
            href="", target="_blank", style={
                "fontSize": "16px", "color": "#2980b9", "textDecoration": "none"
            })
    ]),

    # Table
    html.Div(className='card data-table-card', children=[
        html.H3("Explore Program Data"),
        dash_table.DataTable(
            id='data-table',
            columns=[
                {"name": "Program Name", "id": "program_name", "presentation": "markdown"},
                *[
                    {"name": i.replace('_', ' ').title(), "id": i}
                    for i in df.columns if i not in ['url', 'program_name']
                ]
            ],
            style_cell={'fontFamily': 'Lato, sans-serif', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            page_size=10,
        )
    ])
])

@app.callback(
    [Output('kpi-row', 'children'),
    Output('avg-tuition-bar', 'figure'),
    Output('program-type-donut', 'figure'),
    Output('tuition-dist-hist', 'figure'),
    Output('data-table', 'data'),
    Output('download-link', 'href')],
    [Input('keyword-dropdown', 'value'),
    Input('type-dropdown', 'value'),
    Input('round-dropdown', 'value')]
)

def update_dashboard(selected_keywords, selected_types, selected_rounds):
    dff = df.copy()

    # Filters
    if selected_keywords:
        dff = dff[dff['keywords'].apply(lambda x: any(k in x for k in selected_keywords))]

    if selected_types:
        dff = dff[dff['program_type'].isin(selected_types)]

    if selected_rounds:
        for r in selected_rounds:
            col = f"admission_rounds.{r}"
            if col in dff.columns:
                dff = dff[dff[col].fillna('').str.contains("รับ")]

    # Add Markdown links
    dff['program_name'] = dff.apply(
        lambda row: f"[{row['program_name']}]({row['url']})", axis=1
    )

    dff_clean = dff.dropna(subset=['tuition_per_semester'])

    # KPIs
    total_programs = len(dff)
    avg_tuition = int(dff_clean['tuition_per_semester'].mean()) if not dff_clean.empty else 0
    university_count = dff['university'].nunique()

    kpi_cards = [
        html.Div(className='kpi-card', children=[
            html.I(className='fas fa-book-open kpi-icon'),
            html.P("Total Programs", className='kpi-title'),
            html.H3(f"{total_programs:,}", className='kpi-number')
        ]),
        html.Div(className='kpi-card', children=[
            html.I(className='fas fa-wallet kpi-icon'),
            html.P("Avg. Semester Tuition", className='kpi-title'),
            html.H3(f"฿{avg_tuition:,.0f}", className='kpi-number')
        ]),
        html.Div(className='kpi-card', children=[
            html.I(className='fas fa-university kpi-icon'),
            html.P("Universities Found", className='kpi-title'),
            html.H3(f"{university_count}", className='kpi-number')
        ])
    ]

    # Charts
    tuition_bar_df = dff_clean.groupby('university')['tuition_per_semester'].mean().round(0).astype(int).sort_values(ascending=False).reset_index().head(15)
    program_type_counts = dff['program_type'].value_counts().reset_index()
    program_type_counts.columns = ['program_type', 'count']

    PRIMARY_COLOR = "#2c3e50"
    ACCENT_COLOR = "#f39c12"

    def style_fig(fig, title):
        return fig.update_layout(
            title_text=title,
            font=dict(family="Lato, sans-serif", color=PRIMARY_COLOR),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=60, b=40)
        )

    fig_bar = px.bar(
        tuition_bar_df, x='tuition_per_semester', y='university', orientation='h',
        text='tuition_per_semester'
    )
    fig_bar.update_traces(marker_color=PRIMARY_COLOR, texttemplate='%{text:,.0f}', textposition='inside')
    style_fig(fig_bar, "Average Tuition per Semester (Top 15)")

    fig_donut = px.pie(
        program_type_counts, names='program_type', values='count', hole=0.5,
        color_discrete_sequence=[PRIMARY_COLOR, ACCENT_COLOR, "#34495e", "#95a5a6"]
    )
    style_fig(fig_donut, "Program Type Distribution")

    fig_hist = px.histogram(dff_clean, x='tuition_per_semester', nbins=20)
    fig_hist.update_traces(marker_color=ACCENT_COLOR)
    style_fig(fig_hist, "Distribution of Semester Tuition Fees")

    table_data = dff.to_dict('records')
    csv_string = dff.to_csv(index=False, encoding='utf-8-sig')
    csv_href = "data:text/csv;charset=utf-8," + csv_string

    return kpi_cards, fig_bar, fig_donut, fig_hist, table_data, csv_href

if __name__ == '__main__':
    app.run(debug=True)
