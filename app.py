import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# ==============================================================================
# 1. DATA LOADING & PRE-PROCESSING
# ==============================================================================

# Load dataset
df = pd.read_csv("data/22_Languages_of_the_World.csv")

# Data cleaning
df['macroarea'] = df['macroarea'].fillna('Unknown')
df['status_label'] = df['status_label'].fillna('Unknown')

# Clean family data: if is_isolate is True, family should be 'Isolate'
df.loc[df['is_isolate'] == True, 'family'] = 'Isolate (No known relatives)'
df.loc[df['is_isolate'] == True, 'family_id'] = 'isolate'
df['family'] = df['family'].fillna('Unclassified')
df['family_id'] = df['family_id'].fillna('unclassified')

# For coordinate mapping, filter out missing latitude/longitude
df_map_source = df.dropna(subset=['latitude', 'longitude']).copy()

# Semicolon-separated countries split
df['country_list'] = df['countries'].fillna('').apply(lambda x: [c.strip() for c in x.split(';') if c.strip()])

# Build country ISO-to-name mapping for top countries to enhance UI
country_names = {
    'PG': 'Papua New Guinea', 'ID': 'Indonesia', 'NG': 'Nigeria', 'IN': 'India', 
    'CM': 'Cameroon', 'AU': 'Australia', 'US': 'United States', 'BR': 'Brazil', 
    'CN': 'China', 'MX': 'Mexico', 'PH': 'Philippines', 'RU': 'Russia', 
    'CD': 'DR Congo', 'MY': 'Malaysia', 'CA': 'Canada', 'PE': 'Peru', 
    'CO': 'Colombia', 'VU': 'Vanuatu', 'TD': 'Chad', 'BO': 'Bolivia', 
    'TZ': 'Tanzania', 'NP': 'Nepal', 'ET': 'Ethiopia', 'KE': 'Kenya', 
    'MM': 'Myanmar', 'SD': 'Sudan', 'VN': 'Vietnam', 'EC': 'Ecuador', 
    'VE': 'Venezuela', 'GH': 'Ghana', 'PK': 'Pakistan', 'AR': 'Argentina',
    'SD': 'Sudan', 'AO': 'Angola', 'CF': 'Central African Republic',
    'CI': 'Ivory Coast', 'MZ': 'Mozambique', 'NZ': 'New Zealand',
    'ZA': 'South Africa', 'TH': 'Thailand', 'UG': 'Uganda', 'ZM': 'Zambia',
    'ZW': 'Zimbabwe', 'ES': 'Spain', 'FR': 'France', 'IT': 'Italy',
    'DE': 'Germany', 'GB': 'United Kingdom', 'JP': 'Japan', 'KR': 'South Korea'
}

def get_country_labels(country_codes):
    if not country_codes:
        return 'Unknown'
    labels = [country_names.get(code, code) for code in country_codes]
    return ", ".join(labels)

df['country_names_display'] = df['country_list'].apply(get_country_labels)

# Explode country codes for country-level analysis
df_exploded = df.explode('country_list')
df_exploded['country_name'] = df_exploded['country_list'].apply(lambda x: country_names.get(x, x) if pd.notnull(x) else 'Unknown')
df_exploded = df_exploded[df_exploded['country_list'].fillna('') != '']

# ==============================================================================
# 2. DASH APP SETUP
# ==============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="GlottoScope: World Languages Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

server = app.server  # Expose server for gunicorn

# Pre-calculate filter options
macroarea_options = sorted([m for m in df['macroarea'].unique() if m != 'Unknown'])
status_options = ['not endangered', 'shifting', 'threatened', 'moribund', 'nearly extinct', 'extinct', 'Unknown']

# Custom Plotly Theme Settings
plotly_template = go.layout.Template()
plotly_template.layout = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': {'color': '#f8fafc', 'family': 'Inter, sans-serif'},
    'xaxis': {'gridcolor': 'rgba(255,255,255,0.05)', 'zerolinecolor': 'rgba(255,255,255,0.1)'},
    'yaxis': {'gridcolor': 'rgba(255,255,255,0.05)', 'zerolinecolor': 'rgba(255,255,255,0.1)'},
}

# Color palette for endangerment status
status_colors = {
    'not endangered': '#34d399',  # Green
    'shifting': '#fb923c',        # Orange
    'threatened': '#f59e0b',      # Dark Orange/Amber
    'moribund': '#f87171',        # Light Red
    'nearly extinct': '#ef4444',  # Red
    'extinct': '#b91c1c',         # Dark Red
    'Unknown': '#94a3b8'          # Slate Gray
}

