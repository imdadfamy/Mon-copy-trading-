import psycopg2

# Configuration de ta base PostgreSQL
DB_CONFIG = {
    "dbname": "copytrader_db",
    "user": "imdade_user",
    "password": "ton_mot_de_pass_ici",
    "host": "localhost",
    "port": "5432"
}

def enregistrer_compte_trading():
    print("--- Configuration de votre compte MetaTrader 5 ---")
    email = input("Entrez l'email de votre compte site : ")
    
    # Infos demandées par le broker
    login_mt5 = input("Numéro de compte (Login) : ")
    password_mt5 = input("Mot de passe de trading : ")
    server_mt5 = input("Serveur du Broker (ex: ICVM-Demo ou MetaQuotes-Demo) : ")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. On vérifie si l'utilisateur existe
        cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            user_id = user[0]
            # 2. On insère les données MT5
            cur.execute(
                """INSERT INTO comptes_mt5 (user_id, mt5_login, mt5_password, mt5_server) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, login_mt5, password_mt5, server_mt5)
            )
            conn.commit()
            print(f"\n✅ Compte MT5 lié avec succès à l'utilisateur {email} !")
        else:
            print("\n❌ Erreur : Cet email n'existe pas dans notre base.")

    except Exception as e:
        print(f"❌ Erreur de base de données : {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    enregistrer_compte_trading()