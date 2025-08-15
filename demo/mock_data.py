"""Mock CRM data used for offline demo without external APIs."""

MOCK_SEARCH_DATA = {
    "HubSpot": {
        "pricing": [
            {"title": "HubSpot Pricing", "content": "Free tier available. Starter: $20/month per user. Professional: $890/month for 5 users. Enterprise: $3600/month."},
            {"title": "HubSpot for Small Business", "content": "Best for companies under 50 employees. Free CRM includes contact management, deals, tasks."}
        ],
        "features": [
            {"title": "HubSpot Features", "content": "Email marketing, live chat, forms, email scheduling, meeting scheduling, quotes, conversational bots, reporting dashboard"},
            {"title": "HubSpot Automation", "content": "Workflow automation, lead scoring, email sequences, task automation"}
        ],
        "integrations": [
            {"title": "HubSpot Integrations", "content": "Native: Slack, Gmail, Outlook, Zoom, Shopify, WordPress. 1000+ apps via marketplace"}
        ],
        "limitations": [
            {"title": "HubSpot Limitations", "content": "Free tier limited to 1M contacts. No custom reporting in Starter. API rate limits: 100 calls/10 seconds"}
        ]
    },
    "Zoho": {
        "pricing": [
            {"title": "Zoho CRM Pricing", "content": "Free for 3 users. Standard: $14/user/month. Professional: $23/user/month. Enterprise: $40/user/month"},
            {"title": "Zoho B2B Features", "content": "Affordable for SMBs. Annual billing saves 20%. Includes Zia AI assistant"}
        ],
        "features": [
            {"title": "Zoho Features", "content": "Lead management, deal tracking, contact management, workflow automation, analytics, AI predictions"},
            {"title": "Zoho Advanced", "content": "Territory management, advanced CRM analytics, multiple pipelines, custom modules"}
        ],
        "integrations": [
            {"title": "Zoho Integrations", "content": "Native Zoho suite integration. Connects with Office 365, G Suite, Slack, Mailchimp. 300+ integrations"}
        ],
        "limitations": [
            {"title": "Zoho Limitations", "content": "Complex UI for beginners. Limited customization in lower tiers. No phone support in Standard plan"}
        ]
    },
    "Salesforce": {
        "pricing": [
            {"title": "Salesforce Pricing", "content": "Essentials: $25/user/month. Professional: $80/user/month. Enterprise: $165/user/month. Unlimited: $330/user/month"},
            {"title": "Salesforce for SMB", "content": "Minimum 10 users for Enterprise. Best ROI for 50+ user companies"}
        ],
        "features": [
            {"title": "Salesforce Features", "content": "Lead & opportunity management, account management, contact management, email integration, customizable reports & dashboards"},
            {"title": "Salesforce Platform", "content": "Process automation, approval processes, Einstein AI, mobile app, custom apps, API access"}
        ],
        "integrations": [
            {"title": "Salesforce AppExchange", "content": "4000+ apps available. Native: Slack (owned), Tableau, Mulesoft. Deep integration capabilities"}
        ],
        "limitations": [
            {"title": "Salesforce Limitations", "content": "Steep learning curve. Expensive for small teams. Requires admin resources. Storage limits per user"}
        ]
    }
}
