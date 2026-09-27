Kiro: one deploy that ships the custom domain (KIRO-DOMAIN-PROMPT.md steps 3 to 6) and the favicon +
default social preview (commit d20a423, Claude, on disk, 182 tests passing). DO NOT edit application code.
Propose each AWS-changing step and wait for the owner's go. The owner does the Porkbun DNS steps herself.
Never print the account ID or the full cert ARN in chat or logs (say "the cert ARN").

1. Confirm the certificate is ISSUED (wait if still pending):
   aws acm wait certificate-validated --certificate-arn <cert arn> --region us-east-1 --profile fcp
   If it has not validated after the wait times out, stop and report. Do not deploy without the domain.
2. Rebuild the Lambda bundle (never sam build):
   python tools/build_lambda.py
   Check build/lambda/static/ contains favicon.svg, favicon-32.png, apple-touch-icon.png, og-default.png.
3. Deploy once, with the domain (owner's go):
   sam deploy --parameter-overrides SiteDomain=fullcourtpress.lol SiteCertArn=<cert arn>
   (keep the other saved parameters; if samconfig.toml drops AlertEmail, pass it again)
4. Give the owner the CloudFrontDomain output for Porkbun (she has already deleted the parking records):
   - ALIAS, Host blank, Answer = CloudFrontDomain
   - CNAME, Host www, Answer = CloudFrontDomain
   Wait for her "DNS saved."
5. Rebuild the latest night so static files, front pages and SITE_URL links refresh:
   invoke fcp-hunter with {"nights": ["<latest night>"]}, then invalidate CloudFront /*.
6. Check, PASS/FAIL each:
   - https://fullcourtpress.lol and https://www.fullcourtpress.lol load with the CHECKPOINT 5 headers
   - /static/favicon.svg returns 200 with content-type image/svg+xml
   - front page HTML has rel="icon" and og:image = https://fullcourtpress.lol/static/og-default.png
   - a game page from the rebuilt night has og:image ending in card.png on the new domain
7. Tell the owner to republish golden herself (the golden pages need the new icon links):
   set SITE_URL=https://fullcourtpress.lol/ first so golden gets absolute preview links.
Log in BUILD-LOG.md and LEDGER.md as (Kiro).
