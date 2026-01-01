import asyncio
import os
import psycopg2
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from trading_engine import passer_ordre_sur_compte, API_TOKEN
from metaapi_cloud_sdk import MetaApi

# --- CONFIGURATION ---
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

# --- GESTION GLOBALE ---
api_meta = None  # Sera initialisé dans demarrer_bot pour éviter l'erreur de loop
CONNEXIONS_ACTIVES = {}

async def obtenir_rpc_connection(account_id):
    """Réutilise une connexion RPC pour économiser le quota de 75 sessions"""
    global api_meta
    if account_id in CONNEXIONS_ACTIVES:
        conn = CONNEXIONS_ACTIVES[account_id]
        try:
            if conn.is_connected():
                return conn
        except: pass
    
    account = await api_meta.metatrader_account_api.get_account(account_id)
    connection = account.get_rpc_connection()
    await connection.connect()
    try:
        await asyncio.wait_for(connection.wait_synchronized(), timeout=10)
    except: pass
    
    CONNEXIONS_ACTIVES[account_id] = connection
    return connection

# --- INTELLIGENCE DE CORRECTION ---
def corriger_prix_intelligent(prix_signale, prix_actuel):
    if not prix_signale or prix_actuel <= 0: return prix_signale
    if prix_signale > prix_actuel * 5: return prix_signale / 10
    if prix_signale < prix_actuel / 5: return prix_signale * 10
    return prix_signale

# --- PARSER ---
def analyser_signal(texte):
    texte_clean = texte.upper().replace('\xa0', ' ').replace(':', ' ')
    lignes = texte_clean.split('\n')
    
    est_fermeture = any(w in texte_clean for w in ["CLOSE", "FERMER", "FERMEZ", "EXIT", "CLÔTURE", "FERMÉE"])
    est_partiel = any(w in texte_clean for w in ["PARTIELS", "MOITIÉ", "PARTIAL", "PARTIEL"])

    action = None
    if not (est_fermeture or est_partiel):
        if any(w in texte_clean for w in ["BUY", "ACHAT", "ACHÈTE"]): action = "BUY"
        elif any(w in texte_clean for w in ["SELL", "VENTE", "VENDS"]): action = "SELL"

    symbole = None
    mapping = {"GOLD": "XAUUSD", "BITCOIN": "BTCUSD", "OR": "XAUUSD", "NASDAQ": "NAS100"}
    for mot in texte_clean.split():
        mot_pur = re.sub(r'[^A-Z0-9]', '', mot)
        if mot_pur in mapping: symbole = mapping[mot_pur]; break
        if any(s in mot_pur for s in ["USD", "JPY", "GBP", "BTC", "ETH", "XAU"]): symbole = mot_pur; break

    tps_final, sl = [], None
    for ligne in lignes:
        if any(w in ligne for w in ["SL", "STOP", "LOSS"]):
            nums = re.findall(r"\d+\.?\d*", ligne)
            if nums: sl = float(nums[0])
        elif any(w in ligne for w in ["TP", "TARGET", "OBJ", "OBJECTIF", "OUVERT"]):
            if "OUVERT" in ligne or "OPEN" in ligne:
                tps_final.append(None)
            else:
                nums = re.findall(r"\d+\.?\d*", ligne)
                for n in nums:
                    val = float(n)
                    if val != sl: tps_final.append(val)

    if not tps_final and action:
        tps_final = [None, None, None, None]

    return action, symbole, tps_final, sl, est_fermeture, est_partiel

# --- TÂCHE DE FOND : SYNC PROFITS ---
async def surveiller_profits_cloture():
    global api_meta
    while True:
        try:
            if api_meta is None:
                await asyncio.sleep(2)
                continue

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, ticket_id FROM bilan_trades WHERE profit <= 0.01 AND ticket_id IS NOT NULL")
                    trades_a_sync = cur.fetchall()
                    if trades_a_sync:
                        cur.execute("SELECT DISTINCT metaapi_account_id FROM comptes_mt5 WHERE metaapi_account_id IS NOT NULL")
                        comptes = cur.fetchall()
                        for (acc_id,) in comptes:
                            connection = await obtenir_rpc_connection(acc_id)
                            for db_id, t_id in trades_a_sync:
                                history = await connection.get_deals_by_ticket(str(t_id))
                                if history and isinstance(history, list):
                                    p_net = sum(float(d.get('profit', 0)) + float(d.get('commission', 0)) + float(d.get('swap', 0)) for d in history if isinstance(d, dict))
                                    cur.execute("UPDATE bilan_trades SET profit = %s WHERE id = %s", (p_net, db_id))
                    conn.commit()
        except Exception as e: print(f"⚠️ Erreur Sync Bilan: {e}")
        await asyncio.sleep(300) # Attente de 5 minutes pour préserver le quota

