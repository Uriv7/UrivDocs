#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  UrivDocs — S3 Bucket Setup Script
#  Run this on your LOCAL machine (not EC2)
#  Requires: aws configure already done
#  Usage: bash scripts/setup_s3.sh YOUR_BUCKET_NAME us-east-1
# ═══════════════════════════════════════════════════════════════

BUCKET_NAME="${1:-urivdocs-uploads-$(whoami)}"
REGION="${2:-us-east-1}"

echo "🚀 Creating S3 bucket: $BUCKET_NAME in $REGION"

# Create bucket
if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"
else
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
fi

# Block all public access (files are private)
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning (keeps history of uploaded files)
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# Create uploads/ folder
aws s3api put-object --bucket "$BUCKET_NAME" --key "uploads/"

echo ""
echo "✅ S3 bucket created: $BUCKET_NAME"
echo ""
echo "Add these to your .env and GitHub Secrets:"
echo "  S3_BUCKET=$BUCKET_NAME"
echo "  AWS_REGION=$REGION"
