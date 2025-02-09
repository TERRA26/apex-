from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
WALLET_DATA_FILE = "wallet_data.txt"

# Models for request/response
class ChatMessage(BaseModel):
    message: str

class ModeSwitch(BaseModel):
    mode: str

class AgentResponse(BaseModel):
    response: str

class ModeResponse(BaseModel):
    status: str

# Global variables for agent state
agent = None
config = None

def initialize_agent():
    """Initialize the agent with required configurations"""
    global agent, config
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Read existing wallet data if available
        wallet_data = None
        if os.path.exists(WALLET_DATA_FILE):
            try:
                with open(WALLET_DATA_FILE, 'r') as f:
                    wallet_data = f.read()
            except Exception as e:
                print(f"Error reading wallet data: {e}")

        # Store the agent and config
        agent = llm
        config = {
            "wallet_data": wallet_data,
            "mode": "chat"
        }

        print("Agent initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the agent when the server starts"""
    initialize_agent()

@app.post("/chat", response_model=AgentResponse)
async def chat(message: ChatMessage):
    """Handle chat messages"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Process message with the agent
        response = agent.invoke([HumanMessage(content=message.message)])
        return AgentResponse(response=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mode", response_model=ModeResponse)
async def switch_mode(mode_switch: ModeSwitch):
    """Handle mode switching between chat and autonomous"""
    if not config:
        raise HTTPException(status_code=500, detail="Config not initialized")

    try:
        new_mode = mode_switch.mode
        if new_mode not in ["chat", "auto"]:
            raise HTTPException(status_code=400, detail="Invalid mode")

        config["mode"] = new_mode
        status_message = f"{new_mode.capitalize()} mode activated"
        
        # If switching to auto mode, you might want to start autonomous processing here
        if new_mode == "auto":
            # Add autonomous mode logic here
            pass

        return ModeResponse(status=status_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get the current status of the agent"""
    if not config:
        raise HTTPException(status_code=500, detail="Config not initialized")
    
    return {
        "mode": config["mode"],
        "initialized": agent is not None
    }

def main():
    """Main entry point for the server"""
    uvicorn.run(
        "chatbot:app",
        host="0.0.0.0",
        port=3001,
        reload=True
    )

if __name__ == "__main__":
    main()
