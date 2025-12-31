import os
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession
from typing import List
from fastapi.responses import RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURATION BASE DE DONNÉES ---
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # Connexion pour Railway (Cloud)
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # Connexion pour ton ThinkPad (Local)
        return psycopg2.connect(
            dbname="copytrader_db",
            user="imdade_user",
            password="ton_mot_de_pass_ici", 
            host="localhost",
            port="5432"
        )

API_ID = 30882701
API_HASH = 'ce3413ef77f883d43cc2629addb54790'

# TON JETON METAAPI VÉRIFIÉ
META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI3OWRhNjFhMGVmZTg1OThkZDBlMzhmNDFiMTFjNDJjOSIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiNzlkYTYxYTBlZmU4NTk4ZGQwZTM4ZjQxYjExYzQyYzkiLCJpYXQiOjE3NjY2NzUyNjh9.NMWCHVMrBR5uE4wZ8iVdNBkB-zG4qaEydhAcm1IoOdYNym9a33e7xoxmOY9A6ToorwOG2h_AUpN8QfZw46zD7zbEqNQOaiwyFpJhCswmJ76Rt4ITZgIcvdFwiF2eFNkmWwv4agnrwp-QBdzTHgX6EYWtwNDRP19UHGJCbtKLcoDzLdv3MArGRNJqj_llvJkgYCOAg3i9HNg5mN3cJbNEXhQuhjufDiLwHig8bFftSltHmUEQxR22_ks3xjg1aR5FvrejtKtH4Yde5GzvOZwMh1g6NbENtI1H5dgQhO0R19uVLO2wktGMO3VnRwYf74Ct91lBzh9IMUOzTELtO38U3PAmNOHql49yGaapY0oS2p52Bc-z7gIPiqSxynhubggCWJxVbe4mSCrktp34xnnJU2LVoNj9gnOqLn9D3q8x34EkCjnfibnwFU8S4QTXiJadrLR0H3V-7Rt4opFsNWQ8Ywn-X_TP566RtTywcTgHnwc23KP0MGPaBmeG0ytgF8D8IM_qcdqtb5yL50ZtP0qCdpLWKUByurb2Kpa3WMJw_AJ_mTTjnBmaRGy8CLuivtRlp-DkrAg8uDJ7stzoG-CFbWRWSFAzJJxI2wuAjSpKqaqXfii96vK63Y77K2wt1m-c7CiwEs6eJFqOIyIfz4h1lC48DU-fo3pKANsiL4ItIJk"

clients_en_attente = {}

# --- LOGIQUE CLOUD METAAPI ---
async def inscrire_client_metaapi(user_id, login, password, server):
    url = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai/users/current/accounts"
    headers = {"auth-token": META_API_TOKEN, "Content-Type": "application/json"}
    data = {
        "name": f"Client_{user_id}",
        "type": "cloud",
        "login": login,
        "password": password,
        "server": server,
        "platform": "mt5",
        "application": "MetaApi",
        "magic": 1000
    }
    async with httpx.AsyncClient(timeout=30.0)as client:
        response = await client.post(url, json=data, headers=headers)
        print(f"🔍 DEBUG METAAPI: Status {response.status_code} - Body: {response.text}") # Affiche l'erreur exacte
        if response.status_code in [200, 201]:
            return response.json()['id']
        return None

# --- FONCTION UTILITAIRE : CHARGER LE DASHBOARD ---
def render_user_dashboard(request, user_id, error_msg: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM sessions_telegram WHERE user_id = %s", (user_id,))
    telegram_lie = cur.fetchone() is not None

    cur.execute("SELECT id FROM comptes_mt5 WHERE user_id = %s", (user_id,))
    mt5_lie = cur.fetchone() is not None
    
    cur.execute("SELECT lot_fixe, max_trades_jour, bot_actif FROM reglages_trading WHERE user_id = %s", (user_id,))
    reglages = cur.fetchone()
    lot_actuel = reglages[0] if reglages else 0.01
    max_actuel = reglages[1] if reglages else 5
    bot_actif = reglages[2] if reglages else False

    cur.execute("""
        SELECT symbole, type_ordre, lot, profit, TO_CHAR(date_trade, 'YYYY-MM-DD HH24:MI') 
        FROM bilan_trades WHERE user_id = %s ORDER BY date_trade DESC
    """, (user_id,))
    trades = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user_id": user_id, "telegram_lie": telegram_lie,
        "mt5_lie": mt5_lie, "lot_actuel": lot_actuel, "max_actuel": max_actuel,
        "bot_est_actif": bot_actif, "trades": trades, "error_msg": error_msg
    })

