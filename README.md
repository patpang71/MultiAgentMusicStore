# MultiAgent Music Store

A serverless music store application backed by the [Chinook](https://github.com/lerocha/chinook-database) sample database, deployed to AWS Lambda via an automated CodePipeline.

---

## Project Structure

```
MultiAgentMusicStore/
├── dbscripts/
│   ├── Chinook_MySql.sql                    # Original Chinook schema (explicit PKs)
│   └── Chinook_MySql_AutoIncrementPKs.sql   # Chinook schema with AUTO_INCREMENT PKs
├── lambdas/
│   └── music_store_tools/                   # MCP tool Lambda (Python 3.11)
│       ├── index.py                         # Lambda entry point — routes by tool name
│       ├── db_connection.py                 # Shared Secrets Manager + pymysql helper
│       ├── get_albums_by_artist.py
│       ├── search_tracks_by_artist.py
│       ├── get_songs_by_genre.py
│       ├── search_songs_by_title.py
│       ├── get_track_details_by_id.py
│       ├── get_invoices_by_customer_sorted_by_date.py
│       ├── get_purchased_tracks_sorted_by_unit_price.py
│       ├── get_detail_line_item_for_invoice.py
│       ├── requirements.txt                 # Python dependencies (pymysql)
│       └── tests/                           # Unit tests (mocked DB, no live connection needed)
│           ├── test_index.py
│           ├── test_get_albums_by_artist.py
│           ├── test_search_tracks_by_artist.py
│           ├── test_get_songs_by_genre.py
│           ├── test_search_songs_by_title.py
│           ├── test_get_track_details_by_id.py
│           ├── test_get_invoices_by_customer_sorted_by_date.py
│           ├── test_get_purchased_tracks_sorted_by_unit_price.py
│           └── test_get_detail_line_item_for_invoice.py
├── cdk/                                      # AWS CDK infrastructure (TypeScript)
│   ├── bin/
│   │   └── music-store-app.ts               # CDK app entry point
│   ├── lib/
│   │   ├── constructs/
│   │   │   ├── database.ts                  # RDS MySQL construct
│   │   │   ├── music-store-tools-lambda.ts  # music-store-tools Lambda construct
│   │   │   └── pipeline.ts                  # CodePipeline construct
│   │   └── music-store-stack.ts             # Root stack (VPC + DB + Lambda + Pipeline)
│   ├── buildspecs/
│   │   ├── test.yml                         # Test stage buildspec
│   │   ├── db-init.yml                      # One-time DB seed buildspec
│   │   ├── db-health.yml                    # DB health check buildspec
│   │   └── deploy.yml                       # Deploy buildspec (CDK)
│   ├── cdk.json                             # CDK config and context values
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

---

## Database

The project uses the **Chinook** music store sample database on **Amazon RDS MySQL 8.0**.

| File | Description |
|---|---|
| `Chinook_MySql.sql` | Original schema — PKs are `INT NOT NULL` with values inserted explicitly |
| `Chinook_MySql_AutoIncrementPKs.sql` | Modified schema — PKs are `INT NOT NULL AUTO_INCREMENT`; INSERT statements omit the PK column and let MySQL assign IDs |

The pipeline uses `Chinook_MySql_AutoIncrementPKs.sql` and creates a database named `Chinook_AutoIncrement`.

### Tables

`Album`, `Artist`, `Customer`, `Employee`, `Genre`, `Invoice`, `InvoiceLine`, `MediaType`, `Playlist`, `PlaylistTrack`, `Track`

---

## Lambda: music-store-tools

The `music-store-tools` Lambda exposes eight database query tools for use by an AI agent via MCP.

### Invocation format

Send an event with a `tool` name and `input` value:

```json
{ "tool": "get_albums_by_artist", "input": "AC/DC" }
```

Tools that require no input (e.g. `get_purchased_tracks_sorted_by_unit_price`) can omit the `input` field.

### Music catalogue tools

| Tool | Input | Description |
|---|---|---|
| `get_albums_by_artist` | Artist name (partial match) | Returns all albums grouped by matching artists |
| `search_tracks_by_artist` | Artist name (exact match) | Returns up to 20 tracks for the artist |
| `get_songs_by_genre` | Genre name (exact match) | Returns all tracks for the genre |
| `search_songs_by_title` | Track title (partial match) | Returns up to 10 matching tracks |
| `get_track_details_by_id` | Track ID (integer) | Returns full details for a single track |

### Invoice tools

| Tool | Input | Description |
|---|---|---|
| `get_invoices_by_customer_sorted_by_date` | Customer ID (integer) | Returns all invoices for a customer, newest first |
| `get_purchased_tracks_sorted_by_unit_price` | None | Returns all purchased tracks ordered by unit price descending |
| `get_detail_line_item_for_invoice` | Invoice ID (integer) | Returns invoice header plus all line items for a specific invoice |

### Response format

Every tool returns JSON. On success it contains the results; on not-found or error:

```json
{ "message": "Cannot find any invoices for customer 99" }
{ "message": "Error <error details>" }
```

### Running unit tests locally

```bash
cd lambdas/music_store_tools
python3 -m venv .venv && source .venv/bin/activate
pip install pymysql boto3 pytest
pytest tests/ -v
```

All 24 tests mock the database — no live RDS connection required.

---

## Infrastructure (AWS CDK)

All AWS resources are defined as TypeScript CDK code under `cdk/`.

### Resources created

| Resource | Details |
|---|---|
| **VPC** | 2 AZs, public + private subnets, 1 NAT Gateway |
| **RDS MySQL** | `db.t3.micro`, MySQL 8.0, private subnet, credentials in Secrets Manager |
| **Lambda** | `music-store-tools` — Python 3.11, 256 MB, 30 s timeout, private subnet |
| **CodePipeline** | V2 pipeline — 5 stages (Source → Test → DB Init → DB Health → Deploy) |
| **CodeBuild projects** | One per stage: `music-store-test`, `music-store-db-init`, `music-store-db-health`, `music-store-deploy` |
| **SSM Parameter** | `/music-store/db-initialized` — tracks whether the DB seed has run |
| **Secrets Manager** | `/music-store/db-credentials` — auto-generated RDS admin credentials |

### Pipeline stages

```
GitHub ──► Source ──► Test ──► DB_Init ──► DB_Health_Check ──► Deploy
```

| Stage | Tool | What it does |
|---|---|---|
| **Source** | CodeStar Connection | Pulls source from GitHub on every push to `main` |
| **Test** | CodeBuild | Runs `pytest tests/` |
| **DB_Init** | CodeBuild (in VPC) | Seeds the Chinook database **once**; subsequent runs are a no-op |
| **DB_Health_Check** | CodeBuild (in VPC) | Verifies all tables exist and contain rows before deploying |
| **Deploy** | CodeBuild | Runs `cdk deploy` — redeploys the full stack including the Lambda on every run |

### Lambda redeployment behaviour

Unlike the database (which is seeded only once), the `music-store-tools` Lambda is **redeployed on every pipeline run**. The Deploy stage:

1. Pre-installs Python dependencies (`pymysql`) into the Lambda source directory
2. Runs `cdk deploy` — CDK detects any code changes, zips the directory, uploads the asset, and updates the Lambda function

No manual action is needed; pushing a code change to `main` is enough to update the live Lambda.

### One-time database initialization

The DB Init stage is idempotent. Before running the SQL script it checks for an SSM Parameter at `/music-store/db-initialized`:

- **Not found** → runs `Chinook_MySql_AutoIncrementPKs.sql` against RDS, then sets the parameter to `"true"`.
- **Found (`"true"`)** → skips immediately.

To force a re-seed, delete the flag:

```bash
aws ssm delete-parameter --name "/music-store/db-initialized"
```

---

## Prerequisites

1. [Node.js](https://nodejs.org/) 18+
2. [AWS CLI](https://aws.amazon.com/cli/) configured with credentials (`aws configure`)
3. A **GitHub CodeStar Connection** created in the AWS Console:
   - Go to **AWS Console → CodePipeline → Settings → Connections**
   - Create a connection to GitHub and authorise it
   - Copy the connection ARN

---

## Deployment

### 1. Configure context values

Edit [cdk/cdk.json](cdk/cdk.json) and fill in your values:

```json
{
  "context": {
    "githubOwner": "YOUR_GITHUB_USERNAME_OR_ORG",
    "githubRepo": "MultiAgentMusicStore",
    "githubBranch": "main",
    "codeStarConnectionArn": "arn:aws:codeconnections:REGION:ACCOUNT_ID:connection/YOUR_CONNECTION_ID"
  }
}
```

### 2. Install dependencies and bootstrap

```bash
cd cdk
npm install
npx cdk bootstrap
```

### 3. Deploy

```bash
npx cdk deploy
```

CDK outputs after deployment:

- `DbEndpoint` — the RDS hostname
- `DbSecretArn` — Secrets Manager ARN for the admin credentials
- `MusicStoreToolsLambdaArn` — ARN of the music-store-tools Lambda
- `PipelineConsoleUrl` — direct link to the pipeline in the AWS Console

### 4. Activate the CodeStar connection

After the first `cdk deploy`, go to **AWS Console → Developer Tools → Connections**, find your connection, and click **Update pending connection** to authorise it via GitHub. The pipeline will not trigger until the connection status is `Available`.

### 5. Trigger the pipeline

Push a commit to the configured branch. The pipeline starts automatically. On the first run the DB Init stage seeds the Chinook database; all subsequent runs skip that stage. The Deploy stage runs on every push and updates the Lambda if code has changed.

---

## Useful CDK commands

```bash
# Preview changes without deploying
npx cdk diff

# Synthesize CloudFormation template
npx cdk synth

# Destroy all resources
npx cdk destroy
```