# ==============================================================================
# 3. COMPONENT GENERATORS (KPI Cards)
# ==============================================================================

def make_kpi_card(title, value, icon, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={'fontSize': '1.8rem', 'color': color, 'marginRight': '12px'}),
                html.Div([
                    html.H6(title, className="text-uppercase mb-0 text-muted", style={'fontSize': '0.75rem', 'letterSpacing': '0.05em'}),
                    html.H3(value, className="mb-0 font-weight-bold", style={'color': '#f8fafc', 'fontFamily': 'Outfit, sans-serif'})
                ])
            ], className="d-flex align-items-center")
        ]),
        className="glass-card mb-3",
        style={'borderLeft': f'4px solid {color}'}
    )

# ==============================================================================
# 4. APP LAYOUT
# ==============================================================================

app.layout = html.Div([
    # Top Navbar / Header
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div(
                        html.Img(src="assets/logo.svg", style={'width': '24px', 'height': '24px'}),
                        className="logo-monogram"
                    ),
                    html.Div([
                        html.H1("GlottoScope", className="mb-0 text-white", style={'fontSize': '2rem', 'background': 'linear-gradient(to right, #38bdf8, #c084fc)', 'WebkitBackgroundClip': 'text', 'WebkitTextFillColor': 'transparent'}),
                        html.P("Interactive Catalog of the World's Languages", className="mb-0 text-muted", style={'fontSize': '0.85rem'})
                    ])
                ], className="d-flex align-items-center py-3")
            ], xs=12, md=8),
            dbc.Col([
                html.Div([
                    dbc.Badge("Glottolog 5.2 Source", color="info", className="me-2", style={'fontSize': '0.8rem', 'padding': '6px 12px', 'borderRadius': '20px'}),
                    dbc.Badge(f"{len(df):,} Documented Languages", color="primary", style={'fontSize': '0.8rem', 'padding': '6px 12px', 'borderRadius': '20px'})
                ], className="d-flex justify-content-md-end align-items-center h-100 py-2")
            ], xs=12, md=4)
        ], className="border-bottom border-secondary mb-4"),
        
        # KPI Stats Row
        dbc.Row([
            dbc.Col(make_kpi_card("Total Languages", f"{len(df):,}", "🗣️", "#38bdf8"), xs=12, sm=6, lg=3),
            dbc.Col(make_kpi_card("Language Families", f"{df['family'].nunique() - 2}", "🌿", "#c084fc"), xs=12, sm=6, lg=3), # Subtract Isolate & Unclassified
            dbc.Col(make_kpi_card("Language Isolates", f"{df['is_isolate'].sum()}", "📍", "#fb923c"), xs=12, sm=6, lg=3),
            dbc.Col(make_kpi_card("Extinct Languages", f"{len(df[df['status_label'] == 'extinct']):,}", "🥀", "#f87171"), xs=12, sm=6, lg=3),
        ]),

        # Navigation Tabs
        dbc.Tabs([
            # TAB 1: WORLD MAP
            dbc.Tab(label="World Map Explorer", tab_id="tab-map", children=[
                dbc.Row([
                    # Controls Sidebar
                    dbc.Col([
                        html.Div([
                            html.H5("Filter Languages", className="mb-3 text-white border-bottom pb-2", style={'fontSize': '1.1rem'}),
                            
                            # Language Search zoom dropdown
                            html.Div([
                                html.Label("Search & Zoom to Language", className="control-label"),
                                dcc.Dropdown(
                                    id="search-language",
                                    options=[{'label': f"{row['name']} ({row['id']})", 'value': row['id']} for _, row in df.iterrows()],
                                    placeholder="Type language name...",
                                    className="dash-dropdown mb-3"
                                )
                            ]),
                            
                            # Macroarea dropdown
                            html.Div([
                                html.Label("Macroarea", className="control-label"),
                                dcc.Dropdown(
                                    id="map-filter-macroarea",
                                    options=[{'label': m, 'value': m} for m in macroarea_options],
                                    multi=True,
                                    placeholder="All Macroareas",
                                    className="dash-dropdown mb-3"
                                )
                            ]),
                            
                            # Isolate status filter
                            html.Div([
                                html.Label("Isolate Status", className="control-label"),
                                dcc.RadioItems(
                                    id="map-filter-isolate",
                                    options=[
                                        {'label': ' Show All', 'value': 'all'},
                                        {'label': ' Isolates Only', 'value': 'isolates'},
                                        {'label': ' Exclude Isolates', 'value': 'non-isolates'}
                                    ],
                                    value='all',
                                    labelClassName="d-block mb-2 text-white",
                                    className="mb-3 custom-checklist"
                                )
                            ]),
                            
                            # Endangerment Checklist
                            html.Div([
                                html.Label("Endangerment Status", className="control-label"),
                                dbc.Checklist(
                                    id="map-filter-status",
                                    options=[{'label': s.title(), 'value': s} for s in status_options],
                                    value=status_options.copy(),
                                    inline=False,
                                    className="custom-checklist"
                                )
                            ]),
                        ], className="glass-card controls-card h-100")
                    ], xs=12, md=3),

                    # Map Display
                    dbc.Col([
                        html.Div([
                            dcc.Graph(
                                id="language-map",
                                style={'height': '600px'},
                                config={'displayModeBar': False, 'scrollZoom': True}
                            )
                        ], className="glass-card map-card p-0 overflow-hidden")
                    ], xs=12, md=6),

                    # Details Sidebar
                    dbc.Col([
                        html.Div(id="language-detail-panel", className="glass-card h-100")
                    ], xs=12, md=3)
                ])
            ]),

            # TAB 2: ANALYTICS
            dbc.Tab(label="Analytics & Distributions", tab_id="tab-analytics", children=[
                # Analytics Global Filter
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Analytics Dashboard Filters", className="mb-0 text-white d-flex align-items-center h-100", style={'fontSize': '1.1rem'})
                                ], xs=12, md=4),
                                dbc.Col([
                                    dcc.Dropdown(
                                        id="analytics-filter-macroarea",
                                        options=[{'label': 'All Macroareas', 'value': 'All'}] + [{'label': m, 'value': m} for m in macroarea_options],
                                        value='All',
                                        placeholder="Filter by Macroarea",
                                        className="dash-dropdown"
                                    )
                                ], xs=12, md=8)
                            ])
                        ], className="glass-card controls-card mb-4 py-3")
                    ], width=12)
                ]),
                
                # First Row of charts
                dbc.Row([
                    # Chart 1: Endangerment Distribution
                    dbc.Col([
                        html.Div([
                            html.H5("Endangerment Status Distribution", className="text-white mb-3", style={'fontSize': '1rem'}),
                            dcc.Graph(id="chart-endangerment", config={'displayModeBar': False})
                        ], className="glass-card")
                    ], xs=12, lg=6),

                    # Chart 2: Isolate vs Family Ratio
                    dbc.Col([
                        html.Div([
                            html.H5("Isolate vs. Family Member Ratio", className="text-white mb-3", style={'fontSize': '1rem'}),
                            dcc.Graph(id="chart-isolates", config={'displayModeBar': False})
                        ], className="glass-card")
                    ], xs=12, lg=6),
                ]),

                # Second Row of charts
                dbc.Row([
                    # Chart 3: Top Language Families
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H5("Largest Language Families", className="text-white mb-0", style={'fontSize': '1rem'}),
                                html.Div([
                                    html.Label("Families to show:", className="control-label me-3 mb-0"),
                                    html.Div(
                                        dcc.Slider(
                                            id="families-slider",
                                            min=5,
                                            max=25,
                                            step=5,
                                            value=10,
                                            marks={i: str(i) for i in range(5, 26, 5)}
                                        ),
                                        className="d-inline-block",
                                        style={'width': '150px'}
                                    )
                                ], className="d-flex align-items-center")
                            ], className="d-flex justify-content-between align-items-center mb-3"),
                            dcc.Graph(id="chart-families", config={'displayModeBar': False})
                        ], className="glass-card")
                    ], xs=12, lg=6),

                    # Chart 4: Top Countries by language count
                    dbc.Col([
                        html.Div([
                            html.H5("Top Countries by Number of Languages Spoken", className="text-white mb-3", style={'fontSize': '1rem'}),
                            dcc.Graph(id="chart-countries", config={'displayModeBar': False})
                        ], className="glass-card")
                    ], xs=12, lg=6),
                ])
            ]),

            # TAB 3: EXPLORE DATA
            dbc.Tab(label="Explore Data", tab_id="tab-data", children=[
                dbc.Row([
                    # Search and filters row
                    dbc.Col([
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Search by Language Name / ID", className="control-label"),
                                    dcc.Input(
                                        id="table-search-input",
                                        type="text",
                                        placeholder="Search name...",
                                        className="form-control bg-dark text-white border-secondary mb-3",
                                        style={'borderRadius': '8px', 'height': '38px'}
                                    )
                                ], xs=12, md=4),
                                dbc.Col([
                                    html.Label("Filter Macroarea", className="control-label"),
                                    dcc.Dropdown(
                                        id="table-filter-macroarea",
                                        options=[{'label': 'All Macroareas', 'value': 'All'}] + [{'label': m, 'value': m} for m in macroarea_options],
                                        value='All',
                                        className="dash-dropdown mb-3"
                                    )
                                ], xs=12, md=4),
                                dbc.Col([
                                    html.Label("Filter Endangerment", className="control-label"),
                                    dcc.Dropdown(
                                        id="table-filter-status",
                                        options=[{'label': 'All Statuses', 'value': 'All'}] + [{'label': s.title(), 'value': s} for s in status_options],
                                        value='All',
                                        className="dash-dropdown mb-3"
                                    )
                                ], xs=12, md=4),
                            ])
                        ], className="glass-card controls-card mb-4")
                    ], width=12)
                ]),
                
                dbc.Row([
                    # Datatable
                    dbc.Col([
                        html.Div([
                            dash_table.DataTable(
                                id="languages-table",
                                columns=[
                                    {"name": "Glottocode", "id": "id"},
                                    {"name": "Language Name", "id": "name"},
                                    {"name": "ISO 639-3", "id": "iso639p3code"},
                                    {"name": "Macroarea", "id": "macroarea"},
                                    {"name": "Language Family", "id": "family"},
                                    {"name": "Endangerment Status", "id": "status_label"}
                                ],
                                page_current=0,
                                page_size=12,
                                page_action="custom",
                                sort_action="custom",
                                sort_mode="single",
                                sort_by=[],
                                row_selectable="single",
                                selected_rows=[],
                                style_as_list_view=True,
                                style_header={
                                    'backgroundColor': 'rgba(15, 23, 42, 0.9)',
                                    'color': '#f8fafc',
                                    'fontWeight': '600',
                                    'border': '1px solid rgba(255,255,255,0.08)',
                                    'fontFamily': 'Outfit, sans-serif'
                                },
                                style_cell={
                                    'backgroundColor': 'transparent',
                                    'color': '#cbd5e1',
                                    'padding': '12px 15px',
                                    'border': '1px solid rgba(255,255,255,0.05)',
                                    'textAlign': 'left',
                                    'fontSize': '0.9rem'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'state': 'selected'},
                                        'backgroundColor': 'rgba(56, 189, 248, 0.12)',
                                        'border': '1px solid var(--accent-blue)'
                                    },
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgba(255, 255, 255, 0.01)'
                                    }
                                ]
                            )
                        ], className="glass-card")
                    ], xs=12, md=8),

                    # Sidebar details (same panel updated dynamically)
                    dbc.Col([
                        html.Div(id="table-detail-panel", className="glass-card h-100")
                    ], xs=12, md=4)
                ])
            ]),
            
            # TAB 4: ABOUT & HELP
            dbc.Tab(label="About & Help", tab_id="tab-about", children=[
                dbc.Row([
                    # Column 1: Project & Dataset Info
                    dbc.Col([
                        html.Div([
                            html.H4("About GlottoScope", className="text-white border-bottom pb-2 mb-3", style={'fontFamily': 'Outfit'}),
                            html.P([
                                "GlottoScope is an interactive, server-backed data dashboard designed to analyze and visualize the geographic distribution, genealogical classification, and endangerment levels of the world's languages. This application serves as a tool for linguists, researchers, educators, and language enthusiasts to explore the diversity and vulnerability of global languages.",
                            ], className="text-muted", style={'fontSize': '0.95rem', 'lineHeight': '1.6'}),
                            
                            html.H5("Dataset & Sources", className="text-white mt-4 mb-2", style={'fontFamily': 'Outfit'}),
                            html.P([
                                "The dashboard is built on the ",
                                html.A("Languages of the World dataset", href="https://www.kaggle.com/datasets/ibrahimqasimi/languages-of-the-world-8612-languages", target="_blank", style={'color': 'var(--accent-blue)', 'textDecoration': 'none'}),
                                " (sourced from Glottolog 5.2). It comprises records for ",
                                html.Strong("8,612 languages"),
                                " and language variants worldwide. Key attributes tracked include Glottocode identifiers, genealogical family, geographic coordinates (latitude and longitude), macroarea location, ISO 639-3 codes, isolate status, and endangerment classification."
                            ], className="text-muted", style={'fontSize': '0.95rem', 'lineHeight': '1.6'}),
                            
                            html.H5("Linguistic Concepts Explained", className="text-white mt-4 mb-2", style={'fontFamily': 'Outfit'}),
                            html.Ul([
                                html.Li([html.Strong("Language Family: "), "A group of languages related through descent from a common ancestral language."]),
                                html.Li([html.Strong("Language Isolate: "), "A language with no demonstrable genealogical relationship to any other language—a family consisting of only one member."]),
                                html.Li([html.Strong("Macroarea: "), "Continental-scale regions used to group languages geographically (e.g., Eurasia, Africa, Sahul, South America, North America, Papunesia)."]),
                                html.Li([html.Strong("Endangerment Status: "), "A categorization indicating the vitality of a language, ranging from 'not endangered' (vibrant community of speakers) to 'extinct' (no speakers remaining)."])
                            ], className="text-muted", style={'fontSize': '0.95rem', 'lineHeight': '1.6', 'paddingLeft': '20px'}),
                            
                            html.H5("Credits & Technologies", className="text-white mt-4 mb-2", style={'fontFamily': 'Outfit'}),
                            html.P([
                                "Developed as part of the Data Visualization course assignment using ",
                                html.Strong("Python Dash"),
                                ", ",
                                html.Strong("Plotly"),
                                ", and ",
                                html.Strong("Dash Bootstrap Components"),
                                ". The project uses ",
                                html.Strong("uv"),
                                " for modern Python dependency management and Docker for containerized deployment."
                            ], className="text-muted", style={'fontSize': '0.95rem', 'lineHeight': '1.6'})
                        ], className="glass-card h-100")
                    ], xs=12, md=6),
                    
                    # Column 2: Dashboard Tasks & Help Guide
                    dbc.Col([
                        html.Div([
                            html.H4("Key Analysis Tasks", className="text-white border-bottom pb-2 mb-3", style={'fontFamily': 'Outfit'}),
                            html.P("GlottoScope enables you to perform several concrete analysis tasks:", className="text-muted", style={'fontSize': '0.95rem'}),
                            html.Ol([
                                html.Li([html.Strong("Geographic Distribution: "), "Filter and visualize where language families and isolates are spoken globally."]),
                                html.Li([html.Strong("Endangerment Assessment: "), "Identify regions or families with high concentrations of threatened, moribund, or extinct languages."]),
                                html.Li([html.Strong("Isolate Analysis: "), "Isolate and inspect languages that stand alone without any sister languages."]),
                                html.Li([html.Strong("Density Comparison: "), "Compare countries and macroareas to see which regions boast the highest linguistic diversity."]),
                                html.Li([html.Strong("Individual Language Lookup: "), "Search for specific languages to inspect their coordinates, genealogical family, status, and country affiliations."])
                            ], className="text-muted mb-4", style={'fontSize': '0.95rem', 'lineHeight': '1.6', 'paddingLeft': '20px'}),
                            
                            html.H4("Interactive Help Guide", className="text-white border-bottom pb-2 mb-3", style={'fontFamily': 'Outfit'}),
                            html.Div([
                                html.Div([
                                    html.Span("🗺️", style={'fontSize': '1.3rem', 'marginRight': '10px'}),
                                    html.Div([
                                        html.Strong("World Map Explorer", style={'color': 'var(--accent-blue)'}),
                                        html.P("Use the dropdown filters on the left to filter by macroarea, endangerment status, or isolate status. Search for a language to auto-zoom the map. Click on any point on the map to display its metadata card in the right sidebar.", className="mb-0 text-muted", style={'fontSize': '0.85rem'})
                                    ])
                                ], className="d-flex mb-3"),
                                html.Div([
                                    html.Span("📊", style={'fontSize': '1.3rem', 'marginRight': '10px'}),
                                    html.Div([
                                        html.Strong("Analytics & Distributions", style={'color': 'var(--accent-purple)'}),
                                        html.P("View global distributions of endangerment levels, isolates, and major language families. Filter the whole analytics view by macroarea or use the family slider to customize the horizontal family bar chart.", className="mb-0 text-muted", style={'fontSize': '0.85rem'})
                                    ])
                                ], className="d-flex mb-3"),
                                html.Div([
                                    html.Span("🔍", style={'fontSize': '1.3rem', 'marginRight': '10px'}),
                                    html.Div([
                                        html.Strong("Explore Data (Datatable)", style={'color': 'var(--accent-green)'}),
                                        html.P("Search the entire dataset of 8,612 languages. Filter by name/ID, macroarea, or endangerment level. Click on any row in the table to display the detail card in the right sidebar. Sort the table columns dynamically.", className="mb-0 text-muted", style={'fontSize': '0.85rem'})
                                    ])
                                ], className="d-flex")
                            ])
                        ], className="glass-card h-100")
                    ], xs=12, md=6)
                ])
            ])
        ], id="tabs-container", active_tab="tab-map", className="custom-tabs")
    ], fluid=True, className="px-4 py-3")
], className="main-container")

