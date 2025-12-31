import httpx
import asyncio
from metaapi_cloud_sdk import MetaApi

# --- CONFIGURATION ---
# Nettoyage du token (suppression du 'é' parasite à la fin)
API_TOKEN = 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI3OWRhNjFhMGVmZTg1OThkZDBlMzhmNDFiMTFjNDJjOSIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiNzlkYTYxYTBlZmU4NTk4ZGQwZTM4ZjQxYjExYzQyYzkiLCJpYXQiOjE3NjY2NzUyNjh9.NMWCHVMrBR5uE4wZ8iVdNBkB-zG4qaEydhAcm1IoOdYNym9a33e7xoxmOY9A6ToorwOG2h_AUpN8QfZw46zD7zbEqNQOaiwyFpJhCswmJ76Rt4ITZgIcvdFwiF2eFNkmWwv4agnrwp-QBdzTHgX6EYWtwNDRP19UHGJCbtKLcoDzLdv3MArGRNJqj_llvJkgYCOAg3i9HNg5mN3cJbNEXhQuhjufDiLwHig8bFftSltHmUEQxR22_ks3xjg1aR5FvrejtKtH4Yde5GzvOZwMh1g6NbENtI1H5dgQhO0R19uVLO2wktGMO3VnRwYf74Ct91lBzh9IMUOzTELtO38U3PAmNOHql49yGaapY0oS2p52Bc-z7gIPiqSxynhubggCWJxVbe4mSCrktp34xnnJU2LVoNj9gnOqLn9D3q8x34EkCjnfibnwFU8S4QTXiJadrLR0H3V-7Rt4opFsNWQ8Ywn-X_TP566RtTywcTgHnwc23KP0MGPaBmeG0ytgF8D8IM_qcdqtb5yL50ZtP0qCdpLWKUByurb2Kpa3WMJw_AJ_mTTjnBmaRGy8CLuivtRlp-DkrAg8uDJ7stzoG-CFbWRWSFAzJJxI2wuAjSpKqaqXfii96vK63Y77K2wt1m-c7CiwEs6eJFqOIyIfz4h1lC48DU-fo3pKANsiL4ItIJk'


async def passer_ordre_sur_compte(account_id, symbol, action, lot, tp=None, sl=None):
    """Exécute un ordre au marché et retourne le résultat complet (dont l'orderId)"""
    api = MetaApi(API_TOKEN)
    try:
        account = await api.metatrader_account_api.get_account(account_id)
        
        if account.state != 'DEPLOYED':
            await account.deploy()
            await account.wait_deployed()
        
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized() #

        print(f"SENDING ORDER: {action} {symbol} (Lot: {lot}) TP: {tp} SL: {sl}")
        
        # On s'assure que les valeurs sont au bon format
        lot = float(lot)
        tp = float(tp) if tp else None
        sl = float(sl) if sl else None

        if action == "BUY":
            result = await connection.create_market_buy_order(symbol, lot, sl, tp)
        else:
            result = await connection.create_market_sell_order(symbol, lot, sl, tp)
        
        print(f"✅ SUCCESS: Order placed! ID: {result['orderId']}")
        # TRÈS IMPORTANT : Retourner le dictionnaire pour que le listener récupère l'orderId
        return result 
    except Exception as e:
        err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        print(f"ORDER ERROR for {account_id} : {err_msg}")
        return None

async def fermer_toutes_positions(account_id, symbol=None):
    """Ferme les positions de manière prioritaire et rapide"""
    api = MetaApi(API_TOKEN)
    try:
        print(f"📡 Tentative de fermeture pour le compte: {account_id}") # Pour voir si la fonction se lance
        account = await api.metatrader_account_api.get_account(account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        
        # On n'attend PAS wait_synchronized() ici pour aller plus vite
        positions = await connection.get_positions()
        
        if not positions:
            print(f"ℹ️ Aucune position à fermer sur {account_id}")
            return True

        count = 0
        for pos in positions:
            # Si un symbole est précisé, on ne ferme que celui-là
            if symbol and pos['symbol'] != symbol:
                continue
            
            print(f"📉 FERMETURE EN COURS : {pos['symbol']} (ID: {pos['id']})")
            await connection.close_position(pos['id']) #
            count += 1
            
        print(f"✅ Succès : {count} positions fermées.")
        return True
    except Exception as e:
        print(f"❌ Erreur critique dans fermer_toutes_positions : {e}")
        return False
# À la fin de trading_engine.py, tout à gauche :
async def modifier_sl_position(account_id, position_id, nouveau_sl):
    api_meta = MetaApi(API_TOKEN)
    try:
        account = await api_meta.metatrader_account_api.get_account(account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        # On utilise le nom d'argument exact pour éviter l'erreur 'value'
        await connection.modify_position(str(position_id), stop_loss=float(nouveau_sl))
        return True
    except Exception as e:
        print(f"❌ Erreur modif SL : {e}")
        return False