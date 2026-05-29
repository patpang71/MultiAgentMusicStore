# MultiAgent Music Store

A multi-agent AI music store assistant backed by the [Chinook](https://github.com/lerocha/chinook-database) sample database, deployed to AWS via an automated CodePipeline. Users interact through a **Gradio chat UI** hosted on Elastic Beanstalk; the agents are powered by **LangGraph** and **GPT-4o**.

---

## Architecture Overview

```
User (Browser)
     │
     ▼
┌─────────────────────────────┐
│  Gradio Chat UI             │  Elastic Beanstalk (Docker, t3.small)
│  app.py + LangGraph agents  │  Runs agent graph directly in-process
└────────────┬────────────────┘
             │  boto3 invoke
             ▼
┌─────────────────────────────┐
│  music-store-tools Lambda   │  Python 3.12, private VPC subnet
│  SQL query tools            │
└────────────┬────────────────┘
             │  pymysql
             ▼
┌─────────────────────────────┐
│  Amazon RDS MySQL 8.0       │  Chinook database, private subnet
└─────────────────────────────┘
```

### Agent graph (LangGraph)

```
START
  │
  ├─ verified=False ──► verify_info ──► supervisor
  │                                         │
  └─ verified=True ───► supervisor ──────────┤
                             │               │
                      route="music"   route="invoice"
                             │               │
                        music_agent    invoice_agent
                             │               │
                             └───────────────┘
                                     │
                               supervisor (reset)
                                     │
                                    END
```

**Nodes:**

| Node | Model | Role |
|---|---|---|
| `verify_info` | GPT-4o | Asks for Customer ID, email, or phone; looks up customer via tools; sets `verified=True` |
| `supervisor` | GPT-4o-mini | Greets customer by first name, classifies each request, routes to sub-agents |
| `music_agent` | GPT-4o | Answers catalog questions (songs, albums, artists, genres) using music tools |
| `invoice_agent` | GPT-4o | Answers billing/order questions scoped to the verified customer |

---

## Project Structure

```
MultiAgentMusicStore/
├── gradio_app/
│   ├── app.py                               # Gradio Blocks UI + LangGraph runner
│   ├── requirements.txt                     # gradio, boto3
│   └── Dockerfile.beanstalk                 # Docker image for EB deployment
│
├── lambdas/
│   ├── music_store_tools/                   # Tool Lambda — SQL query functions
│   │   ├── index.py                         # Entry point: routes event to tool function
│   │   ├── db_connection.py                 # Secrets Manager + pymysql connection helper
│   │   ├── get_albums_by_artist.py
│   │   ├── search_tracks_by_artist.py
│   │   ├── get_songs_by_genre.py            # Round-robin interleaved by artist
│   │   ├── search_songs_by_title.py
│   │   ├── get_track_details_by_id.py
│   │   ├── get_customer_by_id.py
│   │   ├── get_customer_by_email.py
│   │   ├── get_customer_by_phone.py         # Normalizes phone inline (no schema column needed)
│   │   ├── get_invoices_by_customer_sorted_by_date.py
│   │   ├── get_purchased_tracks_sorted_by_unit_price.py
│   │   ├── get_detail_line_item_for_invoice.py
│   │   ├── requirements.txt                 # pymysql
│   │   └── tests/                           # Unit tests (mocked DB)
│   │
│   └── music_store_agents/                  # Agent Lambda (also runs inside EB container)
│       ├── index.py                         # Lambda entry point
│       ├── graph.py                         # LangGraph StateGraph definition
│       ├── state.py                         # AgentState TypedDict
│       ├── secrets_helper.py                # Reads OpenAI key from Secrets Manager
│       ├── preferences_helper.py            # DynamoDB read/write for customer preferences
│       ├── nodes/
│       │   ├── verify_info_node.py
│       │   ├── supervisor_node.py
│       │   ├── music_agent_node.py
│       │   └── invoice_agent_node.py
│       ├── tools/
│       │   ├── customer_lookup_tools.py     # LangChain tools wrapping the tools Lambda
│       │   ├── music_catalog_tools.py
│       │   └── invoice_tools.py
│       ├── requirements.txt                 # langgraph, langchain, langchain-openai
│       └── tests/                           # Unit tests
│
├── cdk/                                     # AWS CDK infrastructure (TypeScript)
│   ├── bin/music-store-app.ts               # CDK app entry point
│   ├── lib/
│   │   ├── music-store-stack.ts             # Root stack
│   │   └── constructs/
│   │       ├── database.ts                  # RDS MySQL + Secrets Manager
│   │       ├── music-store-tools-lambda.ts  # music-store-tools Lambda + Lambda Layer
│   │       ├── music-store-agents-lambda.ts # music-store-agents Lambda + DynamoDB table
│   │       ├── gradio-beanstalk.ts          # Elastic Beanstalk app + S3 bundle bucket
│   │       └── pipeline.ts                 # CodePipeline (5 stages)
│   └── buildspecs/
│       ├── test.yml                         # Run pytest
│       ├── db-init.yml                      # Seed Chinook DB once (SSM-guarded)
│       ├── db-health.yml                    # Verify all tables exist and have rows
│       └── deploy.yml                       # CDK deploy + assemble & push EB bundle
│
├── dbscripts/
│   ├── Chinook_MySql_AutoIncrementPKs.sql   # Chinook schema (AUTO_INCREMENT PKs)
│   └── add_phone_normalized_column.sql      # Optional migration (not used — see phone note)
│
└── README.md
```

---

## Agent nodes in detail

### verify_info
- Greets the user and asks for one of: Customer ID, email, or phone number
- Calls the appropriate `music-store-tools` lookup function via the `customer_lookup_tools` wrapper
- On success: sets `verified=True` and stores `customer_info` (firstName, lastName, email, etc.) in state
- On failure: apologises and asks the user to try a different identifier
- Phone numbers are normalised (spaces, parentheses, dashes stripped) and matched inline in SQL

### supervisor
- Uses GPT-4o-mini with structured output (`SupervisorDecision`)
- Greets the verified customer by first name on the first turn
- Classifies each request and routes to `music_agent` or `invoice_agent`
- Detects explicit music preferences ("I love jazz") and persists them to DynamoDB
- After a sub-agent answers, resets routing silently (sub-agents include their own closing prompt)

### music_agent
- Tool-calling loop: calls music catalog tools until no more tool calls are needed
- Answers questions about songs, albums, artists, and genres
- Uses round-robin interleaved results for genre listings (no single artist dominates)
- Ends each response with a prompt for further catalog questions

### invoice_agent
- Scoped to the verified customer's ID — cannot access other customers' data
- Answers questions about invoices, orders, and purchase history
- Ends each response with a prompt for further order questions

---

## Database

**Amazon RDS MySQL 8.0** running the Chinook music store schema.

### Tables
`Album`, `Artist`, `Customer`, `Employee`, `Genre`, `Invoice`, `InvoiceLine`, `MediaType`, `Playlist`, `PlaylistTrack`, `Track`

### One-time initialization
The DB Init pipeline stage runs `Chinook_MySql_AutoIncrementPKs.sql` exactly once, guarded by an SSM parameter:

- **`/music-store/db-initialized` not set** → seeds the database, sets the parameter to `"true"`
- **`/music-store/db-initialized = "true"`** → skips immediately

To force a re-seed:
```bash
aws ssm delete-parameter --name "/music-store/db-initialized"
```

---

## Tool Lambda: music-store-tools

Invoked by the agent nodes via boto3. Accepts events of the form:

```json
{ "tool": "get_albums_by_artist", "input": "AC/DC" }
```

### Customer lookup tools

| Tool | Input | Description |
|---|---|---|
| `get_customer_by_id` | Customer ID (integer) | Looks up customer by numeric ID |
| `get_customer_by_email` | Email address | Looks up customer by email |
| `get_customer_by_phone` | Phone number (any format) | Normalises and matches against stored phone |

### Music catalog tools

| Tool | Input | Description |
|---|---|---|
| `get_albums_by_artist` | Artist name (partial) | Returns all albums grouped by matching artists |
| `search_tracks_by_artist` | Artist name (exact) | Returns up to 20 tracks for the artist |
| `get_songs_by_genre` | Genre name (exact) | Returns tracks for the genre, interleaved by artist |
| `search_songs_by_title` | Track title (partial) | Returns up to 10 matching tracks |
| `get_track_details_by_id` | Track ID (integer) | Full details for one track |

### Invoice tools

| Tool | Input | Description |
|---|---|---|
| `get_invoices_by_customer_sorted_by_date` | Customer ID | All invoices for a customer, newest first |
| `get_purchased_tracks_sorted_by_unit_price` | None | Store-wide track pricing list |
| `get_detail_line_item_for_invoice` | Invoice ID | Invoice header + all line items |

---

## Infrastructure (AWS CDK)

### Resources created

| Resource | Details |
|---|---|
| **VPC** | 2 AZs, public + private subnets, 1 NAT Gateway |
| **RDS MySQL** | `db.t3.micro`, MySQL 8.0, private subnet, credentials in Secrets Manager |
| **Lambda: music-store-tools** | Python 3.12, 256 MB, 30 s timeout, private VPC subnet, Lambda Layer for pymysql |
| **Lambda: music-store-agents** | Python 3.12, Lambda Layer for LangChain/LangGraph dependencies |
| **DynamoDB** | `music-store-customer-preferences` — per-customer genre/artist preference store |
| **Elastic Beanstalk** | `music-store-gradio` app + `music-store-gradio-env`, Docker platform, `t3.small`, single instance |
| **S3 bucket** | Stores EB source bundles uploaded by the pipeline |
| **CodePipeline** | V2 pipeline — 5 stages (Source → Test → DB Init → DB Health → Deploy) |
| **CodeConnections** | GitHub connection for pipeline source |
| **SSM Parameter** | `/music-store/db-initialized` |
| **Secrets Manager** | `/music-store/db-credentials` — RDS credentials + OpenAI API key |

### Pipeline stages

```
GitHub ──► Source ──► Test ──► DB_Init ──► DB_Health_Check ──► Deploy
```

| Stage | What it does |
|---|---|
| **Source** | Pulls from GitHub on every push to `main` |
| **Test** | Runs `pytest` across both Lambda test suites |
| **DB_Init** | Seeds Chinook DB once (SSM-guarded no-op on subsequent runs) |
| **DB_Health_Check** | Verifies all tables exist and contain rows before deploying |
| **Deploy** | Installs Lambda layer deps → `cdk deploy` → assembles & uploads EB bundle → triggers EB deployment |

---

## Secrets Manager secret structure

The secret at `/music-store/db-credentials` must contain:

```json
{
  "host": "...",
  "username": "...",
  "password": "...",
  "openai_api_key": "sk-..."
}
```

The `openai_api_key` field is read at runtime by the agent nodes via `secrets_helper.py`.

---

## Logging

| Component | Log destination |
|---|---|
| Gradio app + agent nodes (in EB container) | EB instance logs → EB Console → Logs tab |
| `music-store-tools` Lambda | CloudWatch → `/aws/lambda/music-store-tools` |
| `music-store-agents` Lambda | CloudWatch → `/aws/lambda/music-store-agents` |

All components use Python's `logging` module at `INFO` level. The root logger level is set in each Lambda's `index.py` to override the Lambda runtime's default `WARNING` level.

---

## Prerequisites

1. [Node.js](https://nodejs.org/) 18+
2. [AWS CLI](https://aws.amazon.com/cli/) configured (`aws configure`)
3. A **GitHub CodeConnections** connection created in the AWS Console:
   - Go to **AWS Console → CodePipeline → Settings → Connections**
   - Create a connection to GitHub and authorise it
   - Copy the connection ARN (format: `arn:aws:codeconnections:REGION:ACCOUNT:connection/ID`)

---

## Deployment

### 1. Bootstrap CDK

```bash
cd cdk
npm install
npx cdk bootstrap
```

### 2. Deploy the stack

```bash
npx cdk deploy MusicStoreStack \
  -c githubOwner=YOUR_GITHUB_USERNAME \
  -c githubRepo=MultiAgentMusicStore \
  -c githubBranch=main \
  -c codeStarConnectionArn=arn:aws:codeconnections:REGION:ACCOUNT:connection/YOUR_ID
```

CDK outputs after deployment:

| Output | Description |
|---|---|
| `DbEndpoint` | RDS hostname |
| `DbSecretArn` | Secrets Manager ARN (add `openai_api_key` here) |
| `MusicStoreToolsLambdaArn` | ARN of the tools Lambda |
| `MusicStoreAgentsLambdaArn` | ARN of the agents Lambda |
| `GradioServiceUrl` | URL of the Gradio chat UI |
| `GradioBundleBucketName` | S3 bucket used by the pipeline for EB bundles |
| `PipelineConsoleUrl` | Link to the pipeline in the AWS Console |

### 3. Add the OpenAI API key to Secrets Manager

The DB secret is auto-generated by CDK. After deployment, add the OpenAI key:

```bash
# Retrieve current secret value
aws secretsmanager get-secret-value --secret-id <DbSecretArn> --query SecretString --output text

# Update with openai_api_key added
aws secretsmanager put-secret-value \
  --secret-id <DbSecretArn> \
  --secret-string '{"host":"...","username":"...","password":"...","openai_api_key":"sk-..."}'
```

### 4. Activate the CodeConnections connection

After `cdk deploy`, go to **AWS Console → Developer Tools → Connections**, find your connection, and click **Update pending connection** to authorise it via GitHub.

### 5. Trigger the pipeline

Push a commit to `main`. The pipeline runs automatically. On the first push:
- DB Init seeds the Chinook database
- Deploy builds the Lambda layers, runs `cdk deploy`, and deploys the Gradio app to Elastic Beanstalk

The Gradio UI becomes available at `GradioServiceUrl` after the EB deployment completes (~5 minutes after the Deploy stage finishes).

---

## Running tests locally

```bash
# music-store-tools tests
cd lambdas/music_store_tools
python3 -m venv .venv && source .venv/bin/activate
pip install pymysql boto3 pytest
pytest tests/ -v

# music-store-agents tests
cd lambdas/music_store_agents
python3 -m venv .venv && source .venv/bin/activate
pip install langgraph langchain langchain-openai boto3 pytest
pytest tests/ -v
```

All tests mock the database and AWS services — no live connections required.

---

## Useful CDK commands

```bash
# Preview changes without deploying
npx cdk diff MusicStoreStack -c githubOwner=... -c githubRepo=... -c githubBranch=... -c codeStarConnectionArn=...

# Synthesize CloudFormation template
npx cdk synth

# Destroy all resources
npx cdk destroy MusicStoreStack
```