# ==============================================================================
# 5. STATE SYNCHRONIZATION & CROSS-FILTERING CALLBACKS
# ==============================================================================

# Shared Detail Panel callback
@app.callback(
    [Output("language-detail-panel", "children"),
     Output("table-detail-panel", "children"),
     Output("search-language", "value")],
    [Input("language-map", "clickData"),
     Input("languages-table", "selected_rows"),
     Input("search-language", "value")],
    [State("languages-table", "page_current"),
     State("languages-table", "page_size"),
     State("table-search-input", "value"),
     State("table-filter-macroarea", "value"),
     State("table-filter-status", "value"),
     State("languages-table", "sort_by")]
)
def update_details(click_data, selected_rows, search_val, page_current, page_size, tbl_search, tbl_macroarea, tbl_status, sort_by):
    # Determine which input triggered the callback
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = 'none'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    selected_lang_id = None

    if trigger_id == 'search-language' and search_val:
        selected_lang_id = search_val
    elif trigger_id == 'language-map' and click_data:
        try:
            selected_lang_id = click_data['points'][0]['customdata'][0]
        except (KeyError, IndexError, TypeError):
            pass
    elif trigger_id == 'languages-table' and selected_rows:
        # Filter table data exactly as it is filtered inside the table callback to match indices
        dff = df.copy()
        if tbl_search:
            dff = dff[dff['name'].str.contains(tbl_search, case=False, na=False) | 
                      dff['id'].str.contains(tbl_search, case=False, na=False)]
        if tbl_macroarea and tbl_macroarea != 'All':
            dff = dff[dff['macroarea'] == tbl_macroarea]
        if tbl_status and tbl_status != 'All':
            dff = dff[dff['status_label'] == tbl_status]
        
        if len(sort_by):
            col_id = sort_by[0]['column_id']
            ascending = sort_by[0]['direction'] == 'asc'
            dff = dff.sort_values(by=col_id, ascending=ascending)

        # Get selected language from page index
        row_idx = selected_rows[0]
        actual_idx = page_current * page_size + row_idx
        if actual_idx < len(dff):
            selected_lang_id = dff.iloc[actual_idx]['id']

    # Default view if nothing is selected
    if not selected_lang_id:
        placeholder = html.Div([
            html.Div("ℹ️", style={'fontSize': '2.5rem', 'marginBottom': '15px', 'color': 'var(--accent-blue)'}),
            html.H5("No Language Selected", className="text-white", style={'fontFamily': 'Outfit'}),
            html.P("Click on a language node on the map, select a row in the Explore Table, or use the search bar above to view detailed linguistic data.", className="text-muted mb-0", style={'fontSize': '0.9rem'})
        ], className="text-center py-5 px-3 d-flex flex-column align-items-center justify-content-center h-100")
        return placeholder, placeholder, dash.no_update

    # Extract language info
    lang_row = df[df['id'] == selected_lang_id]
    if lang_row.empty:
        placeholder = html.Div("Language details not found.")
        return placeholder, placeholder, dash.no_update
        
    lang = lang_row.iloc[0]

    # Generate details panel HTML
    badge_class = f"badge-status status-{lang['status_label'].replace(' ', '-')}"
    
    details_content = html.Div([
        html.H4(lang['name'], className="detail-title mb-1"),
        html.P(f"Glottolog ID: {lang['id']}", className="text-muted mb-3", style={'fontSize': '0.85rem'}),
        
        html.Div([
            html.Div("Endangerment Status", className="detail-label"),
            html.Div(lang['status_label'].title(), className=badge_class),
        ], className="mb-3"),

        html.Div([
            html.Div("Language Family", className="detail-label"),
            html.Div(lang['family'], className="detail-value", style={'fontWeight': '500', 'color': 'var(--accent-purple)'}),
        ]),

        html.Div([
            html.Div("Macroarea", className="detail-label"),
            html.Div(lang['macroarea'], className="detail-value"),
        ]),

        html.Div([
            html.Div("ISO 639-3 Code", className="detail-label"),
            html.Div(lang['iso639p3code'] if pd.notnull(lang['iso639p3code']) else "None", className="detail-value"),
        ]),

        html.Div([
            html.Div("Isolate Status", className="detail-label"),
            html.Div("Yes (Isolate)" if lang['is_isolate'] else "No (Belongs to a family)", className="detail-value"),
        ]),

        html.Div([
            html.Div("Countries Spoken In", className="detail-label"),
            html.Div(lang['country_names_display'], className="detail-value", style={'fontSize': '0.9rem', 'lineHeight': '1.4'}),
        ]),

        html.Div([
            html.Div("Geographic Center", className="detail-label"),
            html.Div(f"Lat: {lang['latitude']:.4f}, Lon: {lang['longitude']:.4f}" if pd.notnull(lang['latitude']) else "No Coordinates", className="detail-value"),
        ]),
        
    ], className="py-2")

    # Set dropdown value to reflect selection (if not already set by dropdown itself)
    new_search_val = selected_lang_id if trigger_id != 'search-language' else dash.no_update

    return details_content, details_content, new_search_val

