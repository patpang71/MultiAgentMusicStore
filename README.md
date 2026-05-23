# MultiAgent Music Store

A serverless music store application backed by the [Chinook](https://github.com/lerocha/chinook-database) sample database, deployed to AWS Lambda via an automated CodePipeline.

---

## Project Structure

```
MultiAgentMusicStore/
├── dbscripts/
│   ├── Chinook_MySql.sql                    # Original Chinook schema (explicit PKs)
│   └── Chinook_MySql_AutoIncrementPKs.sql   # Chinook schema with AUTO_INCREMENT PKs
├── cdk/                                      # AWS CDK infrastructure (TypeScript)
│   ├── bin/
│   │   └── music-store-app.ts               # CDK app entry point
│   ├── lib/
│   │   ├── constructs/
│   │   │   ├── database.ts                  # RDS MySQL construct
│   │   │   └── pipeline.ts                  # CodePipeline construct
│   │   └── music-store-stack.ts             # Root stack (VPC + DB + Pipeline)
│   ├── buildspecs/
│   │   ├── test.yml                         # Test stage buildspec
│   │   ├── db-init.yml                      # One-time DB seed buildspec
│   │   └── deploy.yml                       # Lambda deploy buildspec (SAM)
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

## Infrastructure (AWS CDK)

All AWS resources are defined as TypeScript CDK code under `cdk/`.

### Resources created

| Resource | Details |
|---|---|
| **VPC** | 2 AZs, public + private subnets, 1 NAT Gateway |
| **RDS MySQL** | `db.t3.micro`, MySQL 8.0, private subnet, credentials in Secrets Manager |
| **CodePipeline** | V2 pipeline — 4 stages (Source → Test → DB Init → Deploy) |
| **CodeBuild projects** | One per stage: `music-store-test`, `music-store-db-init`, `music-store-deploy` |
| **SSM Parameter** | `/music-store/db-initialized` — tracks whether the DB seed has run |
| **Secrets Manager** | `/music-store/db-credentials` — auto-generated RDS admin credentials |

### Pipeline stages

```
GitHub ──► Source ──► Test ──► DB_Init ──► Deploy
```

| Stage | Tool | What it does |
|---|---|---|
| **Source** | CodeStar Connection | Pulls source from GitHub on every push to `main` |
| **Test** | CodeBuild | Runs `pytest tests/` — skips gracefully if no tests exist yet |
| **DB_Init** | CodeBuild (in VPC) | Seeds the Chinook database **once**; subsequent runs are a no-op |
| **Deploy** | CodeBuild | Runs `sam build && sam deploy` to deploy Lambda functions |

### One-time database initialization

The DB Init stage is idempotent. Before running the SQL script it checks for an SSM Parameter at `/music-store/db-initialized`:

- **Not found** → runs `Chinook_MySql_AutoIncrementPKs.sql` against RDS, then sets the parameter to `"true"`.
- **Found (`"true"`)** → skips immediately. The SQL script will never run again unless you manually delete the SSM parameter.

To force a re-seed, delete the flag:

```bash
aws ssm delete-parameter --name "/music-store/db-initialized"
```

---

## Prerequisites

1. [Node.js](https://nodejs.org/) 18+
2. [AWS CLI](https://aws.amazon.com/cli/) configured with credentials (`aws configure`)
3. [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) — `npm install -g aws-cdk`
4. A **GitHub CodeStar Connection** created in the AWS Console:
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
    "codeStarConnectionArn": "arn:aws:codestar-connections:REGION:ACCOUNT_ID:connection/YOUR_CONNECTION_ID"
  }
}
```

Alternatively, pass them on the command line with `-c`:

```bash
cdk deploy \
  -c githubOwner=myorg \
  -c githubRepo=MultiAgentMusicStore \
  -c codeStarConnectionArn=arn:aws:codestar-connections:us-east-1:123456789:connection/abc123
```

### 2. Install dependencies and bootstrap

```bash
cd cdk
npm install

# Bootstrap your AWS account/region once (creates CDK staging bucket etc.)
npx cdk bootstrap
```

### 3. Deploy

```bash
npx cdk deploy
```

CDK will print a diff and ask for confirmation before creating resources. After deployment it outputs:

- `DbEndpoint` — the RDS hostname
- `DbSecretArn` — Secrets Manager ARN for the admin credentials
- `PipelineConsoleUrl` — direct link to the pipeline in the AWS Console

### 4. Trigger the pipeline

Push a commit to the configured branch. The pipeline will start automatically. On the first run, the DB Init stage seeds the Chinook database. All subsequent runs skip that stage.

---

## Application deployment (SAM)

The **Deploy** stage uses [AWS SAM](https://aws.amazon.com/serverless/sam/). Add a `template.yaml` SAM template at the repo root that defines your Lambda functions. The stage runs:

```bash
sam build
sam deploy --stack-name music-store-app --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM ...
```

The S3 bucket used for SAM artifacts is named `music-store-sam-<ACCOUNT_ID>` (must exist before the first deploy, or be created in the SAM template).

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
