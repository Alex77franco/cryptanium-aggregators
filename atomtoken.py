import requests

def get_cosmos_token_balances(wallet_address, cosmos_rpc_url):

    try:
        url = f"{cosmos_rpc_url}/bank/v1beta1/balances/{wallet_address}"
        response = requests.get(url)
        response.raise_for_status()  
        data = response.json()

        if 'balances' in data:
            balances = {}
            for balance in data['balances']:
                denom = balance['denom']
                amount = balance['amount']
                token_id = get_token_id(denom)  
                balances[denom] = {
                    'amount': amount,
                    'token_id': token_id
                }
            return balances
        else:
            print(f"Warning: Unexpected response format. 'balances' field not found.")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching token balances: {e}")
        return {}

def get_token_id(denom):
    
    if denom == "uatom":
        return "cosmos:uatom"
    elif denom == "":
        return "ibc:27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
    else:
        return None

if __name__ == "__main__":
    wallet_address = "cosmos1c6nwjknq8hkfqdhwx6rvj6xt24asv4u7asjqy4"
    cosmos_rpc_url = "https://docs-demo.cosmos-mainnet.quiknode.pro/cosmos"  

    token_balances = get_cosmos_token_balances(wallet_address, cosmos_rpc_url)

    if token_balances:
        print("Tokens and their balances:")
        for denom, balance_info in token_balances.items():
            print(f"{denom}: Amount = {balance_info['amount']}, Token ID = {balance_info['token_id']}")
    else:
        print("Error: Could not retrieve token balances.")