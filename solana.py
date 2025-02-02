import os
import requests
import csv
import time
from datetime import datetime
import threading

# Constants
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
DEX_SCREENER_API_URL = "https://api.dexscreener.com/tokens/v1/solana/"
WALLET_ADDRESS = "5Z7UwKzHbYfoJos5MZmLPbDpgkCbAayteirQT3aU5hRU"
REPORTS_FOLDER = "reports"

# Loading animation
loading = True

def show_loading(message):
    """Show a loading animation in the terminal."""
    global loading
    dots = 0
    while loading:
        print(f"\r{message}{'.' * (dots % 4)}", end='', flush=True)
        dots += 1
        time.sleep(0.5)

    # After loading stops, persist the message with dots
    print(f"\r{message}...", end='', flush=True)

def get_solana_balance(wallet_address: str) -> float:
    """Fetch the SOL balance for a given wallet address."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }

    try:
        response = requests.post(RPC_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        balance_lamports = data['result']['value']
        balance_sol = balance_lamports / 1_000_000_000  # 1 SOL = 1,000,000,000 Lamports
        return balance_sol
    except requests.RequestException as e:
        print(f"\nRequest error: {e}")
    except KeyError:
        print("\nError parsing response data.")
    return 0.0

def get_spl_tokens(wallet_address: str):
    """Fetch the SPL tokens for a given wallet address."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # Token Program ID
            {"encoding": "jsonParsed"}
        ]
    }

    try:
        response = requests.post(RPC_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        token_accounts = data['result']['value']
        tokens = []

        for account in token_accounts:
            mint_address = account['account']['data']['parsed']['info']['mint']
            token_amount = account['account']['data']['parsed']['info']['tokenAmount']
            ui_amount = float(token_amount['uiAmount'])
            tokens.append({"mint": mint_address, "amount": ui_amount})

        return tokens
    except requests.RequestException as e:
        print(f"\nRequest error: {e}")
    except KeyError:
        print("\nError parsing response data.")
    return []

def get_token_metadata_and_price(token_address: str):
    """Fetch token metadata and price from the DEX Screener API."""
    try:
        response = requests.get(DEX_SCREENER_API_URL + token_address)
        if response.status_code == 200:
            data = response.json()
            if data:
                for pair in data:
                    base_token = pair.get('baseToken', {})
                    name = base_token.get('name', 'Unknown')
                    symbol = base_token.get('symbol', 'UNKNOWN')
                    price_usd = float(pair.get('priceUsd', 0.0))
                    return name, symbol, price_usd
        else:
            print(f"\nError fetching metadata for {token_address} (Status Code: {response.status_code})")
    except requests.RequestException as e:
        print(f"\nRequest error: {e}")

    return "Unknown Token", "UNKNOWN", 0.0

def export_to_csv(data: list, filename: str):
    """Export the results to a CSV file, including a total value row."""
    try:
        # Sort data by the "Total Value (USD)" column in descending order
        data = sorted(data, key=lambda x: float(x['Total Value (USD)']), reverse=True)

        # Ensure the "reports" directory exists
        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        # Construct the full file path inside the "reports" directory
        file_path = os.path.join(REPORTS_FOLDER, filename)
        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = ['Token Name', 'Symbol', 'Address', 'Balance', 'Price (USD)', 'Total Value (USD)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            total_value_sum = 0.0

            for row in data:
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            # Add 3 empty rows and then write the total value row
            writer.writerow({})
            writer.writerow({})
            writer.writerow({})
            writer.writerow({
                "Token Name": "TOTAL",
                "Symbol": "",
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

    # Start loading animation
    loading_thread = threading.Thread(target=show_loading, args=("Fetching data",))
    loading_thread.start()

    # Get SOL balance and price
    sol_balance = get_solana_balance(WALLET_ADDRESS)
    _, _, sol_price = get_token_metadata_and_price("So11111111111111111111111111111111111111112")  # SOL token address on Solana

    # Get SPL token balances and prices
    results = []
    results.append({
        "Token Name": "Solana",
        "Symbol": "SOL",
        "Address": "native SOL",
        "Balance": f"{sol_balance:.6f}",
        "Price (USD)": f"{sol_price:.6f}",
        "Total Value (USD)": f"{sol_balance * sol_price:.6f}"
    })

    tokens = get_spl_tokens(WALLET_ADDRESS)
    if tokens:
        for token in tokens:
            mint_address = token['mint']
            balance = token['amount']
            name, symbol, price_usd = get_token_metadata_and_price(mint_address)
            total_value = balance * price_usd

            # Add to CSV results
            results.append({
                "Token Name": name,
                "Symbol": symbol,
                "Address": mint_address,
                "Balance": balance,
                "Price (USD)": f"{price_usd:.6f}",
                "Total Value (USD)": f"{total_value:.6f}"
            })

    # Stop loading animation and persist message
    loading = False
    loading_thread.join()

    # CSV creation message
    print("\nCreating CSV file...")

    # Export data to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{WALLET_ADDRESS}_Solana_{timestamp}.csv"
    export_to_csv(results, filename)

    print("Done!")

if __name__ == "__main__":
    main()