# ==============================================================================
# 6. DYNAMIC MAP CALLBACK
# ==============================================================================

@app.callback(
    Output("language-map", "figure"),
    [Input("map-filter-macroarea", "value"),
     Input("map-filter-isolate", "value"),
     Input("map-filter-status", "value"),
     Input("search-language", "value")]
)
def update_map(selected_macroareas, isolate_status, selected_statuses, selected_lang_id):
    # Filter dataset for mapping
    dff = df_map_source.copy()

    # Apply Macroarea filter
    if selected_macroareas:
        dff = dff[dff['macroarea'].isin(selected_macroareas)]

    # Apply Isolate filter
    if isolate_status == 'isolates':
        dff = dff[dff['is_isolate'] == True]
    elif isolate_status == 'non-isolates':
        dff = dff[dff['is_isolate'] == False]

    # Apply Status filter
    if selected_statuses:
        dff = dff[dff['status_label'].isin(selected_statuses)]
    else:
        # If none selected, return empty figure
        fig = go.Figure()
        fig.update_layout(
            template=plotly_template,
            mapbox_style="carto-darkmatter",
            mapbox_zoom=1,
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig

    # Map settings
    map_center = {"lat": 10, "lon": 10}
    map_zoom = 1.05

    # If a language is searched, zoom to it
    if selected_lang_id:
        zoom_row = df_map_source[df_map_source['id'] == selected_lang_id]
        if not zoom_row.empty:
            map_center = {"lat": zoom_row.iloc[0]['latitude'], "lon": zoom_row.iloc[0]['longitude']}
            map_zoom = 5.5

    # Create Scatter Mapbox figure with explicit center and zoom passed directly
    fig = px.scatter_mapbox(
        dff,
        lat="latitude",
        lon="longitude",
        color="status_label",
        color_discrete_map=status_colors,
        hover_name="name",
        custom_data=["id", "family", "status_label"],
        center=map_center,
        zoom=map_zoom
    )

    # Hover template styling
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Family: %{customdata[1]}<br>Status: %{customdata[2]}<br>ID: %{customdata[0]}<extra></extra>"
    )

    # If zoomed to a specific language, add a glowing highlight circle first
    if selected_lang_id:
        zoom_row = df_map_source[df_map_source['id'] == selected_lang_id]
        if not zoom_row.empty:
            lang = zoom_row.iloc[0]
            fig.add_trace(
                go.Scattermapbox(
                    lat=[lang['latitude']],
                    lon=[lang['longitude']],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color='white',
                        opacity=0.4
                    ),
                    hoverinfo='none',
                    showlegend=False
                )
            )

    # Apply layout changes AFTER adding all traces to prevent resetting of center/zoom
    fig.update_layout(
        template=plotly_template,
        mapbox_style="carto-darkmatter",
        mapbox_zoom=map_zoom,
        mapbox_center=map_center,
        uirevision=selected_lang_id or 'none',
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            title="Endangerment",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(11, 15, 25, 0.85)",
            bordercolor="rgba(255, 255, 255, 0.1)",
            borderwidth=1,
            font=dict(size=10)
        )
    )

    return fig

