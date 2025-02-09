import express from 'express';
import cors from 'cors';
import {
    AgentKit,
    CdpWalletProvider,
    wethActionProvider,
    walletActionProvider,
    erc20ActionProvider,
    cdpApiActionProvider,
    cdpWalletActionProvider,
    pythActionProvider,
} from "@coinbase/agentkit";
import { getLangChainTools } from "@coinbase/agentkit-langchain";
import { HumanMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";
import * as dotenv from "dotenv";
import * as fs from "fs";

dotenv.config();

const app = express();
const port = 3001;

// Enable CORS for frontend
app.use(cors());
app.use(express.json());

// Configure CDP Wallet Provider
const WALLET_DATA_FILE = "wallet_data.txt";

// Initialize agent and config
let agent: any;
let config: any;

async function initializeAgent() {
    try {
        // Initialize LLM
        const llm = new ChatOpenAI({
            model: "gpt-4o-mini",
        });

        let walletDataStr: string | null = null;

        // Read existing wallet data if available
        if (fs.existsSync(WALLET_DATA_FILE)) {
            try {
                walletDataStr = fs.readFileSync(WALLET_DATA_FILE, "utf8");
            } catch (error) {
                console.error("Error reading wallet data:", error);
            }
        }

        // Configure CDP Wallet Provider
        const cdpWalletProvider = new CdpWalletProvider({
            walletData: walletDataStr,
            onWalletDataChange: (newWalletData: string) => {
                fs.writeFileSync(WALLET_DATA_FILE, newWalletData);
            },
        });

        // Initialize AgentKit
        const agentKit = new AgentKit({
            llm,
            walletProvider: cdpWalletProvider,
            actionProviders: [
                wethActionProvider,
                walletActionProvider,
                erc20ActionProvider,
                cdpApiActionProvider,
                cdpWalletActionProvider,
                pythActionProvider,
            ],
        });

        // Get LangChain tools
        const tools = getLangChainTools(agentKit);

        return { agent: tools, config: agentKit };
    } catch (error) {
        console.error("Error initializing agent:", error);
        throw error;
    }
}

// Initialize agent on startup
(async () => {
    try {
        const result = await initializeAgent();
        agent = result.agent;
        config = result.config;
        console.log("Agent initialized successfully");
    } catch (error) {
        console.error("Failed to initialize agent:", error);
    }
})();

// Chat endpoint
app.post('/chat', async (req, res) => {
    try {
        if (!agent || !config) {
            throw new Error("Agent not initialized");
        }

        const { message } = req.body;
        if (!message) {
            return res.status(400).json({ error: "Message is required" });
        }

        const response = await agent.invoke([new HumanMessage(message)]);
        res.json({ response: response.content });
    } catch (error) {
        console.error("Error processing chat:", error);
        res.status(500).json({ error: "Failed to process chat message" });
    }
});

// Mode switch endpoint
app.post('/mode', async (req, res) => {
    const { mode } = req.body;
    if (mode === 'auto') {
        // Implementation for auto mode
        res.json({ status: 'Auto mode activated' });
    } else {
        // Implementation for chat mode
        res.json({ status: 'Chat mode activated' });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
