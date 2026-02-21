# src/rag_bot/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

# Root data directory (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "vendor"
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma_db"
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

# Ensure directories exist
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Anthropic config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Embedding model
EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ChromaDB collection name
COLLECTION_NAME = "infra_docs"

# Vendor documents catalog
VENDOR_DOCUMENTS = {
    "Dell": [
        {
            "name": "PowerEdge_Rack_Servers_Quick_Reference_Guide.pdf",
            "url": "https://i.dell.com/sites/csdocuments/Product_Docs/en/Dell-EMC-PowerEdge-Rack-Servers-Quick-Reference-Guide.pdf"
        },
        {
            "name": "PowerEdge_R660xs_Technical_Guide.pdf",
            "url": "https://www.delltechnologies.com/asset/en-us/products/servers/technical-support/poweredge-r660xs-technical-guide.pdf"
        },
        {
            "name": "PowerEdge_R740_R740xd_Technical_Guide.pdf",
            "url": "https://i.dell.com/sites/csdocuments/shared-content_data-sheets_documents/en/aa/poweredge_r740_r740xd_technical_guide.pdf"
        },
        {
            "name": "OpenManage_Server_Administrator_v9.5_Users_Guide.pdf",
            "url": "https://dl.dell.com/topicspdf/openmanage-server-administrator-v95_users-guide_en-us.pdf"
        },
        {
            "name": "System_Configuration_Profiles_Reference_Guide.pdf",
            "url": "https://dl.dell.com/manuals/common/dellemc-server-config-profile-refguide.pdf"
        },
    ],
    "IBM": [
        {
            "name": "Power_Systems_Virtual_Server_Guide_for_IBM_i.pdf",
            "url": "https://www.redbooks.ibm.com/redbooks/pdfs/sg248513.pdf"
        },
        {
            "name": "SPSS_Statistics_Server_Administrators_Guide.pdf",
            "url": "https://www.ibm.com/docs/SSLVMB_28.0.0/pdf/IBM_SPSS_Statistics_Server_Administrator_Guide.pdf"
        },
        {
            "name": "HTTP_Server_v6_Users_Guide.pdf",
            "url": "https://public.dhe.ibm.com/software/webserver/appserv/library/v60/ihs_60.pdf"
        },
        {
            "name": "Storage_Protect_PDF_Documentation_Index.pdf",
            "url": "https://www.ibm.com/docs/en/storage-protect/8.1.25?topic=pdf-files"
        },
    ],
    "Cisco": [
        {
            "name": "Enterprise_Campus_Infrastructure_Design_Guide.pdf",
            "url": "https://www.cisco.com/c/dam/global/shared/assets/pdf/cisco_enterprise_campus_infrastructure_design_guide.pdf"
        },
        {
            "name": "IT_Wireless_LAN_Design_Guide.pdf",
            "url": "https://www.cisco.com/c/dam/en_us/about/ciscoitatwork/downloads/ciscoitatwork/pdf/Cisco_IT_Wireless_LAN_Design_Guide.pdf"
        },
        {
            "name": "IT_IP_Addressing_Best_Practices.pdf",
            "url": "https://www.cisco.com/c/dam/en_us/about/ciscoitatwork/downloads/ciscoitatwork/pdf/Cisco_IT_IP_Addressing_Best_Practices.pdf"
        },
        {
            "name": "Network_Registrar_7.2_User_Guide.pdf",
            "url": "https://www.cisco.com/c/en/us/td/docs/net_mgmt/network_registrar/7-2/user/guide/cnr72book.pdf"
        },
    ],
    "Juniper": [
        {
            "name": "Junos_Overview.pdf",
            "url": "https://www.juniper.net/documentation/us/en/software/junos/junos-overview/junos-overview.pdf"
        },
        {
            "name": "Junos_OS_Network_Management_Administration_Guide.pdf",
            "url": "https://archive.org/download/junos-srxsme/JunOS%20SRX%20Documentation%20Set/network-management.pdf"
        },
        {
            "name": "Junos_Space_Network_Management_Security_Policy.pdf",
            "url": "https://csrc.nist.gov/CSRC/media/projects/cryptographic-module-validation-program/documents/security-policies/140sp3779.pdf"
        },
    ],
    "Fortinet": [
        {
            "name": "FortiOS_5.6_Firewall_Handbook.pdf",
            "url": "https://fortinetweb.s3.amazonaws.com/docs.fortinet.com/v2/attachments/b94274f8-1a11-11e9-9685-f8bc1258b856/FortiOS-5.6-Firewall.pdf"
        },
        {
            "name": "FortiWeb_6.0.7_Administration_Guide.pdf",
            "url": "https://fortinetweb.s3.amazonaws.com/docs.fortinet.com/v2/attachments/14ac8f15-2226-11ea-9384-00505692583a/fortiweb-v6.0.7-admin-guide.pdf"
        },
        {
            "name": "FortiGate-200_Administration_Guide.pdf",
            "url": "https://www.andovercg.com/datasheets/fortigate-fortinet-200.pdf"
        },
        {
            "name": "FortiGate_Next-Gen_Firewall_Common_Criteria_Handbook.pdf",
            "url": "https://www.commoncriteriaportal.org/files/epfiles/Fortinet%20FortiGate_EAL4_ST_V1.5.pdf(320893)_TMP.pdf"
        },
    ],
    "EUC": [
        {
            "name": "Dell_EUC_Overview.html",
            "url": "https://www.dell.com/en-us/lp/dt/end-user-computing"
        },
        {
            "name": "Nutanix_EUC_Solutions.html",
            "url": "https://www.nutanix.com/solutions/end-user-computing"
        },
        {
            "name": "EUC_Score_Toolset_Documentation.html",
            "url": "https://eucscore.com/docs/tools.html"
        },
        {
            "name": "Apparity_EUC_Governance_Docs_Repository.html",
            "url": "https://apparity.com/euc-resources/spreadsheet-euc-documents/"
        },
    ]
}
