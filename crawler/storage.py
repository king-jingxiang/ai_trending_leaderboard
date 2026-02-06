import json
import boto3
from botocore.exceptions import ClientError
from .config import Config

class Storage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=Config.S3_ENDPOINT_URL,
            aws_access_key_id=Config.S3_ACCESS_KEY_ID,
            aws_secret_access_key=Config.S3_SECRET_ACCESS_KEY,
            region_name=Config.S3_REGION_NAME
        )
        self.bucket = Config.S3_BUCKET_NAME

    def upload_json(self, key, data):
        """Uploads a dictionary as a JSON file to S3."""
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json_str.encode('utf-8'),
                ContentType='application/json'
            )
            print(f"Successfully uploaded {key} to {self.bucket}")
        except ClientError as e:
            print(f"Error uploading {key}: {e}")

    def get_json(self, key):
        """Retrieves a JSON file from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error getting {key}: {e}")
            return None

    def list_files(self, prefix):
        """Lists files in S3 with a given prefix."""
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            
            keys = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        keys.append(obj['Key'])
            return keys
        except ClientError as e:
            print(f"Error listing files with prefix {prefix}: {e}")
            return []
