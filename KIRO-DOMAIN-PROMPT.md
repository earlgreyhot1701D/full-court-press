Kiro: custom domain fullcourtpress.lol (owner bought it at Porkbun). template.yaml already has optional
SiteDomain / SiteCertArn parameters (Claude, on disk). DO NOT edit application code.
Propose each AWS-changing step and wait for the owner's go. The owner does the Porkbun DNS steps herself.

1. Request the certificate in us-east-1 (CloudFront only uses us-east-1 certificates):
   aws acm request-certificate --domain-name fullcourtpress.lol --subject-alternative-names www.fullcourtpress.lol --validation-method DNS --tags Key=Project,Value=full-court-press --region us-east-1 --profile fcp
2. Get the validation records and give them to the owner as a table (Type CNAME, Host, Answer):
   aws acm describe-certificate --certificate-arn <arn> --region us-east-1 --profile fcp --query "Certificate.DomainValidationOptions[].ResourceRecord"
   Porkbun note for the owner: in the Host field, enter only the part before ".fullcourtpress.lol"
   (Porkbun appends the domain), and paste the Answer without a trailing dot if Porkbun rejects it.
3. Wait for ISSUED (usually minutes after the owner saves the records):
   aws acm wait certificate-validated --certificate-arn <arn> --region us-east-1 --profile fcp
4. Deploy with the domain (owner's go):
   sam deploy --parameter-overrides SiteDomain=fullcourtpress.lol SiteCertArn=<arn>
   (keep the other saved parameters; if samconfig.toml drops AlertEmail, pass it again)
5. Give the owner the CloudFrontDomain output (dxxxx.cloudfront.net) for Porkbun:
   - ALIAS record, Host blank (apex), Answer = CloudFrontDomain
   - CNAME record, Host www, Answer = CloudFrontDomain
   (delete Porkbun's default parking records for the apex and www first)
6. After DNS: https://fullcourtpress.lol and https://www.fullcourtpress.lol load with the headers from
   CHECKPOINT 5. Then rebuild the latest night once so SITE_URL (share-card links) uses the new domain.
Log in BUILD-LOG.md and LEDGER.md as (Kiro).
