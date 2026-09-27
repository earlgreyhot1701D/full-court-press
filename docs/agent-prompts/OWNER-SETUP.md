# Owner setup (Shara does these, Kiro doesn't)

| When | Step |
|---|---|
| Before kickoff | Fill in the "Who it's for" line in `.kiro/steering/product.md` |
| Decided | Budget $10/month alarm, $25/month wind-down ceiling |
| Before Block 5b | Pick the Polly voice: AWS Console > Amazon Polly > Text-to-Speech, Engine: **Neural**, paste a transcript, Listen. Compare Danielle and Ruth. Tiffany is generative-only, so she is out |
| Block 0 | Activate the `Project` tag under Billing > Cost allocation tags once it appears (up to 24 hours after the first tagged resource) |
| Done Sep 20 | Compliance gate closed: ESPN ruled out, BALLDONTLIE chosen. See LEDGER.md |
| Before Block 0.4 | Create a free BALLDONTLIE account, get the API key, and put it in SSM Parameter Store as a SecureString named `/full-court-press/bdl-api-key`. Do not paste the key into Kiro |
| Block 0.4 | Decide on the data tier if player stats return 401: ALL-STAR is $9.99/month per sport and unlocks the spotlight, box score and The Number |
| Before Block 0.3 | Install the **Agent Toolkit for AWS**: https://raw.githubusercontent.com/aws/agent-toolkit-for-aws/refs/heads/main/setup-instructions/setup.md . Profile `fcp`, region `us-east-1`. Sign in with `aws login` in the browser. No access keys, no MFA setup needed |
| Before Block 0.3 | In Kiro's MCP config, add `"AWS_MCP_PROXY_PROFILES": "fcp"` to the `aws-mcp` server entry |
| Fallback only | If the toolkit will not install: create IAM user `fcp-kiro-agent` **in the console yourself**, console access unchecked (no password, no MFA), tag `Project=full-court-press`, create one access key, then run `aws configure --profile fcp` locally and paste it. Kiro has no place to store AWS keys: it reads the profile from your machine. Do NOT have Kiro run `aws iam create-access-key`, because the secret would be printed into its transcript. Delete the key at wind-down |
| Block 0.3 | Screenshot the toolkit sign-in, the skill list, Kiro's `aws-mcp` config block, the CloudTrail event list filtered to `fcp-kiro-agent`, and the console showing what the agent created. Blur the account id in all of them |
| Block 0.3 | Post in the hackathon Discussion tab: what form of "proof of coding agent connection to the AWS console" do they want? Nobody has asked yet |
| Block 0.5 | If the model needs access enabled in the Bedrock console, enable it |
| Block 2.3 | Approve the 5 golden games |
| Block 3.6 | Read 2 issues. Approve or redirect the voices |
| Block 5.4 | Approve `sam deploy` |
| Oct 1 | Builder Center post: live URL, golden link, connection proof, AWS services, dev process, tags `#personal-expression` `#community` |
| Oct 2 by noon PT | Submit |
| After judging | Block 7 wind down |

Open question to post in the hackathon Discussion tab: what form should "proof of coding agent connection to the AWS console" take?
