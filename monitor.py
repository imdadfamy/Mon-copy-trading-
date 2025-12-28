import asyncio
from metaapi_cloud_sdk import MetaApi

API_TOKEN = 'TON_TOKEN_METAAPI'

async def monitor_breakeven(account_id):
    api = MetaApi(API_TOKEN)
    try:
        account = await api.metatrader_account_api.get_account(account_id)
        if account.state != 'DEPLOYED':
            await account.deploy()
            await account.wait_deployed()

        connection = await account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronization()

        print(f"👀 Surveillance active pour le compte {account_id}...")

        # On récupère les positions actuelles
        positions = await connection.get_positions()
        
        # On garde en mémoire le prix d'entrée du groupe de positions
        # (Hypothèse : toutes les positions ouvertes en même temps sur un symbole ont le même prix d'entrée)
        
        while True:
            # On rafraîchit la liste des positions
            current_positions = await connection.get_positions()
            
            # Si le nombre de positions a diminué, cela veut dire qu'un TP a été touché
            # Ou on peut vérifier si une position spécifique (celle du TP1) a disparu
            
            # Logique simplifiée : Si une position est fermée en profit, 
            # on passe les autres au Breakeven.
            
            # Pour chaque symbole actif
            symboles_actifs = set(p['symbol'] for p in current_positions)
            
            for symbole in symboles_actifs:
                pos_du_symbole = [p for p in current_positions if p['symbol'] == symbole]
                
                # Si on détecte qu'il reste des positions mais que le prix a bien avancé
                for p in pos_du_symbole:
                    prix_entree = float(p['openPrice'])
                    prix_actuel = float(p['currentPrice'])
                    type_ordre = p['type'] # POSITION_TYPE_BUY ou POSITION_TYPE_SELL
                    
                    # Vérification si on doit passer au Breakeven
                    # (Exemple : si le prix a dépassé le TP1)
                    doit_passer_be = False
                    if type_ordre == 'POSITION_TYPE_BUY' and prix_actuel > (prix_entree + 0.0005): # +5 pips
                         doit_passer_be = True
                    elif type_ordre == 'POSITION_TYPE_SELL' and prix_actuel < (prix_entree - 0.0005):
                         doit_passer_be = True
                         
                    if doit_passer_be and float(p['stopLoss']) != prix_entree:
                        print(f"🛡️ Passage au Breakeven pour {symbole} (Position {p['id']})")
                        try:
                            await connection.modify_position(p['id'], {'stopLoss': prix_entree})
                        except Exception as e:
                            print(f"Erreur modif SL : {e}")

            await asyncio.sleep(5) # Vérification toutes les 5 secondes

    except Exception as e:
        print(f"Erreur Monitor : {e}")

if __name__ == "__main__":
    # Remplace par un ID de test pour essayer
    asyncio.run(monitor_breakeven('ID_DE_TON_COMPTE_MT5'))