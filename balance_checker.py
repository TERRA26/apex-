import os
from dotenv import load_dotenv
import requests
from typing import Optional, Dict

load_dotenv()

class AgentKitClient:
    def __init__(self):
        self.api_key = os.getenv('AGENTKIT_API_KEY')
        if not self.api_key:
            raise ValueError("AGENTKIT_API_KEY not found in environment variables")
        self.base_url = "https://api.coinbase.com/v2"
        
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
    def get_balance(self, address: Optional[str] = None, token: Optional[str] = None) -> Dict:
        """
        Get balance for a specific address and token
        :param address: Optional wallet address. If not provided, uses default wallet
        :param token: Optional token symbol (e.g., 'ETH', 'USDC'). If not provided, gets all balances
        :return: Dictionary containing balance information
        """
        endpoint = f"{self.base_url}/accounts"
        params = {}
        
        if address:
            params['address'] = address
        if token:
            params['currency'] = token
            
        try:
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._format_balance_response(data)
            else:
                return {
                    'error': f"Failed to get balance: {response.status_code}",
                    'details': response.text
                }
                
        except Exception as e:
            return {'error': f"Error fetching balance: {str(e)}"}
            
    def _format_balance_response(self, data: Dict) -> Dict:
        """Format the balance response into a more readable format"""
        balances = {}
        for account in data.get('data', []):
            currency = account.get('currency', {}).get('code', 'UNKNOWN')
            balance = {
                'amount': account.get('balance', {}).get('amount', '0'),
                'native_amount': account.get('native_balance', {}).get('amount', '0'),
                'native_currency': account.get('native_balance', {}).get('currency', 'USD')
            }
            balances[currency] = balance
            
        return {
            'balances': balances,
            'total_count': len(balances)
        }

def main():
    try:
        client = AgentKitClient()
        
        # Get all balances
        print("Fetching all balances...")
        result = client.get_balance()
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
            
        print("\nYour Balances:")
        print("-" * 50)
        
        for currency, balance in result['balances'].items():
            print(f"{currency}:")
            print(f"  Amount: {balance['amount']} {currency}")
            print(f"  Value: ${balance['native_amount']} {balance['native_currency']}")
            print("-" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
