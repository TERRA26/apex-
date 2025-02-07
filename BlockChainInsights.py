import requests
from web3 import Web3
import json
from datetime import datetime


class BlockchainInsightsAgent:
    def __init__(self):
        self.chat_endpoint = "https://autonome.alt.technology/apex-owfsxk/chat"
        self.session = requests.Session()
        self.session.auth = ("apex", "eUUeBYoizG")

        # Use public Ethereum RPC endpoint
        self.w3 = Web3(Web3.HTTPProvider('https://ethereum.publicnode.com'))

        # Common token addresses
        self.tokens = {
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        }

    def format_block_data(self, block):
        return {
            'number': block['number'],
            'timestamp': datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            'transactions': len(block['transactions']),
            'gas_used': block['gasUsed'],
            'gas_limit': block['gasLimit'],
            'base_fee': block.get('baseFeePerGas', 0)
        }

    def get_latest_blocks(self, count=3):
        try:
            latest = self.w3.eth.block_number
            blocks = []

            for i in range(count):
                block = self.w3.eth.get_block(latest - i, full_transactions=False)
                blocks.append(self.format_block_data(dict(block)))

            # Create analysis prompt
            block_info = []
            for b in blocks:
                block_info.append(f"Block {b['number']}:")
                block_info.append(f"- Time: {b['timestamp']}")
                block_info.append(f"- Transactions: {b['transactions']}")
                block_info.append(f"- Gas Used: {b['gas_used']:,}")
                block_info.append(f"- Gas Limit: {b['gas_limit']:,}")
                if b['base_fee']:
                    block_info.append(f"- Base Fee: {self.w3.from_wei(b['base_fee'], 'gwei')} gwei")
                block_info.append("")

            analysis_prompt = "Analyze these recent Ethereum blocks and provide insights:\n\n" + "\n".join(block_info)
            return self.get_ai_analysis(analysis_prompt)

        except Exception as e:
            return f"Error fetching blocks: {str(e)}"

    def get_wallet_analysis(self, address):
        try:
            if not self.w3.is_address(address):
                return "Invalid Ethereum address format"

            balance = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance, 'ether')

            analysis_prompt = f"""Analyze this Ethereum wallet:
            Address: {address}
            Balance: {balance_eth:.4f} ETH

            Provide insights about:
            1. The wallet's ETH holdings
            2. Whether this appears to be a personal wallet or contract
            3. Any notable observations about the balance
            """

            return self.get_ai_analysis(analysis_prompt)

        except Exception as e:
            return f"Error analyzing wallet: {str(e)}"

    def get_ai_analysis(self, prompt):
        try:
            response = self.session.post(
                self.chat_endpoint,
                json={"message": prompt},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get('response', 'No analysis provided')
            else:
                return f"Error getting AI analysis (Status {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    agent = BlockchainInsightsAgent()
    print("Blockchain Insights Agent (type 'quit' to exit)")
    print("-" * 50)

    while True:
        print("\nOptions:")
        print("1. Analyze Recent Blocks")
        print("2. Analyze Wallet")
        print("3. Quit")

        choice = input("\nChoice: ")

        if choice == "1":
            print("\nFetching recent blocks...")
            analysis = agent.get_latest_blocks()
            print(f"\nAnalysis:\n{analysis}")

        elif choice == "2":
            address = input("\nEnter Ethereum address: ")
            print("\nAnalyzing wallet...")
            analysis = agent.get_wallet_analysis(address)
            print(f"\nAnalysis:\n{analysis}")

        elif choice == "3" or choice.lower() == 'quit':
            break

        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()