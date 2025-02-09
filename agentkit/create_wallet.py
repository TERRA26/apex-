from eth_account import Account
import secrets

def create_wallet():
    # Generate a random private key
    private_key = secrets.token_hex(32)
    
    # Create an account from the private key
    account = Account.from_key(private_key)
    
    print("\n=== New Ethereum Wallet Created ===")
    print(f"Address: {account.address}")
    print(f"Private Key: {private_key}")
    print("\nIMPORTANT:")
    print("1. Save your private key securely - you'll need it for the .env file")
    print("2. Never share your private key with anyone")
    print("3. This is a test wallet - only use it for development")
    print("4. You'll need some test ETH from a Sepolia faucet")
    print("\nTo get test ETH:")
    print("1. Go to https://sepoliafaucet.com/")
    print("2. Connect with Alchemy or another provider")
    print("3. Enter your wallet address to receive test ETH")

if __name__ == "__main__":
    create_wallet()