# --- MOTEUR PRINCIPAL TELEGRAM ---
async def demarrer_bot():
    global api_meta
    # On initialise l'API ici, une seule fois, après le démarrage de la loop
    api_meta = MetaApi(API_TOKEN)
    
    try:
        with get_db_connection() as conn_init:
            with conn_init.cursor() as cur_init:
                cur_init.execute("SELECT string_session FROM sessions_telegram LIMIT 1")
                res = cur_init.fetchone()
        
        if not res: return print("❌ Session Telegram manquante.")

        client = TelegramClient(StringSession(res[0]), API_ID, API_HASH)
        await client.connect()
        print("🚀 BOT OPÉRATIONAL : Multi-Comptes & Breakeven")

        @client.on(events.NewMessage)
        async def handler(event):
            msg_id_actuel = event.id
            msg_id_tague = event.reply_to_msg_id if event.is_reply else None
            action, symbole, tps_list, sl_initial, est_total, est_partiel = analyser_signal(event.raw_text)

            with get_db_connection() as conn_h:
                with conn_h.cursor() as cur_h:
                    # Filtrage Source
                    cur_h.execute("SELECT user_id FROM sources WHERE canal_id = %s OR canal_id = %s", (str(event.chat_id), str(event.chat_id).replace("-100", "")))
                    if not cur_h.fetchone(): return

                    # --- LOGIQUE DE FERMETURE CIBLÉE & BREAKEVEN ---
                    if (est_total or est_partiel) and msg_id_tague:
                        print(f"🛑 ORDRE DE CLÔTURE DÉTECTÉ SUR MESSAGE #{msg_id_tague}")
                        cur_h.execute("""
                            SELECT b.ticket_id, c.metaapi_account_id FROM bilan_trades b 
                            JOIN comptes_mt5 c ON b.user_id = c.user_id 
                            WHERE b.telegram_msg_id = %s AND b.profit <= 0.01
                        """, (msg_id_tague,))
                        rows = cur_h.fetchall()
                        if rows:
                            acc_id = rows[0][1]
                            conn_mt5 = await obtenir_rpc_connection(acc_id)
                            if est_partiel:
                                ticket_a_fermer = rows[0][0]
                                try:
                                    await conn_mt5.close_position(ticket_a_fermer)
                                    cur_h.execute("UPDATE bilan_trades SET profit = 0.01 WHERE ticket_id = %s", (ticket_a_fermer,))
                                    print(f"✅ TP validé pour le ticket {ticket_a_fermer}")
                                except: pass
                                
                                # BREAKEVEN AUTOMATIQUE
                                positions_ouvertes = await conn_mt5.get_positions()
                                for pos in positions_ouvertes:
                                    if any(str(r[0]) == pos['id'] for r in rows if str(r[0]) != ticket_a_fermer):
                                        try:
                                            await conn_mt5.modify_position(pos['id'], {'stopLoss': pos['openPrice']})
                                            print(f"🛡️ BE activé pour {pos['id']} à {pos['openPrice']}")
                                        except Exception as e: print(f"⚠️ Erreur BE: {e}")
                            else:
                                for t_id, _ in rows:
                                    try: 
                                        await conn_mt5.close_position(t_id)
                                        print(f"✅ Position {t_id} fermée.")
                                    except: pass
                                cur_h.execute("UPDATE bilan_trades SET profit = 0.01 WHERE telegram_msg_id = %s", (msg_id_tague,))
                        conn_h.commit()
                        return 

                    # --- LOGIQUE D'OUVERTURE ---
                    if action and symbole:
                        cur_h.execute("""
                            SELECT m.metaapi_account_id, r.lot_fixe, r.user_id 
                            FROM comptes_mt5 m 
                            JOIN reglages_trading r ON m.user_id = r.user_id 
                            JOIN sources s ON m.user_id = s.user_id
                            WHERE r.bot_actif = TRUE AND (s.canal_id = %s OR s.canal_id = %s)
                        """, (str(event.chat_id), str(event.chat_id).replace("-100", "")))
                        
                        clients = cur_h.fetchall()
                        for acc_id, lot_fixe_db, u_id in clients:
                            lot = lot_fixe_db if lot_fixe_db > 0 else 0.1
                            try:
                                acc_m = await api_meta.metatrader_account_api.get_account(acc_id)
                                p_info = await acc_m.get_symbol_price(symbole)
                                p_live = p_info['ask'] if action == "BUY" else p_info['bid']
                            except: p_live = 0
                            
                            sl_f = corriger_prix_intelligent(sl_initial, p_live)
                            for tp_brut in tps_list:
                                tp_f = corriger_prix_intelligent(tp_brut, p_live) if tp_brut else None
                                res = await passer_ordre_sur_compte(acc_id, symbole, action, lot, tp_f, sl_f)
                                if res and 'orderId' in res:
                                    cur_h.execute("""
                                        INSERT INTO bilan_trades (user_id, symbole, type_ordre, lot, profit, date_trade, ticket_id, telegram_msg_id)
                                        VALUES (%s, %s, %s, %s, 0.0, NOW(), %s, %s)
                                    """, (u_id, symbole, action, lot, str(res['orderId']), msg_id_actuel))
                        conn_h.commit()

        await asyncio.gather(client.run_until_disconnected(), surveiller_profits_cloture())
    except Exception as e: print(f"💥 ERREUR : {e}")

if __name__ == "__main__":
    asyncio.run(demarrer_bot())