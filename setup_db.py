import psycopg2

# Remplace par les infos que tu as choisies à l'étape précédente
DB_CONFIG = {
    "dbname": "copytrader_db",
    "user": "imdade_user",
    "password": "ton_mot_de_pass_ici",
    "host": "localhost",
    "port": "5432"
}

def create_tables():
    commands = (
        """
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            mot_de_passe VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions_telegram (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES utilisateurs(id),
            phone VARCHAR(20),
            string_session TEXT NOT NULL,
            canal_source_id BIGINT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS comptes_mt5 (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES utilisateurs(id),
            mt5_login VARCHAR(50),
            mt5_password VARCHAR(100),
            mt5_server VARCHAR(100),
            risk_percent DECIMAL DEFAULT 1.0
        )
        """
    )
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        cur.close()
        conn.commit()
        print("Les tables ont été créées avec succès dans PostgreSQL !")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    create_tables()