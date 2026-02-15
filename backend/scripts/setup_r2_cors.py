#!/usr/bin/env python
"""
Script to configure CORS on Cloudflare R2 bucket for direct browser uploads.

Run this once to enable PDF uploads from the frontend.

Usage:
    cd backend
    source venv/Scripts/activate  # or venv/bin/activate on Linux/Mac
    python scripts/setup_r2_cors.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

import boto3
from botocore.client import Config

def setup_cors():
    """Configure CORS on the R2 bucket."""

    # Get credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    endpoint_url = os.getenv('AWS_S3_ENDPOINT_URL')
    region = os.getenv('AWS_S3_REGION_NAME', 'auto')

    if not all([access_key, secret_key, bucket_name, endpoint_url]):
        print("Error: Missing required environment variables.")
        print("Make sure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, and AWS_S3_ENDPOINT_URL are set.")
        sys.exit(1)

    print(f"Configuring CORS for bucket: {bucket_name}")
    print(f"Endpoint: {endpoint_url}")

    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        region_name=region,
        config=Config(signature_version='s3v4')
    )

    # CORS configuration for browser uploads
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedOrigins': [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000',
                    'http://127.0.0.1:3001',
                    # Add your production domain here:
                    # 'https://syncscript.yourdomain.com',
                ],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedHeaders': ['*'],
                'ExposeHeaders': ['ETag', 'Content-Length', 'Content-Type'],
                'MaxAgeSeconds': 3600
            }
        ]
    }

    try:
        # Apply CORS configuration
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print("✓ CORS configuration applied successfully!")

        # Verify by reading back
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        print("\nCurrent CORS rules:")
        for i, rule in enumerate(response.get('CORSRules', []), 1):
            print(f"\nRule {i}:")
            print(f"  AllowedOrigins: {rule.get('AllowedOrigins', [])}")
            print(f"  AllowedMethods: {rule.get('AllowedMethods', [])}")
            print(f"  AllowedHeaders: {rule.get('AllowedHeaders', [])}")
            print(f"  ExposeHeaders: {rule.get('ExposeHeaders', [])}")
            print(f"  MaxAgeSeconds: {rule.get('MaxAgeSeconds', 'N/A')}")

    except Exception as e:
        print(f"Error configuring CORS: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_cors()
