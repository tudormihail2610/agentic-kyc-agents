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

# MCPs

```bash

npx @modelcontextprotocol/inspector
```

```bash
adk deploy cloud_run --project versatile-hub-351115 --region us-central1 --service_name client-analysis-agent --a2a client_analysis_agent
```


```bash
adk deploy cloud_run --project versatile-hub-351115 --region us-central1 --service_name client-approval-agent --a2a client_approval_agent
```

```bash
adk deploy cloud_run --project versatile-hub-351115 --region us-central1 --service_name client-comms-agent --a2a client_comms_agent
```

```bash
adk deploy cloud_run --project versatile-hub-351115 --region us-central1 --service_name comms-approval-agent --a2a comms_approval_agent
```

```bash
adk deploy cloud_run --project versatile-hub-351115 --region us-central1 --service_name interpol-guard-agent --a2a interpol_guard_agent
```