from datetime import datetime, timedelta
import logging
import influxdb_client
import pandas as pd
from influxdb_client.client.write_api import SYNCHRONOUS
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Blueprint
import psycopg2
import json
import requests
from bs4 import BeautifulSoup
from flask import send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from flask_mail import Mail, Message
from urllib.parse import quote
import random 
from urllib.parse import quote


logging.basicConfig(level=logging.DEBUG)


# Skin IMG
def get_steam_market_image(skin_name):
    # Zamień spację w nazwie skórki na '%20' i przygotuj URL
    encoded_skin_name = skin_name.replace(' ', '%20')
    encoded_skin_name = encoded_skin_name.replace('|', '%7C')
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
    logging.debug(f"Error path to img {skin_name}")
    return None


# Konfiguracja InfluxDB
influxdb_host = "127.0.0.1:8086"
bucket = "Test"
org = "Steam"
token = "h3Pp4GlwPPbuJDVXkyaqEweBJE7TzvR3WJAJHd3Ft_zOiYmPZKs3h6GYG4EJvgpiXYQZRkH867mp5p63U_6nLg=="
#org = "c9d2f82bec384031"
#token = "YY7AtGmBB5uAAcgdEP5G0u34dqbbmEYmr7-ZgOEG4spK_6l9XMThk7HQckSQVWwD7mGxKSLzcTqHXU8bGU5pow=="

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'skindbmailer@gmail.com'
app.config['MAIL_PASSWORD'] = 'jpye ddvm zlgn jwtk'
mail = Mail(app) 

def connect_db():
    try:
        connection = psycopg2.connect(
            host="127.0.0.1",
            user="postgres",
            password="rootpass",
            database="postgres",
            port="5432"
        )
        return connection
    except psycopg2.Error as e:
        # Print or log the error message
        print(f"Error connecting to the database: {e}")
        # Optionally, raise the exception to propagate it further
        raise


def generate_random_code():
    return str(random.randint(100000, 999999))

send_email_bp = Blueprint('send_email_bp', __name__)

