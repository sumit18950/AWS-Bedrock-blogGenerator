# AWS-Bedrock-blogGenerator
# AWS Blog Generator (Serverless, Amazon Bedrock)

A serverless application that generates a ~200-word blog post on any topic using Amazon Nova Lite on Amazon Bedrock and stores the result in Amazon S3.

## Architecture

```
Client (Postman) -> API Gateway (POST /blog-generation) -> AWS Lambda (Python) -> Amazon Bedrock (Nova Lite) -> Amazon S3
```

1. A client sends a POST request with a blog topic to the API Gateway endpoint.
2. API Gateway triggers the Lambda function.
3. Lambda calls Amazon Nova Lite through the Bedrock Converse API to generate the blog.
4. Lambda saves the blog as a `.txt` file in an S3 bucket and returns the file's key.

## Services Used

- Amazon Bedrock (Converse API, `amazon.nova-lite-v1:0`)
- AWS Lambda (Python)
- Amazon API Gateway
- Amazon S3
- AWS IAM
- Postman (testing)

## Project Structure

```
aws-blog-project/
├── app.py              # Lambda function code
├── python/             # boto3 packages for the Lambda layer (not committed)
├── boto3-layer.zip     # Lambda layer archive (not committed)
└── README.md
```

## API

**Endpoint:** `POST /blog-generation`

**Request body:**

```json
{
  "blog_topic": "machine learning"
}
```

**Success response (200):**

```json
{
  "message": "Blog generation is completed",
  "s3_key": "blog-output/20261122-150034.txt"
}
```

**Error responses:**

| Status | Meaning |
|--------|---------|
| 400 | `blog_topic` missing from the request |
| 500 | Blog generation failed, or saving to S3 failed |

## Setup

### 1. S3 bucket

Create an S3 bucket with a globally unique name (lowercase letters, numbers and hyphens only; no underscores). Keep "Block all public access" enabled. Set the same name in `app.py`:

```python
S3_BUCKET = "your-bucket-name"
```

### 2. Lambda layer (newer boto3)

The boto3 version built into the Lambda runtime is too old for the Converse API, so a layer provides a newer one.

```powershell
python -m pip install boto3 -t python/
tar -a -c -f boto3-layer.zip python
```

Upload `boto3-layer.zip` as a new layer in Lambda, choose the same Python runtime as your function, and attach the layer to the function.

### 3. Lambda function

- Runtime: Python 3.x
- Paste the code from `app.py`
- Set the timeout to 30-60 seconds (the 3-second default is too short)

### 4. IAM permissions

Add an inline policy to the Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

### 5. API Gateway

Create a REST API with a `POST` method on `/blog-generation`, integrate it with the Lambda function, and deploy it to a stage (for example `dev`).

## Testing

Send a POST request with Postman (body type: raw) or curl:

```bash
curl -X POST "https://<api-id>.execute-api.<region>.amazonaws.com/dev/blog-generation" \
  -H "Content-Type: application/json" \
  -d '{"blog_topic": "machine learning"}'
```

Then open the S3 bucket and check the `blog-output/` folder for the generated file.

## Notes

- Bedrock is called in `us-east-1`. The Lambda and API Gateway can run in any region.
- The API currently has no authentication. Add an API key or usage plan before leaving it public.

## Possible Improvements

- Accept tone and word count in the request body
- Return the blog text in the API response
- Add API authentication