# --- ROUTES D'AUTHENTIFICATION ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Redirige l'accueil vers l'inscription"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    """Affiche la page d'inscription"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    """Affiche la page de connexion"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register")
async def register(request: Request):
    """Crée l'utilisateur et ses réglages par défaut"""
    try:
        data = await request.form()
        email = data.get("email")
        password = data.get("password")

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Insertion Email/MDP uniquement
                cur.execute(
                    "INSERT INTO utilisateurs (email, mot_de_passe) VALUES (%s, %s) RETURNING id",
                    (email, password)
                )
                new_user_id = cur.fetchone()[0]
                
                # Création des réglages (essentiel pour le bot)
                cur.execute(
                    "INSERT INTO reglages_trading (user_id, lot_fixe, bot_actif) VALUES (%s, 0.01, FALSE)",
                    (new_user_id,)
                )
                conn.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        print(f"❌ Erreur Inscription: {e}")
        return templates.TemplateResponse("register.html", {"request": request, "error_msg": "Email déjà utilisé."})
@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM utilisateurs WHERE email = %s AND mot_de_passe = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return render_user_dashboard(request, user[0])
    return "Identifiants incorrects."


@app.post("/save-mt5")
async def save_mt5(request: Request, user_id: int = Form(...), mt5_login: str = Form(...), mt5_password: str = Form(...), mt5_server: str = Form(...)):
    # 1. Création sur MetaApi
    meta_account_id = await inscrire_client_metaapi(user_id, mt5_login, mt5_password, mt5_server)
    
    if not meta_account_id:
        return render_user_dashboard(request, user_id, "Erreur lors de la liaison Cloud MetaApi.")

    # 2. Sauvegarde PostgreSQL avec Commit
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO comptes_mt5 (user_id, mt5_login, mt5_password, mt5_server, metaapi_account_id) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (user_id) DO UPDATE SET 
                mt5_login = EXCLUDED.mt5_login, 
                mt5_password = EXCLUDED.mt5_password, 
                mt5_server = EXCLUDED.mt5_server, 
                metaapi_account_id = EXCLUDED.metaapi_account_id
        """, (user_id, mt5_login, mt5_password, mt5_server, meta_account_id))
        
        conn.commit() # Crucial pour enregistrer les données
        cur.close()
        conn.close()
        print(f"💾 SUCCESS: Compte {mt5_login} enregistré pour l'user {user_id}")
        return render_user_dashboard(request, user_id)
    except Exception as e:
        print(f"💥 ERREUR BDD lors de save-mt5: {e}")
        return render_user_dashboard(request, user_id, f"Erreur BDD : {e}")

# --- ROUTES TELEGRAM (RÉAJOUTÉES) ---

@app.post("/connect-telegram")
async def connect_telegram(request: Request, phone: str = Form(None), user_id: int = Form(...)):
    if not phone or len(phone.strip()) < 5:
        return render_user_dashboard(request, user_id, "Numéro obligatoire.")
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        sent_code = await client.send_code_request(phone)
        clients_en_attente[phone] = {"client": client, "phone_code_hash": sent_code.phone_code_hash}
        return templates.TemplateResponse("verify.html", {"request": request, "phone": phone, "user_id": user_id})
    except Exception as e:
        return render_user_dashboard(request, user_id, f"Erreur Telegram : {e}")

@app.post("/verify-telegram")
async def verify_telegram(request: Request, phone: str = Form(...), code: str = Form(...), user_id: int = Form(...)):
    if phone not in clients_en_attente: 
        print("❌ Erreur : Téléphone non trouvé dans la file d'attente")
        return render_user_dashboard(request, user_id, "Session expirée.")
    
    data = clients_en_attente[phone]
    client = data["client"]
    try:
        print(f"⏳ Tentative de connexion pour {phone}...")
        await client.sign_in(phone, code, phone_code_hash=data["phone_code_hash"])
        
        session_str = client.session.save()
        print("✅ Session Telegram validée et sauvegardée.")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sessions_telegram (user_id, phone, string_session) 
            VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET string_session = EXCLUDED.string_session
        """, (user_id, phone, session_str))
        conn.commit()
        
        print("🔍 Récupération des canaux (cela peut être long)...")
        dialogs = await client.get_dialogs()
        
        channels_data = [{"id": d.id, "name": d.name, "last_msg": ""} for d in dialogs if d.is_channel or d.is_group]
        print(f"🎉 {len(channels_data)} canaux trouvés. Envoi vers select_channel.html")

        await client.disconnect()
        del clients_en_attente[phone]
        
        return templates.TemplateResponse("select_channel.html", {"request": request, "user_id": user_id, "channels": channels_data})
    
    except Exception as e: 
        print(f"💥 ERREUR CRITIQUE : {e}")
        return render_user_dashboard(request, user_id, f"Erreur : {e}")