@send_email_bp.route('/send_confirmation_email_from_profile', methods=['GET'])
def send_confirmation_email_from_profile():
    try:
        # Dodaj kod do przekazania informacji o sesji i wywołania funkcji send_confirmation_email
        if 'user' in session:
            user_id = session['user']['id']
            auth_code = generate_random_code()

            # Przekazanie informacji o sesji do funkcji send_confirmation_email
            send_confirmation_email(session, auth_code)

            return redirect(url_for('profile'))
        else:
            return jsonify({'status': 'error', 'message': 'Użytkownik nie jest zalogowany'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Błąd: {str(e)}'})

# Dodaj Blueprint do aplikacji
app.register_blueprint(send_email_bp)
def send_confirmation_email(session, auth_code):
    try:
        if 'user' in session:
            user_id = session['user']['id']
            username = session['user']['username']

            # Pobierz adres e-mail użytkownika z bazy danych
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM uzytkownik WHERE iduzytkownika = %s;", (user_id,))
            user_email = cursor.fetchone()[0]
            conn.close()

            # Aktualizuj kod autoryzacyjny użytkownika w bazie danych
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE uzytkownik SET kodweryfikacyjny = %s WHERE iduzytkownika = %s;", (auth_code, user_id))
            conn.commit()
            conn.close()

            # Wyślij wiadomość e-mail
            msg = Message('Potwierdzenie rejestracji', sender='skindbmailer@gmail.com', recipients=[user_email])
            msg.body = f'Twój kod to: {auth_code}'
            mail.send(msg)
            print('Wiadomość została wysłana')

            # Dodanie informacji o sesji
            session['confirmation_email_sent'] = True

        else:
            print('Brak zalogowanego użytkownika')

    except Exception as e:
        print(f'Błąd podczas wysyłania e-maila: {str(e)}')

# Wywołanie funkcji send_confirmation_email
@app.route('/send_confirmation_email')
def send_confirmation_email_route():
    try:
        if 'user' in session:
            user_id = session['user']['id']
            auth_code = generate_random_code()

            # Przekazanie informacji o sesji do funkcji send_confirmation_email
            send_confirmation_email(session, auth_code)

            return redirect(url_for('profile'))
        else:
            return 'Użytkownik nie jest zalogowany'
    except Exception as e:
        return f'Błąd: {str(e)}'

@app.route('/confirm_registration', methods=['POST'])
def confirm_registration():
    try:
        if 'user' in session:
            user_id = session['user']['id']
            confirmation_code = request.form.get('confirmation_code')

            # Sprawdź, czy kod potwierdzenia jest poprawny
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT kodweryfikacyjny FROM uzytkownik WHERE iduzytkownika = %s;", (user_id,))
            stored_confirmation_code = cursor.fetchone()[0]

            conn.close()

            if str(confirmation_code).strip() == str(stored_confirmation_code).strip():
                # Zaktualizuj kolumnę 'zweryfikowany' w bazie danych
                print(stored_confirmation_code)
                print(confirmation_code)
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE uzytkownik SET zweryfikowany = TRUE WHERE iduzytkownika = %s;", (user_id,))
                conn.commit()
                conn.close()

                flash("Rejestracja została pomyślnie potwierdzona!", 'success')
                return redirect(url_for('profile'))
            else:
                flash("Nieprawidłowy kod potwierdzenia.", 'error')
                return redirect(url_for('profile')) \

        else:
            return redirect(url_for('login'))
    except Exception as e:
        flash(f"Błąd podczas potwierdzania rejestracji: {str(e)}", 'error')
        return redirect(url_for('profile'))


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

    texts = skinName.split("|")

    weaponType = texts[0].strip()

    skinName = ''.join(texts[1:]).strip()

    getchart = get_data(weaponType, skinName)
    getdatafrompostgres = skin_data_from_postgres(weaponType,skinName)

    context = {'getchart': getchart, 'getskindata': getdatafrompostgres}
    return render_template('skin.html', **context)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the user exists in the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT iduzytkownika, nazwa, haslo FROM uzytkownik WHERE nazwa = %s;", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            # Set session after logging in
            session['user'] = {'id': user[0], 'username': user[1]}
            return redirect(url_for('index'))
        else:
            flash("Błędna nazwa użytkownika lub hasło.", 'error')  # Dodaj ten flash message
            #return "Błędna nazwa użytkownika lub hasło."

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        nazwa = request.form.get('username')
        email = request.form.get('email')
        steamid = request.form.get('steamid')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Check if passwords match
        if password != password_confirm:
            flash("Hasła się nie zgadzają!", 'error')
            return redirect(url_for('register_user'))

        # Check if password length is at least 8 characters
        if len(password) < 8:
            flash("Hasło musi mieć conajmniej 8 znaków!", 'error')
            return redirect(url_for('register_user'))

        # Check if SteamID has exactly 17 characters
        if len(steamid) != 17:
            flash("SteamID musi mieć dokładnie 17 znaków!", 'error')
            return redirect(url_for('register_user'))

        # Check if username or email already exist
        conn = connect_db()
        cursor = conn.cursor()

        try:
            if user_exists(nazwa, email, cursor):
                flash("Użytkownik o podanej nazwie lub emailu już istnieje!", 'error')
                return redirect(url_for('register_user'))

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert data into the database
            cursor.execute("""
                INSERT INTO uzytkownik (nazwa, email, haslo, steamid, zweryfikowany)
                VALUES (%s, %s, %s, %s, %s);
            """, (nazwa, email, hashed_password, steamid, False))

            conn.commit()
            return redirect(url_for('login'))

        except Exception as e:
            conn.rollback()
            flash(f"Błąd podczas rejestracji: {e}", 'error')
            return redirect(url_for('register_user'))

        finally:
            conn.close()

    return render_template('register.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_image_url/<path:skin_name>', methods=['GET'])
def get_image_url(skin_name):
    image_url2 = str(get_steam_market_image(skin_name))
    if image_url2:
        logging.debug(image_url2)
        return image_url2
    else:
        return 'png/error.png' # Zmień na ścieżkę do domyślnego zdjęcia    


@app.route('/profile', methods=['GET'])
def profile():
    if 'user' in session:
        user_id = session['user']['id']
        username = session['user']['username']

        # Pobierz dodatkowe informacje o użytkowniku z bazy danych
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT iduzytkownika, nazwa, email, zweryfikowany FROM uzytkownik WHERE iduzytkownika = %s;", (user_id,))
        user_info = cursor.fetchone()
        conn.close()

        if user_info:
            return render_template('profile.html', user_info=user_info)
        else:
            flash("Błąd pobierania informacji o użytkowniku", 'error')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Wylogowanie
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/query_influxdb', methods=['GET'])
def query_influxdb():
    # Utwórz zapytanie Flux
    flux_query = '''
    from(bucket: "Test")
      |> range(start: 0, stop: now())
      |> last()
      |> filter(fn: (r) => r["Normal"] != "")
      |> sort(columns:["_value"], desc: true)
      |> limit(n:10)
    '''

    client = influxdb_client.InfluxDBClient(
        url=influxdb_host,
        token=token,
        org=org
    )

    # Wykonaj zapytanie
    query_api = client.query_api()
    result = query_api.query(org=org, query=flux_query)

    # Przetwórz wyniki do formatu JSON
    data = []
    for table in result:
        for record in table.records:
            data.append(record.values)

    sorted_data = sorted(data, key=lambda x: x.get('_value', 0), reverse=True)[:10]

    return jsonify(sorted_data)


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
            from(bucket: "Test")
            |> range(start: -{x}d, stop: now())
            |> filter(fn: (r) => r["_measurement"] == "{weaponType}")
            |> filter(fn: (r) => r["Normal"] == "{skinName}")
            |> filter(fn: (r) => r["_field"] == "Cena")
         '''
        else:
            query = f'''
            from(bucket: "Test")
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
        LIMIT 1;
    """, (f'{weaponType}', f'{skinName}', f'{stan}'))

    data = cursor.fetchall()
    
    conn.close()
    print(data)
    return data

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' in session:
        user_id = session['user']['id']
        username = session['user']['username']

        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            # Sprawdź, czy obecne hasło jest poprawne
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT haslo FROM uzytkownik WHERE iduzytkownika = %s;", (user_id,))
            stored_password = cursor.fetchone()[0]
            conn.close()

            if not check_password_hash(stored_password, current_password):
                flash("Obecne hasło jest nieprawidłowe.", 'error')
                return redirect(url_for('change_password'))

            if len(new_password) < 8:
                flash("Hasło musi mieć conajmniej 8 znaków!", 'error')
                return redirect(url_for('change_password'))

            # Sprawdź, czy nowe hasła się zgadzają
            if new_password != confirm_new_password:
                flash("Nowe hasła się nie zgadzają.", 'error')
                return redirect(url_for('change_password'))

            # Zaktualizuj hasło w bazie danych
            hashed_new_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE uzytkownik SET haslo = %s WHERE iduzytkownika = %s;", (hashed_new_password, user_id))
            conn.commit()
            conn.close()

            flash("Hasło zostało pomyślnie zmienione.", 'success')
            return render_template('change_password.html')

        return render_template('change_password.html', username=username)
    else:
        return redirect(url_for('login'))
def user_exists(username, email, cursor):
    # Check if username or email already exist in the database
    cursor.execute("""
        SELECT COUNT(*)
        FROM uzytkownik
        WHERE nazwa = %s OR email = %s;
    """, (username, email))

    return cursor.fetchone()[0] > 0

if __name__ == '__main__':
    #db.create_all()
    #app.run(debug=True)
    pass

app.run()