from datetime import datetime, timedelta
import influxdb_client
import pandas as pd
from influxdb_client.client.write_api import SYNCHRONOUS
from flask import Flask, render_template, request, jsonify
import psycopg2
import json
import requests
from bs4 import BeautifulSoup

# Skin IMG
def get_steam_market_image(skin_name):
    # Zamień spację w nazwie skórki na '%20' i przygotuj URL
    encoded_skin_name = skin_name.replace(' ', '%20')
    encoded_skin_name = skin_name.replace('|', '%7C')
    market_url = f'https://steamcommunity.com/market/listings/730/{encoded_skin_name}'

    # Wyślij żądanie do strony Steam Market
    response = requests.get(market_url)
    if response.status_code == 200:
        # Parsuj HTML przy użyciu BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Znajdź div z klasą "market_listing_largeimage" i pobierz link do zdjęcia
        image_div = soup.find('div', {'class': 'market_listing_largeimage'})
        if image_div:
            image_url = image_div.find('img')['src']
            return image_url

    return None


# Konfiguracja InfluxDB
influxdb_host = "127.0.0.1:8086"
bucket = "admin"
#org = "086f756ff907fbd5"
#token = "4khVY-qf0z-Bt3iGxam3IvXvExtahAwFRaflw_3hP1QNU38lFjpg-0ZQHlmb3FEU57wGQrZEu4Mvea-UFuXS8Q=="
org = "c9d2f82bec384031"
token = "YY7AtGmBB5uAAcgdEP5G0u34dqbbmEYmr7-ZgOEG4spK_6l9XMThk7HQckSQVWwD7mGxKSLzcTqHXU8bGU5pow=="

app = Flask(__name__)

def connect_db():
    try:
        connection = psycopg2.connect(
            host="127.0.0.1",
            user="postgres",
            password="admin",
            database="postgres",
            port="5432"
        )
        return connection
    except psycopg2.Error as e:
        # Print or log the error message
        print(f"Error connecting to the database: {e}")
        # Optionally, raise the exception to propagate it further
        raise


@app.route('/get_suggestions', methods=['GET'])
def get_suggestions():
    query = request.args.get('query', '')
    suggestions = fetch_suggestions_from_db(query)
    return jsonify(suggestions)

def fetch_suggestions_from_db(query):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT typ_skina, "nazwa_skorki", "stan_zuzycia"
        FROM public.typ_przedmiotu
        WHERE typ_skina ILIKE %s
           OR "nazwa_skorki" ILIKE %s
           OR "stan_zuzycia" ILIKE %s
        LIMIT 10;
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))

    suggestions = cursor.fetchall()
    
    conn.close()

    return suggestions




@app.route('/<skinName>')
def skin(skinName):
    if skinName == "favicon.ico":
        return "/favicon.ico"
    print(skinName)
    texts = skinName.split("|")
    print(texts)
    weaponType = texts[0].strip()
    print(weaponType)
    print(len(texts))
    print(texts)
    skinName = texts[1].strip()

    getchart = get_data(weaponType, skinName)
    getdatafrompostgres = skin_data_from_postgres(weaponType,skinName)

    context = {'getchart': getchart, 'getskindata': getdatafrompostgres}
    return render_template('skin.html', **context)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['GET'])
def get_data(weaponType,skinName):

    client = influxdb_client.InfluxDBClient(
        url=influxdb_host,
        token=token,
        org=org
    )
    
    datax = []
    datay = []
    
    for x in range(30, 0, -1):
        if x == 1:
            query = f'''
            from(bucket: "admin")
            |> range(start: -{x}d, stop: now())
            |> filter(fn: (r) => r["_measurement"] == "{weaponType}")
            |> filter(fn: (r) => r["Normal"] == "{skinName}")
            |> filter(fn: (r) => r["_field"] == "Cena")
         '''
        else:
            query = f'''
            from(bucket: "admin")
            |> range(start: -{x}d, stop: -{x-1}d)
            |> filter(fn: (r) => r["_measurement"] == "{weaponType}")
            |> filter(fn: (r) => r["Normal"] == "{skinName}")
            |> filter(fn: (r) => r["_field"] == "Cena")
         '''
        
        query_api = client.query_api()
        result = query_api.query(query, org=org)

        for table in result:
            for record in table.records:
                value = record.get_value()
                time = record.get_time()
                datax.append(time)
                datay.append(value)

    
    df = pd.DataFrame({'time': datax, 'value': datay})
    #return jsonify(df.to_dict()) # zwróć dane jako JSON
    # Konwertowanie ramki danych do formatu JSON
    json_data = df.to_json(orient='records')

    # Wyświetlenie wyniku
    json_data = json.loads(json_data)
    new_json_data = json.dumps([[entry["time"], entry["value"]] for entry in json_data], indent=4)
    return(new_json_data)

def skin_data_from_postgres(weaponType, skinName):
    czesci_stanu = skinName.split("(")

    # Usuń dodatkowe białe znaki
    czesci_stanu = [czesc.strip(" )") for czesc in czesci_stanu]

    # Zastąp ")" pustym ciągiem w drugiej części
    czesci_stanu[1] = czesci_stanu[1].replace(")", "")

    # Wynik
    skinName = czesci_stanu[0]
    stan = czesci_stanu[1]


    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM public.typ_przedmiotu
        WHERE "typ_skina" = %s
           AND "nazwa_skorki" = %s
           AND "stan_zuzycia" = %s
        LIMIT 10;
    """, (f'{weaponType}', f'{skinName}', f'{stan}'))

    data = cursor.fetchall()
    
    conn.close()
    print(data)
    return data

if __name__ == '__main__':
    #db.create_all()
    #app.run(debug=True)
    pass

app.run()