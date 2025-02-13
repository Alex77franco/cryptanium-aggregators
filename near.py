import requests
import json
import base64
import os
import csv
import threading
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

NEAR_RPC_URL = "https://rpc.mainnet.near.org"

contract_address = "ledgerbyfigment.poolv1.near"
method_name = "get_account"

account_id = "cfdf371346821425cffe9ddd42cd0645c44d8837d614fc884a712a8662e50cfa"

PIKESPEAK_API_URL = "https://api.pikespeak.ai/account/wealth/"
REPORTS_FOLDER = "reports"
API_KEY = os.getenv("PIKESPEAK_API_KEY")

loading = True

def show_loading(message):
    """Show a loading animation in the terminal."""
    global loading
    dots = 0
    while loading:
        print(f"\r{message}{'.' * (dots % 4)}", end='', flush=True)
        dots += 1
        time.sleep(0.5)
    print(f"\r{message}...", end='', flush=True)

def safe_float(value, default=0.0):
    """Convert a value to float safely, with a default fallback."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def get_staked_near_balance():
    """Fetch the staked NEAR balance using the NEAR RPC."""
    data = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "query",
        "params": {
            "request_type": "call_function",
            "finality": "final",
            "account_id": contract_address,
            "method_name": method_name,
            "args_base64": base64.b64encode(json.dumps({"account_id": account_id}).encode("utf-8")).decode("utf-8")
        }
    }

    response = requests.post(NEAR_RPC_URL, json=data)

    if response.status_code == 200:
        result = response.json()
        if "result" in result and "result" in result["result"]:
            decoded_result = json.loads(bytes(result["result"]["result"]).decode("utf-8"))
            staked_balance = int(decoded_result.get("staked_balance", "0")) / 1e24
            return staked_balance
        else:
            print("Unexpected response format:", result)
            return 0.0
    else:
        print(f"Failed to fetch staked balance. Status code: {response.status_code}")
        print(response.text)
        return 0.0

def get_account_balances(account_id):
    """Fetch all token balances for a given NEAR account using the Pikespeak API."""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{PIKESPEAK_API_URL}{account_id}", headers=headers)
        response.raise_for_status()
        data = response.json()

        balances = data.get('balance', [])
        if not balances:
            print("No tokens found for this account.")
            return []

        results = []
        for token in balances:
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('contract', 'Unknown')
            balance = safe_float(token.get('amount', 0))
            price_usd = safe_float(token.get('tokenPrice'))
            total_value = safe_float(token.get('usdValue'))

            results.append({
                "Symbol": symbol,
                "Address": address,
                "Balance": f"{balance:.6f}",
                "Price (USD)": f"{price_usd:.6f}",
                "Total Value (USD)": f"{total_value:.6f}"
            })

        return results
    except requests.RequestException as e:
        print(f"Error fetching balances: {e}")
        return []

def export_to_csv(data, filename, staked_near_balance, near_price):
    """Export the results to a CSV file."""
    try:
        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = ['Symbol', 'Address', 'Balance', 'Price (USD)', 'Total Value (USD)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            total_value_sum = 0.0

            for row in data:
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            staked_total_value = staked_near_balance * near_price
            writer.writerow({
                "Symbol": "Stacked NEAR",
                "Address": contract_address,
                "Balance": f"{staked_near_balance:.6f}",
                "Price (USD)": f"{near_price:.6f}",
                "Total Value (USD)": f"{staked_total_value:.6f}"
            })

            total_value_sum += staked_total_value
            writer.writerow({})
            writer.writerow({
                "Symbol": "TOTAL",
                "Address": "",
                "Balance": "",
                "Price (USD)": "",
                "Total Value (USD)": f"{total_value_sum:.6f}"
            })

        print(f"\nData successfully exported to {file_path}")
    except Exception as e:
        print(f"\nError exporting to CSV: {e}")

def main():
    global loading

    print("Running...")
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    token_data = get_account_balances(account_id)
    staked_near_balance = get_staked_near_balance()

    loading = False
    loading_thread.join()

    if token_data:
        near_price = next((float(token['Price (USD)']) for token in token_data if token['Symbol'] == 'NEAR'), 0.0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{account_id}_NEAR_{timestamp}.csv"
        export_to_csv(token_data, filename, staked_near_balance, near_price)

    print("Done!")

if __name__ == "__main__":
    main()