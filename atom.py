import requests
import json

def get_atom_balance_rpc(wallet_address, cosmos_rpc_url):
  """
  Fetches the current balance for the given ATOM wallet address using the Cosmos SDK gRPC API.

  Args:
      wallet_address: ATOM wallet address (e.g., "cosmos1c6nwjknq8hkfqdhwx6rvj6xt24asv4u7asjqy4").
      cosmos_rpc_url: URL of the Cosmos node's gRPC endpoint.

  Returns:
      A dictionary containing the wallet's balance information 
      (structure depends on the actual API response).
  """
  try:
      # Replace with the actual gRPC method for balance (if different)
      method = "balances"

      url = f"{cosmos_rpc_url}/{method}/{wallet_address}"  # Construct URL like the curl command

      headers = {"Content-Type": "application/json"}

      response = requests.get(url, headers=headers)
      response.raise_for_status()  # Raise an exception for bad status codes
      data = response.json()

      return data

  except requests.exceptions.RequestException as e:
      print(f"Error fetching balance: {e}")
      return {}

if __name__ == "__main__":
  wallet_address = "cosmos1c6nwjknq8hkfqdhwx6rvj6xt24asv4u7asjqy4"
  cosmos_rpc_url = "https://docs-demo.cosmos-mainnet.quiknode.pro/cosmos/bank/v1beta1"

  balance_data = get_atom_balance_rpc(wallet_address, cosmos_rpc_url)
  if balance_data:
     # Write transactions to JSON file
    filename = f"{wallet_address}.json"
    with open(filename, "w") as f:
        json.dump(balance_data, f, indent=4)
