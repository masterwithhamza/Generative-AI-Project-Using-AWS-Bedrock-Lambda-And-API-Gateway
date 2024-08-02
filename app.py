import boto3
import botocore.config
import json

from datetime import datetime

def blog_generate_using_bedrock(blogtopic: str) -> str:
    prompt = f"Write a 200-word blog on the topic: {blogtopic}"

    body = {
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0.5,
        "top_p": 0.9
    }

    try:
        # Create a Bedrock client
        bedrock = boto3.client("bedrock-runtime", region_name="ap-south-1",
                               config=botocore.config.Config(read_timeout=300, retries={'max_attempts': 3}))
        
        # Invoke the model
        response = bedrock.invoke_model(body=json.dumps(body), modelId="meta.llama3-70b-instruct-v1:0")
        
        # Read the response body
        response_content = response.get('body').read()
        response_data = json.loads(response_content)

        # Extract generated content
        blog_details = response_data.get('generation', '')
        return blog_details
    except Exception as e:
        print(f"Error generating the blog: {e}")
        return ""

def save_blog_details_s3(s3_key: str, s3_bucket: str, generate_blog: str):
    s3 = boto3.client('s3')

    try:
        # Put the generated blog into the specified S3 bucket
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=generate_blog)
        print("Blog saved to S3")
    except Exception as e:
        print(f"Error when saving the blog to S3: {e}")

def lambda_handler(event, context):
    try:
        # Parse the incoming event body
        event = json.loads(event['body'])
        blogtopic = event['blog_topic']

        # Generate blog content
        generate_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

        if generate_blog:
            # Define S3 key and bucket
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            s3_key = f"blog-output/{current_time}.txt"
            s3_bucket = 'bedrock-with-hamza'

            # Save the blog content to S3
            save_blog_details_s3(s3_key, s3_bucket, generate_blog)
        else:
            print("No blog was generated")

        return {
            'statusCode': 200,
            'body': json.dumps('Blog Generation is completed')
        }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred during blog generation')
        }
