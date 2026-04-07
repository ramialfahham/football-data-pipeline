import functions_framework
import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
import io
import re

GCP_PROJECT_ID = "football-data-pipeline-gcp"
DATASET_ID = "FOOTBALL_DATA"
LEAGUES = ['D1', 'E0', 'I1', 'SP1', 'F1']
URLS = ["https://www.football-data.co.uk/germanym.php", "https://www.football-data.co.uk/englandm.php"]

def make_unique_columns(columns):
    seen = {}
    new_cols = []
    for col in columns:
        # Säubern: Nur Buchstaben, Zahlen und Unterstriche
        clean = re.sub(r'[^a-zA-Z0-9]', '_', col)
        if not clean or not clean[0].isalpha(): clean = 'f_' + clean
        
        # Duplikate verhindern
        final_name = clean
        if final_name in seen:
            seen[final_name] += 1
            final_name = f"{final_name}_{seen[final_name]}"
        else:
            seen[final_name] = 0
        new_cols.append(final_name)
    return new_cols

@functions_framework.http
def load_football_data(request):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    all_links = []
    for page in URLS:
        res = requests.get(page, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.csv') and any(f"/{l}.csv" in href for l in LEAGUES):
                all_links.append(f"https://www.football-data.co.uk/{href}")

    success_count = 0
    for url in all_links:
        try:
            file_res = requests.get(url, headers=headers)
            if file_res.status_code == 200:
                lines = file_res.content.decode('latin-1').splitlines()
                if not lines: continue
                
                # Header auslesen und eindeutig machen
                raw_header = lines[0].split(',')
                clean_header = make_unique_columns(raw_header)
                lines[0] = ",".join(clean_header)
                
                parts = url.split('/')
                table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.RAW_{parts[-1].replace('.csv','')}_{parts[-2]}"
                
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.CSV,
                    skip_leading_rows=1,
                    autodetect=True,
                    write_disposition="WRITE_TRUNCATE"
                )
                
                final_csv = "\n".join(lines)
                job = client.load_table_from_file(io.BytesIO(final_csv.encode('utf-8')), table_id, job_config=job_config)
                job.result()
                success_count += 1
        except Exception as e:
            print(f"Fehler bei {url}: {e}")
            continue

    return f"Erfolg: {success_count} Tabellen geladen.", 200
