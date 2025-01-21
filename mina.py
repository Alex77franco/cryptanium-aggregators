 
import requests
import json

def parse_mina_explorer_response(response_data):
  """
  Parses the given response data from the Mina Explorer API.

  Args:
      response_data: The JSON response data from the API.

  Returns:
      A dictionary containing extracted information:
          - public_key: The public key of the account.
          - balance: The total balance of the account.
          - nonce: The current nonce of the account.
          - delegate: The current delegate for staking.
          - voting_for: The current voting choice.
          - total_tx: The total number of transactions.
          - staking_info: Information about current and next epoch staking.
  """

  data = {}
  account_data = response_data.get('account', {})

  data['public_key'] = account_data.get('publicKey')
  data['balance'] = account_data.get('balance', {}).get('total')
  data['nonce'] = account_data.get('nonce')
  data['delegate'] = account_data.get('delegate')
  data['voting_for'] = account_data.get('votingFor')
  data['total_tx'] = account_data.get('totalTx')

  # Extract staking information
  staking_info = {
      'current_epoch': {
          'balance': account_data.get('epochStakingAccount', [{}])[0].get('balance'),
          'delegate': account_data.get('epochStakingAccount', [{}])[0].get('delegate'),
          'voting_for': account_data.get('epochStakingAccount', [{}])[0].get('voting_for'),
      },
      'next_epoch': {
          'balance': account_data.get('nextEpochStakingAccount', [{}])[0].get('balance'),
          'delegate': account_data.get('nextEpochStakingAccount', [{}])[0].get('delegate'),
          'voting_for': account_data.get('nextEpochStakingAccount', [{}])[0].get('voting_for'),
      }
  }
  data['staking_info'] = staking_info

  return data


def get_mina_transactions_rest(public_key):
  """
  Fetches transaction history for the given MINA wallet using a GET request to a REST API.

  Args:
      public_key: MINA wallet's public key.

  Returns:
      A list of dictionaries, where each dictionary represents a transaction with 
      keys: 'from' (optional), 'to' (optional), 'amount' (optional), 'timestamp', 'fee' (optional).  
      Note that not all data may be available in the API response.
  """
  try:
    url = f"https://api.minaexplorer.com/accounts/{public_key}"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    if data:
        account_info = parse_mina_explorer_response(data)
        
        return account_info
    else:
      print(f"Error: Unexpected response format from API.")
      return []

  except requests.exceptions.RequestException as e:
    print(f"Error fetching transaction history: {e}")
    return []

if __name__ == "__main__":
  public_key = "B62qjTJPtZ8sPeLyaCQMHebSYj2GPwGvhnTeR2gr8jUEYSsGFxADXEH"
  transactions = get_mina_transactions_rest(public_key)

  # Write transactions to JSON file
  with open("mina.json", "w") as f:
    json.dump(transactions, f, indent=4)