# ==============================================================================
# 7. ANALYTICS CHARTS CALLBACK
# ==============================================================================

@app.callback(
    [Output("chart-endangerment", "figure"),
     Output("chart-isolates", "figure"),
     Output("chart-families", "figure"),
     Output("chart-countries", "figure")],
    [Input("analytics-filter-macroarea", "value"),
     Input("families-slider", "value")]
)
def update_analytics_charts(selected_macroarea, num_families):
    # Filter dataset for analytics
    dff = df.copy()
    dff_exploded = df_exploded.copy()
    if selected_macroarea and selected_macroarea != 'All':
        dff = dff[dff['macroarea'] == selected_macroarea]
        dff_exploded = dff_exploded[dff_exploded['macroarea'] == selected_macroarea]

    # --- 1. Endangerment Status Distribution (Bar Chart) ---
    status_counts = dff['status_label'].value_counts().reindex(status_options).fillna(0).reset_index()
    status_counts.columns = ['Status', 'Count']
    
    fig_endangerment = px.bar(
        status_counts,
        x='Status',
        y='Count',
        color='Status',
        color_discrete_map=status_colors,
        text_auto='.2s'
    )
    fig_endangerment.update_layout(
        template=plotly_template,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Number of Languages",
        margin=dict(l=60, r=20, t=30, b=60),
        height=280
    )

    # --- 2. Isolate vs Family Ratio (Donut Chart) ---
    isolate_counts = dff['is_isolate'].value_counts().reset_index()
    isolate_counts.columns = ['Is Isolate', 'Count']
    isolate_counts['Label'] = isolate_counts['Is Isolate'].map({True: 'Language Isolates', False: 'Belongs to Family'})
    
    fig_isolates = px.pie(
        isolate_counts,
        values='Count',
        names='Label',
        color='Label',
        color_discrete_map={'Language Isolates': 'var(--accent-orange)', 'Belongs to Family': 'var(--accent-blue)'},
        hole=0.5
    )
    fig_isolates.update_traces(textinfo='percent+label', hovertemplate="%{label}: %{value} (%{percent})<extra></extra>")
    fig_isolates.update_layout(
        template=plotly_template,
        showlegend=False,
        margin=dict(l=20, r=20, t=10, b=10),
        height=280
    )

    # --- 3. Top Language Families (Horizontal Bar Chart) ---
    # Filter out isolate & unclassified for family size rankings
    family_counts = dff[~dff['family'].isin(['Isolate (No known relatives)', 'Unclassified'])]['family'].value_counts().reset_index()
    family_counts.columns = ['Family', 'Languages']
    family_counts = family_counts.head(num_families)
    
    fig_families = px.bar(
        family_counts,
        x='Languages',
        y='Family',
        orientation='h',
        text_auto=True
    )
    fig_families.update_traces(
        marker_color='var(--accent-purple)',
        hovertemplate="Family: %{y}<br>Languages: %{x}<extra></extra>"
    )
    fig_families.update_layout(
        template=plotly_template,
        xaxis_title="Language Count",
        yaxis_title="",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=180, r=30, t=30, b=50),
        height=330
    )

    # --- 4. Languages by Country (Bar Chart) ---
    country_counts = dff_exploded['country_name'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Languages']
    country_counts = country_counts.head(15)

    fig_countries = px.bar(
        country_counts,
        x='Country',
        y='Languages',
        text_auto=True
    )
    fig_countries.update_traces(
        marker_color='var(--accent-blue)',
        hovertemplate="Country: %{x}<br>Languages: %{y}<extra></extra>"
    )
    fig_countries.update_layout(
        template=plotly_template,
        xaxis_title="",
        yaxis_title="Languages Spoken",
        xaxis=dict(tickangle=45),
        margin=dict(l=60, r=20, t=30, b=110),
        height=330
    )

    return fig_endangerment, fig_isolates, fig_families, fig_countries

# ==============================================================================
# 8. EXPLORE DATATABLE CALLBACK
# ==============================================================================

@app.callback(
    [Output("languages-table", "data"),
     Output("languages-table", "selected_rows")],
    [Input("languages-table", "page_current"),
     Input("languages-table", "page_size"),
     Input("languages-table", "sort_by"),
     Input("table-search-input", "value"),
     Input("table-filter-macroarea", "value"),
     Input("table-filter-status", "value")]
)
def update_table(page_current, page_size, sort_by, search_val, macroarea_val, status_val):
    dff = df.copy()

    # Apply Search filter
    if search_val:
        dff = dff[dff['name'].str.contains(search_val, case=False, na=False) | 
                  dff['id'].str.contains(search_val, case=False, na=False)]

    # Apply Macroarea filter
    if macroarea_val and macroarea_val != 'All':
        dff = dff[dff['macroarea'] == macroarea_val]

    # Apply Status filter
    if status_val and status_val != 'All':
        dff = dff[dff['status_label'] == status_val]

    # Apply Sorting
    if len(sort_by):
        col_id = sort_by[0]['column_id']
        ascending = sort_by[0]['direction'] == 'asc'
        dff = dff.sort_values(by=col_id, ascending=ascending)

    # Paginate and return data
    page_data = dff.iloc[
        page_current * page_size : (page_current + 1) * page_size
    ].to_dict('records')

    # Reset selection when filters change (to avoid index out of bounds or old selection bugs)
    return page_data, []

# ==============================================================================
# 6. APP EXECUTION
# ==============================================================================

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
