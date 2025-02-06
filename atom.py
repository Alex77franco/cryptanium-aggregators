import os
import requests
import csv
import time
from datetime import datetime
import threading

BASE_URL = "https://docs-demo.cosmos-mainnet.quiknode.pro"
ADDRESS = "cosmos1c6nwjknq8hkfqdhwx6rvj6xt24asv4u7asjqy4"
DEXSCREENER_URL = "https://api.dexscreener.com/tokens/v1/bsc/0x0Eb3a705fc54725037CC9e008bDede697f62F335" #pulling price of ATOM on BSC - No cosmos data on dexscreener.
REPORTS_FOLDER = "reports"

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

def get_available_balance(address):
    """Fetch the available (spendable) ATOM balance for a given Cosmos address."""
    url = f"{BASE_URL}/cosmos/bank/v1beta1/balances/{address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        balances = response.json().get("balances", [])
        for balance in balances:
            if balance["denom"] == "uatom":
                return int(balance["amount"]) / 1_000_000 
        return 0.0
    except requests.RequestException as err:
        print(f"Error fetching available balance: {err}")
        return 0.0

def get_delegated_balance(address):
    """Fetch the delegated balance (staked) for a given Cosmos address."""
    url = f"{BASE_URL}/cosmos/staking/v1beta1/delegations/{address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        delegations = response.json().get("delegation_responses", [])
        total_delegated = sum(int(delegation["balance"]["amount"]) for delegation in delegations)
        return total_delegated / 1_000_000 
    except requests.RequestException as err:
        print(f"Error fetching delegated balance: {err}")
        return 0.0

def get_rewards(address):
    """Fetch staking rewards for a given Cosmos address."""
    url = f"{BASE_URL}/cosmos/distribution/v1beta1/delegators/{address}/rewards"
    try:
        response = requests.get(url)
        response.raise_for_status()
        rewards = response.json().get("total", [])
        for reward in rewards:
            if reward["denom"] == "uatom":
                return float(reward["amount"]) / 1_000_000 
        return 0.0
    except requests.RequestException as err:
        print(f"Error fetching rewards: {err}")
        return 0.0

def get_atom_price():
    """Fetch the current price of ATOM from Dexscreener."""
    try:
        response = requests.get(DEXSCREENER_URL)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return float(data[0]["priceUsd"])
        return 0.0
    except requests.RequestException as err:
        print(f"Error fetching ATOM price: {err}")
        return 0.0

def export_to_csv(data, filename):
    """Export the results to a CSV file, including a total value row."""
    try:
        data = sorted(data, key=lambda x: float(x['Total Value (USD)']), reverse=True)

        os.makedirs(REPORTS_FOLDER, exist_ok=True)

        file_path = os.path.join(REPORTS_FOLDER, filename)

        with open(file_path, mode='w', newline='') as csvfile:
            fieldnames = ['Category', 'Balance', 'Price (USD)', 'Total Value (USD)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            total_value_sum = 0.0

            for row in data:
                total_value_sum += float(row['Total Value (USD)'])
                writer.writerow(row)

            writer.writerow({})
            writer.writerow({})
            writer.writerow({})
            writer.writerow({
                "Category": "TOTAL",
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

    atom_price = get_atom_price()
    available_balance = get_available_balance(ADDRESS)
    delegated_balance = get_delegated_balance(ADDRESS)
    rewards = get_rewards(ADDRESS)

    loading = False
    loading_thread.join()

    results = [
        {
            "Category": "Available Balance",
            "Balance": f"{available_balance:.6f}",
            "Price (USD)": f"{atom_price:.6f}",
            "Total Value (USD)": f"{available_balance * atom_price:.6f}"
        },
        {
            "Category": "Delegated Balance",
            "Balance": f"{delegated_balance:.6f}",
            "Price (USD)": f"{atom_price:.6f}",
            "Total Value (USD)": f"{delegated_balance * atom_price:.6f}"
        },
        {
            "Category": "Rewards",
            "Balance": f"{rewards:.6f}",
            "Price (USD)": f"{atom_price:.6f}",
            "Total Value (USD)": f"{rewards * atom_price:.6f}"
        }
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ADDRESS}_Cosmos_{timestamp}.csv"
    export_to_csv(results, filename)

    print("Done!")

if __name__ == "__main__":
    main()
