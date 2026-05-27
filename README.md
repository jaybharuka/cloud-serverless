# Cloud Serverless Messaging

> Send emails and SMS from a static website — zero servers, 100% AWS managed services.

[![AWS SAM](https://img.shields.io/badge/AWS%20SAM-Deployed-orange?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/serverless/sam/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Architecture

```
 Browser (S3 Static Site)
        │
        │  POST /send  {typeOfSending, message, destinationEmail | phoneNumber}
        ▼
 ┌─────────────────┐
 │   API Gateway   │  REST API with CORS
 └────────┬────────┘
          │
          ▼
 ┌─────────────────────────┐
 │  Lambda                 │  restApiHandler — validates input
 │  (RestApiHandlerFunction)│
 └────────┬────────────────┘
          │  StartExecution
          ▼
 ┌──────────────────────────────────────────┐
 │           AWS Step Functions             │
 │                                          │
 │   ┌─── Choice: typeOfSending ──────┐     │
 │   │                                │     │
 │   ▼ "email"              "sms" ▼   │     │
 │ ┌────────────┐      ┌────────────┐ │     │
 │ │   Lambda   │      │   Lambda   │ │     │
 │ │  (email)   │      │   (sms)    │ │     │
 │ └─────┬──────┘      └──────┬─────┘ │     │
 └───────┼────────────────────┼───────┘
         │                    │
         ▼                    ▼
   Amazon SES           Amazon SNS
   (Email delivery)     (SMS delivery)
```

**Request flow:**
1. User submits the form on the **S3-hosted** static site
2. JavaScript POSTs the payload to **API Gateway**
3. A **Lambda** function validates input and starts a **Step Functions** execution
4. Step Functions routes by `typeOfSending`:
   - `"email"` → **Email Lambda** → **Amazon SES**
   - `"sms"` → **SMS Lambda** → **Amazon SNS**

---

## Features

- ✅ Send **email** and **SMS** from a single serverless form
- ✅ Decoupled workflow orchestration via **AWS Step Functions**
- ✅ Input validation and structured error responses at every Lambda
- ✅ CORS-enabled API Gateway for browser clients
- ✅ **Infrastructure as Code** — one-command deploy with AWS SAM
- ✅ Unit tested with **pytest** (mocked AWS calls, no live infrastructure needed)
- ✅ Runs within the **AWS Free Tier** (< $1 / month)

---

## Tech Stack

| Layer | Service / Tool |
|-------|----------------|
| Frontend | HTML · CSS · Vanilla JS hosted on **Amazon S3** |
| API | **Amazon API Gateway** (REST) |
| Orchestration | **AWS Step Functions** |
| Compute | **AWS Lambda** (Python 3.12) |
| Email | **Amazon SES** |
| SMS | **Amazon SNS** |
| IaC | **AWS SAM** (CloudFormation) |
| Testing | **pytest** |

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) | Configured with `aws configure` |
| [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) | Build & deploy |
| Python 3.12+ | Local development & tests |
| Verified SES email | Required as the sender address |

---

## Deployment

### 1. Clone

```bash
git clone https://github.com/<your-username>/cloud-serverless.git
cd cloud-serverless
```

### 2. Build and deploy with SAM

```bash
sam build
sam deploy --guided
```

Answer the prompts:

| Prompt | Value |
|--------|-------|
| Stack Name | `cloud-serverless` |
| AWS Region | `ap-south-1` (or your region) |
| SourceEmail | your **verified SES** email address |
| Confirm changeset | `y` |

### 3. Update the frontend API endpoint

After deploy, grab the output URL:

```bash
aws cloudformation describe-stacks \
  --stack-name cloud-serverless \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

Paste it into `frontend/app.js`:

```js
const API_ENDPOINT = "https://<your-api-id>.execute-api.<region>.amazonaws.com/prod/send";
```

### 4. Upload the frontend to S3

```bash
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name cloud-serverless \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

aws s3 sync frontend/ s3://$BUCKET/
```

### 5. Open the site

```bash
aws cloudformation describe-stacks \
  --stack-name cloud-serverless \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteUrl'].OutputValue" \
  --output text
```

---

## Local Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all unit tests
pytest

# Run with coverage report
pytest --cov=functions --cov-report=term-missing

# Lint
ruff check functions/ tests/

# Format
black functions/ tests/

# Local API (requires Docker)
sam local start-api
```

---

## Project Structure

```
cloud-serverless/
├── functions/
│   ├── rest_api_handler/   # Entry Lambda — validates & starts Step Functions
│   │   └── app.py
│   ├── email_sender/       # Sends email via Amazon SES
│   │   └── app.py
│   └── sms_sender/         # Sends SMS via Amazon SNS
│       └── app.py
├── frontend/
│   ├── index.html          # Single-page messaging form
│   ├── style.css           # Responsive styling
│   └── app.js              # Fetch API integration
├── statemachine/
│   └── sending.asl.json    # Step Functions state machine definition
├── tests/
│   └── unit/               # pytest unit tests (all AWS calls mocked)
│       ├── test_rest_api_handler.py
│       ├── test_email_sender.py
│       └── test_sms_sender.py
├── template.yaml           # AWS SAM template (IaC)
├── samconfig.toml          # SAM deployment defaults
├── pyproject.toml          # pytest + ruff + black config
├── requirements.txt        # Lambda runtime deps
└── requirements-dev.txt    # Local dev & test deps
```

---

## AWS Free Tier Costs

| Service | Free Tier | Typical Usage |
|---------|-----------|---------------|
| S3 | 5 GB storage · 20K GET requests | < 1 MB |
| API Gateway | 1M API calls / month | Negligible |
| Lambda | 1M requests / month | Negligible |
| Step Functions | 4,000 state transitions / month | Negligible |
| SES | 62,000 outbound messages / month | Negligible |
| SNS | 1M publishes / month | Negligible |

**Estimated total cost: < $1 / month**

---

## License

[MIT](LICENSE)
