# agentic-kyc-agents

Repository for AI agents for KYC process


# Agents

- news_collector_agent
- validate_name_address_agent
- validate_name_interpol_agent
- verify_account_docs_agent
- update_customer_data_agent
- prepare_confirmation_email_agent
- validate_email_agent
- perform_email_tasks_agent
- extract_client_information_agent

(Each agent folder contains a basic agent.json, agent.py and requirements.txt as templates.)
{
  "capabilities": {},
  "defaultInputModes": [
    "text/plain"
  ],
  "defaultOutputModes": [
    "text/plain"
  ],
  "description": "Validates customer name and address.",
  "name": "validate-name-address-agent",
  "skills": [
    {
      "id": "validate-name",
      "name": "Validate Name",
      "description": "Validates the customer's full name.",
      "tags": ["validation", "identity"]
    },
    {
      "id": "validate-address",
      "name": "Validate Address",
      "description": "Validates the customer's address format and existence.",
      "tags": ["validation", "address"]
    }
  ],
  "url": "http://localhost:9092",
  "version": "1.0.0"
}

