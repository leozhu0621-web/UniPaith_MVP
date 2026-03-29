"""
Create S3 bucket with proper configuration for UniPaith document storage.
Run once during infrastructure setup.

Usage: python -m scripts.setup_s3
"""
import json

import boto3

from unipaith.config import settings


def main() -> None:
    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    bucket = settings.s3_bucket_name
    region = settings.aws_region

    create_args: dict = {"Bucket": bucket}
    if region != "us-east-1":
        create_args["CreateBucketConfiguration"] = {"LocationConstraint": region}

    client.create_bucket(**create_args)
    print(f"Created bucket: {bucket}")

    client.put_bucket_encryption(
        Bucket=bucket,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )
    print("Enabled AES-256 encryption")

    client.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print("Blocked all public access")

    cors = {
        "CORSRules": [
            {
                "AllowedOrigins": settings.cors_origins,
                "AllowedMethods": ["PUT", "GET"],
                "AllowedHeaders": ["*"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors)
    print("CORS configured")

    lifecycle = {
        "Rules": [
            {
                "ID": "AbortIncompleteMultipartUpload",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1},
            }
        ]
    }
    client.put_bucket_lifecycle_configuration(
        Bucket=bucket, LifecycleConfiguration=lifecycle
    )
    print("Lifecycle rules configured")
    print(f"\nS3_BUCKET_NAME={bucket}")


if __name__ == "__main__":
    main()
