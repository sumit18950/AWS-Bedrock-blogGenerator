import json
import boto3
import botocore.config
from datetime import datetime

MODEL_ID = "amazon.nova-lite-v1:0"
S3_BUCKET = "aws-bedrock-course1"  # S3 bucket names cannot contain underscores


def blog_generate_using_bedrock(blogtopic: str) -> str:
    try:
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            config=botocore.config.Config(read_timeout=300, retries={"max_attempts": 3}),
        )

        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": f"Write a 200 word blog on the topic: {blogtopic}"}],
                }
            ],
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )

        return response["output"]["message"]["content"][0]["text"]

    except Exception as e:
        print(f"Error generating the blog: {e}")
        return ""


def save_blog_details_s3(s3_key: str, s3_bucket: str, generate_blog: str) -> bool:
    s3 = boto3.client("s3")
    try:
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=generate_blog)
        print("Blog saved to S3")
        return True
    except Exception as e:
        print(f"Error when saving the blog to S3: {e}")
        return False


def lambda_handler(event, context):
    # API Gateway sends the body as a JSON string; a direct test event may send a dict
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    blogtopic = body.get("blog_topic")
    if not blogtopic:
        return {
            "statusCode": 400,
            "body": json.dumps("blog_topic is required"),
        }

    generate_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

    if not generate_blog:
        return {
            "statusCode": 500,
            "body": json.dumps("Blog generation failed"),
        }

    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    s3_key = f"blog-output/{current_time}.txt"

    if not save_blog_details_s3(s3_key, S3_BUCKET, generate_blog):
        return {
            "statusCode": 500,
            "body": json.dumps("Blog generated but saving to S3 failed"),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Blog generation is completed", "s3_key": s3_key}),
    }