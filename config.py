import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AUTONOME_USERNAME = os.getenv("AUTONOME_USERNAME")
    AUTONOME_PASSWORD = os.getenv("AUTONOME_PASSWORD")
    AUTONOME_ENDPOINT = os.getenv("AUTONOME_ENDPOINT")
    AGENTKIT_API_KEY = os.getenv("AGENTKIT_API_KEY")
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    FLOW_ACCESS_NODE = os.getenv("FLOW_ACCESS_NODE")
    FLOW_PRIVATE_KEY = os.getenv("FLOW_PRIVATE_KEY")
    FLOW_ACCOUNT_ADDRESS = os.getenv("FLOW_ACCOUNT_ADDRESS")

    @classmethod
    def validate(cls):
        missing = []
        for attr in dir(cls):
            if not attr.startswith("__") and getattr(cls, attr) is None:
                missing.append(attr)
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

config = Config()
