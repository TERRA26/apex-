from typing import Dict, Any
import aiohttp
from config import config
from web3 import Web3
from flow_py_sdk import flow_client

class WalletManager:
    def __init__(self):
        self.agentkit_key = config.AGENTKIT_API_KEY
        self.flow_client = None
        self.web3 = None
        self.initialize_clients()
        
    def initialize_clients(self):
        # Initialize Flow client
        self.flow_client = flow_client(
            host=config.FLOW_ACCESS_NODE.split(':')[0],
            port=int(config.FLOW_ACCESS_NODE.split(':')[1])
        )
        
        # Initialize Web3 for EVM compatibility
        self.web3 = Web3()
        
    async def execute_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if params.get('chain') == 'flow':
            return await self.execute_flow_transaction(params)
        else:
            return await self.execute_evm_transaction(params)
            
    async def execute_flow_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Implementation for Flow blockchain transactions
            tx = await self.flow_client.create_transaction(
                script=params.get('script'),
                args=params.get('args', []),
                proposer=config.FLOW_ACCOUNT_ADDRESS,
                payer=config.FLOW_ACCOUNT_ADDRESS,
                authorizers=[config.FLOW_ACCOUNT_ADDRESS]
            )
            
            # Sign and send transaction
            signed_tx = await self.flow_client.sign_transaction(
                tx,
                config.FLOW_PRIVATE_KEY
            )
            
            result = await self.flow_client.send_transaction(signed_tx)
            return {
                'status': 'success',
                'tx_hash': result.hash.hex(),
                'chain': 'flow'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'chain': 'flow'
            }
            
    async def execute_evm_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.agentkit_key}',
                    'Content-Type': 'application/json'
                }
                
                # Use AgentKit for EVM transactions
                async with session.post(
                    'https://api.agentkit.coinbase.com/v1/transactions',
                    json=params,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            'status': 'success',
                            'tx_hash': result.get('transaction_hash'),
                            'chain': params.get('chain', 'ethereum')
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': result.get('error'),
                            'chain': params.get('chain', 'ethereum')
                        }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'chain': params.get('chain', 'ethereum')
            }
            
    async def get_balance(self, address: str, token: str = None) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.agentkit_key}',
                    'Content-Type': 'application/json'
                }
                
                params = {'address': address}
                if token:
                    params['token'] = token
                    
                async with session.get(
                    'https://api.agentkit.coinbase.com/v1/balance',
                    params=params,
                    headers=headers
                ) as response:
                    return await response.json()
        except Exception as e:
            return {'error': str(e)}
