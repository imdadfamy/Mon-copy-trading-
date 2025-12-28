


import psycopg2
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = 30882701
API_HASH = 'ce3413ef77f883d43cc2629addb54790'
DB_CONFIG = {
    "dbname": "copytrader_db",
    "user": "imdade_user",
    "password": "ton_mot_de_pass_ici",
    "host": "localhost",
    "port": "5432"
}

def demarrer_processus_complet():
    email_utilisateur = input("Entrez l'email pour ce compte : ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Création de l'utilisateur
        cur.execute("INSERT INTO utilisateurs (email, mot_de_passe) VALUES (%s, %s) RETURNING id", 
                    (email_utilisateur, "password_provisoire"))
        user_id = cur.fetchone()[0]

        # 2. Lancement de la connexion Telegram
        print("\n--- Connexion Telegram en cours ---")
        with TelegramClient(StringSession(), API_ID, API_HASH) as client:
            session_str = client.session.save()
            me = client.get_me()
            telephone = me.phone if me.phone else "Inconnu"

            # 3. Récupération immédiate des canaux
            print(f"\nConnecté en tant que : {me.first_name}")
            print("Récupération de tes canaux en cours...")
            
            dialogs = client.get_dialogs()
            canaux_valides = [d for d in dialogs if d.is_channel or d.is_group]

            for i, canal in enumerate(canaux_valides):
                print(f"{i}. {canal.name}")

            choix = int(input("\nEntre le numéro du canal à copier : "))
            canal_choisi = canaux_valides[choix]

            # 4. On enregistre tout en une seule fois dans la base de données
            cur.execute(
                """INSERT INTO sessions_telegram (user_id, phone, string_session, canal_source_id) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, telephone, session_str, canal_choisi.id)
            )
            
            conn.commit()
            print(f"\n✅ Terminé ! Utilisateur créé, Session sauvegardée et Canal '{canal_choisi.name}' lié.")

    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    demarrer_processus_complet()