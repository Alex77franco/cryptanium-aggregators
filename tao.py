import requests
import json
from dotenv import dotenv_values

config = dotenv_values(".env")
tao_key = config.get("TAO_KEY")

def get_tao_balance_rpc(wallet_address, tao_rpc_url):
  try:
      # Replace with the actual method name for balance (if different)
      method = "address"

      url = f"{tao_rpc_url}?{method}={wallet_address}"  # Construct URL
      headers = {
          "accept": "application/json",
          "Authorization": tao_key  # Replace if needed
      }

      response = requests.get(url, headers=headers)
      response.raise_for_status()  # Raise an exception for bad status codes
      return response.json()

  except requests.exceptions.RequestException as e:
      print(f"Error fetching balance for {wallet_address}: {e}")
      return None

if __name__ == "__main__":
  wallet_addresses = [
      "5EcYxFfwKLKogdKkGdz88ZFh2J6TqpygRGdRqHWADii9vzYb",
      "5Fqxv8Ba3GG6BHWMeUScGHt39ddJmafAnGkuxxCRXicSYVWY",
      "5DMxfUJfhSskQnSkzJnFJQns1Ej2FbZLAFjfs5mSTjccLkx8"
  ]

  for wallet_address in wallet_addresses:
    balance_data = get_tao_balance_rpc(wallet_address, tao_rpc_url="https://api.taostats.io/api/account/history/v1")
    if balance_data:
      # Create filename based on wallet address
      filename = f"{wallet_address}.json"
      with open(filename, "w") as f:
        json.dump(balance_data, f, indent=4)
        print(f"Balance for {wallet_address} written to {filename}")
    else:
      print(f"Failed to retrieve balance for {wallet_address}.")