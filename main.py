# -*- coding: utf-8 -*-
"""
HF timeseries processing script
Originally from: https://colab.research.google.com/drive/1C9o5nYQuFESdc5v2fjUAzHB399ZI4QZV
"""

import os
import time
import dataclasses
import pandas as pd
import gspread
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuration & Data Structures
# -----------------------------------------------------------------------------

@dataclasses.dataclass
class Params:
    ticker: str
    sheet_id: str

params = [
    Params(ticker='hfgm', sheet_id='1qSxF2O1K7ZznYiYPmco0-2bjly6BOfchF122oUMSC1w'),
    Params(ticker='hfeq', sheet_id='11cnEliJDlETvYHXE2UKCo4CbzGbZPT8jjGGxF53H3e0'),
]

# Update this path to where your credentials and project files are located
base_dir = '.' 

credential_file = os.path.join(base_dir, 'positionsdownloader-b257900bcaa5.json')

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------

try:
    gc = gspread.service_account(filename=credential_file)
except Exception as e:
    print(f"Warning: Could not authenticate with gspread using {credential_file}. Error: {e}")
    gc = None

# -----------------------------------------------------------------------------
# Function Definitions
# -----------------------------------------------------------------------------

def build_figs_for_params(params: Params, gc_client):
    if not gc_client:
        raise ValueError("gspread client is not authenticated.")
        
    spreadsheet = gc_client.open_by_key(params.sheet_id)

    # Iterate through all worksheets
    all_df = []
    for worksheet in spreadsheet.worksheets():
        # Convert to DataFrame
        print(f"Processing worksheet: {worksheet.title}")
        df = pd.DataFrame(worksheet.get_all_records())
        df['date'] = worksheet.title
        time.sleep(0.5)

        all_df.append(df)
    
    total = pd.concat(all_df)
    total['date'] = pd.to_datetime(total['date'])

    # Create a pivot table with 'date' as index, 'SecurityName' as columns, and 'MarketValue' as values
    pivot_df = total.pivot_table(index='date', columns='SecurityName', values='MarketValue', aggfunc='sum').fillna(0)

    # Calculate the sum of MarketValue for each SecurityName to sort the columns
    sorted_columns = pivot_df.abs().sum().sort_values(ascending=True).index

    # Reindex the pivot_df columns based on the sorted order and reset index for plotly
    pivot_df_sorted = pivot_df[sorted_columns].drop_duplicates(keep='first').reset_index()

    # Melt the DataFrame to long format for plotly express
    df_melted = pivot_df_sorted.melt(id_vars='date', var_name='SecurityName', value_name='MarketValue')
    df_melted['NormalizedMarketValue'] = df_melted.groupby('date')['MarketValue'].transform(lambda x: (x / x.abs().sum()) * 100)

    # Plot the interactive stacked bar chart using plotly.express
    fig = px.bar(df_melted,
                x='date',
                y='NormalizedMarketValue',
                color='SecurityName',
                title=f'({params.ticker.upper()}) Market Value Stacked by SecurityName per Date (Ordered by Total Market Value, Negative for shorts)',
                labels={'date': 'Date',
                        'NormalizedMarketValue': 'Normalized Market Value (%)',
                        'SecurityName': 'Security Name'},
                hover_data={'date': '|%Y-%m-%d', 'NormalizedMarketValue': ':, .2f', 'SecurityName': True},
                height=600)

    fig.update_layout(xaxis_tickangle=-45)
    fig.update_layout(barmode='relative') # Explicitly set stacked bar chart property
    return fig

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

def main():
    if not gc:
        print("Skipping figure generation due to missing Google authentication.")
        return

    # Generate Figures
    print("Generating Figure 1...")
    fig1 = build_figs_for_params(params[0], gc)
    
    print("Generating Figure 2...")
    fig2 = build_figs_for_params(params[1], gc)

    # Create the website directory if it doesn't already exist
    website_dir = os.path.join(base_dir, 'website')
    os.makedirs(website_dir, exist_ok=True)

    # Export figures to HTML strings (divs only, to embed in our own layout)
    # include_plotlyjs='cdn' creates a smaller file that loads plotly from CDN
    # If offline is needed, use include_plotlyjs=True (larger file)
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False) # Plotly JS already included by fig1

    # Simple HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Market Value Analysis</title>
        <style>
            body {{ font-family: sans-serif; margin: 2rem; }}
            .chart-container {{ margin-bottom: 2rem; border: 1px solid #ddd; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #333; }}
        </style>
    </head>
    <body>
        <h1>Market Value Analysis</h1>
        
        <div class="chart-container">
            {fig1_html}
        </div>
        
        <div class="chart-container">
            {fig2_html}
        </div>
    </body>
    </html>
    """

    # Write the HTML content to index.html in the website directory
    index_path = os.path.join(website_dir, 'index.html')
    with open(index_path, 'w') as f:
        f.write(html_content)

    print(f"Static 'index.html' has been created in {website_dir}")

if __name__ == "__main__":
    main()
