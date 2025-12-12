import requests
import json
import pandas as pd
from datetime import date
import os

BLS_API_KEY = os.environ.get('BLS_API_KEY')

SERIES_IDS = [
    "LNS14000000",          # U-3 Unemployment Rate
    "LNS13327709",          # U-6 Underemployment Rate
    "CES0000000001",        # Total Nonfarm Payroll
    "CES0500000003",        # Avg Hourly Earnings (All Private)
    "CUUR0000SA0",          # CPI (All Items) - For Real Wage Calc
    "JTS000000000000000JOL",# Job Openings
    "JTS000000000000000QUL",# Quits
    "JTS000000000000000LDL" # Layoffs
]

SERIES_NAMES = {
    "LNS14000000": "Unemployment Rate (U3)",
    "LNS13327709": "Underemployment Rate (U6)",
    "CES0000000001": "Total Nonfarm Employment",
    "CES0500000003": "Avg Hourly Earnings",
    "CUUR0000SA0": "CPI",
    "JTS000000000000000JOL": "Job Openings",
    "JTS000000000000000QUL": "Quits",
    "JTS000000000000000LDL": "Layoffs"
}

def fetch_data():
    headers = {'Content-type': 'application/json'}
    data = json.dumps({
        "seriesid": SERIES_IDS,
        "startyear": "2020", 
        "endyear": str(date.today().year),
        "registrationkey": BLS_API_KEY
    })

    print("Requesting data from BLS API")
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    json_data = json.loads(p.text)

    if json_data['status'] != 'REQUEST_SUCCEEDED':
        print("API Error:", json_data['message'])
        return None
    
    # Make a list from the JSON
    records = []
    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        col_name = SERIES_NAMES.get(series_id, series_id)

        for item in series['data']:
            year = item['year']
            period = item['period']
            month = int(period.replace("M", ""))
            date_str = f"{year}-{month:02d}-01"
            records.append({
                "date": date_str,
                "variable": col_name,
                "value": float(item['value'])
            })
    df = pd.DataFrame(records)
    # Make variables columns
    df_pivot = df.pivot(index='date', columns='variable', values='value').reset_index()
    # Make dates datetime
    df_pivot['date'] = pd.to_datetime(df_pivot['date'])
    df_pivot = df_pivot.sort_values('date')

    return df_pivot

def process_data(df):
    # Real wages: nominal wage / CPI * 100
    if 'Avg Hourly Earnings' in df.columns and 'CPI' in df.columns:
        df['Real Wages'] = (df['Avg Hourly Earnings'] / df['CPI']) * 100
        print("Calculated Real Wages")
    return df

if __name__ == "__main__":
    df = fetch_data()
    if df is not None:
        df = process_data(df)
        # Save data
        filename = 'labor_market_data.csv'
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(df.tail())
