# Unipile — unified messaging API (synthetic stack playbook, fixture)

> Synthetic fixture reconstructing a stack playbook note. Public product facts only — no operator data. Part of the hermetic own-stack sweep test (`stack-paths.fixture.json`).

- Subscription: paid, flat plan (1-10 accounts connected).
- Providers supported (messaging): LinkedIn, WhatsApp, Telegram, Messenger, **Instagram**.
- Capabilities: hosted-auth **session delegation** (user connects their account via a hosted login URL); `GET chats/{chat_id}/messages` paginated DM history; real-time webhooks `message.new` / `message.update`; attachments proxied by the vendor.
- Risk class: credentialed **by delegation** — platform-ToS exposure applies; read-inbound is the lowest-risk operation class.
- Relevance triggers: unified messaging API, social inbox, DM retrieval, Instagram messages, WhatsApp bridge.
