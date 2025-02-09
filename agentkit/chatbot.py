from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
import json
import os
from typing import Optional, List
from web3 import Web3
from eth_account import Account
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain_core.tools import Tool
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str

class ModeSwitch(BaseModel):
    mode: str

class BlockchainTools:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL", "https://sepolia.base.org")))
        self.account = None
        if os.getenv("PRIVATE_KEY"):
            self.account = Account.from_key(os.getenv("PRIVATE_KEY"))

    def get_balance(self, address: str = None) -> str:
        try:
            target = address or self.account.address
            balance = self.w3.eth.get_balance(target)
            eth_balance = self.w3.from_wei(balance, 'ether')
            return f"Balance for {target}: {eth_balance} ETH"
        except Exception as e:
            return f"Error getting balance: {str(e)}"

    def transfer_eth(self, to_address: str, amount: float) -> str:
        try:
            if not self.account:
                return "No private key configured"
            
            wei_amount = self.w3.to_wei(amount, 'ether')
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = {
                'nonce': nonce,
                'to': to_address,
                'value': wei_amount,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            return f"Transaction sent: {tx_hash.hex()}"
        except Exception as e:
            return f"Error sending transaction: {str(e)}"

    def sign_message(self, message: str) -> str:
        """Sign a message with the wallet"""
        try:
            if not self.account:
                return "No private key configured"
            signed = self.account.sign_message(text=message)
            return f"Message signed. Signature: {signed.signature.hex()}"
        except Exception as e:
            return f"Error signing message: {str(e)}"

class AgentManager:
    def __init__(self):
        self.agent = None
        self.mode = "chat"
        self.blockchain = BlockchainTools()
        self.messages: List[HumanMessage | AIMessage] = []

    def format_response(self, response: str) -> str:
        """Format response in markdown"""
        if "```" not in response:
            response = f"```markdown\n{response}\n```"
        return response

    def validate_environment(self):
        required_vars = [
            "GOOGLE_API_KEY",
            "RPC_URL"
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    async def initialize_agent(self):
        try:
            self.validate_environment()

            llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.7,
                convert_system_message_to_human=True
            )

            tools = [
                Tool(
                    name="get_balance",
                    func=self.blockchain.get_balance,
                    description="Get ETH balance for an address. Input should be an Ethereum address."
                ),
                Tool(
                    name="transfer_eth",
                    func=self.blockchain.transfer_eth,
                    description="Transfer ETH to an address. Input should be a tuple of (to_address, amount)."
                ),
                Tool(
                    name="sign_message",
                    func=self.blockchain.sign_message,
                    description="Sign a message with the wallet. Input should be the message to sign."
                )
            ]

            # Create agent prompt
            template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate(
                template=template,
                input_variables=["input", "agent_scratchpad"],
                partial_variables={
                    "tools": render_text_description(tools),
                    "tool_names": ", ".join([tool.name for tool in tools])
                }
            )

            agent = create_react_agent(llm, tools, prompt)
            self.agent = AgentExecutor(agent=agent, tools=tools, verbose=True)

            logger.info("Agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise e

    async def process_message(self, message: str) -> str:
        try:
            self.messages.append(HumanMessage(content=message))
            
            # Get agent response
            response = await self.agent.ainvoke({
                "input": message
            })
            
            # Format and store response
            formatted_response = self.format_response(response["output"])
            self.messages.append(AIMessage(content=formatted_response))
            
            return formatted_response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def run_autonomous_mode(self, interval: int = 10):
        try:
            thought = """Be creative and do something interesting with blockchain. 
            Choose an action that highlights your abilities."""

            response = await self.agent.ainvoke({
                "input": thought
            })
            return self.format_response(response["output"])
        except Exception as e:
            logger.error(f"Error in autonomous mode: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

agent_manager = AgentManager()

@app.on_event("startup")
async def startup_event():
    try:
        await agent_manager.initialize_agent()
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise e

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        response = await agent_manager.process_message(message.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/switch-mode")
async def switch_mode(mode_switch: ModeSwitch):
    try:
        if mode_switch.mode not in ["chat", "auto"]:
            raise ValueError("Invalid mode. Use 'chat' or 'auto'")
        agent_manager.mode = mode_switch.mode
        return {"status": f"Switched to {mode_switch.mode} mode"}
    except Exception as e:
        logger.error(f"Mode switch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    return {
        "mode": agent_manager.mode,
        "agent_initialized": agent_manager.agent is not None,
        "network": os.getenv("RPC_URL", "https://sepolia.base.org"),
        "wallet": agent_manager.blockchain.account.address if agent_manager.blockchain.account else None
    }

def main():
    try:
        logger.info("Starting server...")
        uvicorn.run(
            "chatbot:app",
            host="0.0.0.0",
            port=3001,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise e

if __name__ == "__main__":
    main()
