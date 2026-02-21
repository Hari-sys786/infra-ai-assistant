# src/rag_bot/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root: src/rag_bot/config.py -> src -> PROJECT_ROOT
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

# Data directories
DATA_ROOT = PROJECT_ROOT / "data" / "vendor"
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma_db"
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

# Ensure directories exist
DATA_ROOT.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# LLM config — supports: groq, anthropic, gemini, openai
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Legacy aliases
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Embedding model
EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ChromaDB collection name
COLLECTION_NAME = "infra_docs"

# Vendor documents catalog
VENDOR_DOCUMENTS = {
    "Dell": [
        {"name": "PowerEdge_Rack_Servers_Quick_Reference_Guide.pdf"},
        {"name": "PowerEdge_R660xs_Technical_Guide.pdf"},
        {"name": "PowerEdge_R740_R740xd_Technical_Guide.pdf"},
        {"name": "OpenManage_Server_Administrator_v9.5_Users_Guide.pdf"},
        {"name": "System_Configuration_Profiles_Reference_Guide.pdf"},
    ],
    "IBM": [
        {"name": "Power_Systems_Virtual_Server_Guide_for_IBM_i.pdf"},
        {"name": "HTTP_Server_v6_Users_Guide.pdf"},
    ],
    "Cisco": [
        {"name": "Enterprise_Campus_Infrastructure_Design_Guide.pdf"},
        {"name": "IT_Wireless_LAN_Design_Guide.pdf"},
        {"name": "IT_IP_Addressing_Best_Practices.pdf"},
        {"name": "Network_Registrar_7.2_User_Guide.pdf"},
    ],
    "Juniper": [
        {"name": "Junos_Overview.pdf"},
        {"name": "Junos_OS_Network_Management_Administration_Guide.pdf"},
    ],
    "Fortinet": [
        {"name": "FortiOS_5.6_Firewall_Handbook.pdf"},
        {"name": "FortiWeb_6.0.7_Administration_Guide.pdf"},
        {"name": "FortiGate-200_Administration_Guide.pdf"},
    ],
    "EUC": [
        {"name": "Dell_EUC_Overview.html"},
        {"name": "Nutanix_EUC_Solutions.html"},
        {"name": "EUC_Score_Toolset_Documentation.html"},
    ],
}
