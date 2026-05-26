# GitHub Secrets Setup Guide

Go to: **GitHub → Your Repo → Settings → Secrets and variables → Actions → New repository secret**

Add EXACTLY these secrets:

| Secret Name | Example Value | How to Get |
|---|---|---|
| `EC2_HOST` | `54.123.45.67` | AWS EC2 Console → Public IPv4 address |
| `EC2_USERNAME` | `ubuntu` | Always `ubuntu` for Ubuntu AMI |
| `SSH_PRIVATE_KEY` | `-----BEGIN RSA...` | `cat urivdocs-key.pem` — copy ALL content |
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | AWS IAM → User → Security credentials → Access keys |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI...` | Same as above (only shown once!) |
| `AWS_REGION` | `us-east-1` | The AWS region you chose |
| `S3_BUCKET` | `urivdocs-uploads-yourname` | The bucket name you created |
| `DOMAIN_NAME` | `yourdomain.com` | Your domain (or your EC2 IP if no domain) |

## How to get SSH_PRIVATE_KEY

```bash
cat urivdocs-key.pem
```

Copy the ENTIRE output — it looks like this:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890abcdef...
...many lines...
-----END RSA PRIVATE KEY-----
```

Paste every single line including the BEGIN and END lines.

## Common Mistakes

1. SSH_PRIVATE_KEY — don't add extra spaces or newlines at start/end
2. EC2_HOST — just the IP address, no http:// prefix
3. S3_BUCKET — just bucket name, no s3:// prefix
4. AWS keys — must belong to IAM user with S3 + EC2 permissions