# --- RÉGLAGES ET SOURCES ---

@app.post("/save-settings")
async def save_settings(request: Request, user_id: int = Form(...), lot: float = Form(...), max_trades: int = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reglages_trading (user_id, lot_fixe, max_trades_jour) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (user_id) DO UPDATE SET lot_fixe = EXCLUDED.lot_fixe, max_trades_jour = EXCLUDED.max_trades_jour
        """, (user_id, lot, max_trades))
        conn.commit()
        cur.close()
        conn.close()
        return render_user_dashboard(request, user_id)
    except Exception as e:
        return render_user_dashboard(request, user_id, f"Erreur technique : {e}")

@app.post("/toggle-bot")
async def toggle_bot(request: Request, user_id: int = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT bot_actif FROM reglages_trading WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    nouvel_etat = not res[0] if res else True
    cur.execute("""
        INSERT INTO reglages_trading (user_id, bot_actif) 
        VALUES (%s, %s) 
        ON CONFLICT (user_id) DO UPDATE SET bot_actif = EXCLUDED.bot_actif
    """, (user_id, nouvel_etat))
    conn.commit()
    cur.close(); conn.close()
    return render_user_dashboard(request, user_id)

@app.post("/save-sources")
async def save_sources(request: Request, user_id: int = Form(...)):
    try:
        data = await request.form()
        # Récupère tous les éléments cochés nommés "selected_channels"
        channels = data.getlist("selected_channels")
        
        if not channels:
            return render_user_dashboard(request, user_id, "Aucun canal sélectionné.")

        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. On vide les anciennes sources pour éviter les conflits
        cur.execute("DELETE FROM sources WHERE user_id = %s", (user_id,))
        
        # 2. On insère les nouvelles sources
        for entry in channels:
            if '|' in entry:
                canal_id, canal_name = entry.split('|', 1)
                cur.execute(
                    "INSERT INTO sources (user_id, canal_id, nom_canal) VALUES (%s, %s, %s)",
                    (user_id, canal_id, canal_name)
                )
        
        conn.commit()
        cur.close(); conn.close()
        print(f"✅ Sources mises à jour pour l'utilisateur {user_id}")
        return render_user_dashboard(request, user_id)
        
    except Exception as e:
        print(f"💥 Erreur Save Sources : {e}")
        return render_user_dashboard(request, user_id, f"Erreur sources : {e}")


if __name__ == "__main__":
    # Railway définit automatiquement une variable d'environnement PORT
    port = int(os.environ.get("PORT", 8000)) 
    # Utilise host="0.0.0.0" pour être accessible depuis l'extérieur
    uvicorn.run(app, host="0.0.0.0", port=port)