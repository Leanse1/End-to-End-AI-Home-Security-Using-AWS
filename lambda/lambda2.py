from __future__ import print_function
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
import json
from io import BytesIO
import os

print('Loading function')

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodbTableName = 'leanse-family-db'
dynamodb = boto3.resource('dynamodb')
familyTable = dynamodb.Table(dynamodbTableName)

def index_faces(bucket, key):
    response = rekognition.index_faces(
        Image={"S3Object":
            {"Bucket": bucket,
            "Name": key}},
            CollectionId="family_members")
    return response

def lambda_handler(event, context):
    # Get the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    timestamp = datetime.now()
    year_month_day = timestamp.strftime("%Y-%m-%d")
    print("Year-month-day:", year_month_day)  # Add this line for debugging
    year, month, day = year_month_day.split('-')

    # Check if the object belongs to today's date folder
    if f"{year}-{month}/{day}" not in object_key:
        return {
            'statusCode': 200,
            'body': json.dumps('Object does not belong to today\'s date folder.')
        }

    # Read the object from S3
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    image_bytes = response['Body'].read()

    # Detect faces in the image
    response_faces = rekognition.search_faces_by_image(
        CollectionId='family_members',
        Image={'Bytes': image_bytes},
        FaceMatchThreshold=50  # Lowering the threshold for potential matches
    )

    print("Face detection response:", response_faces)

    # Process face matches
    for match in response_faces['FaceMatches']:
        print(match['Face']['FaceId'], match['Face']['Confidence'])

        face = familyTable.get_item(
            Key={'rekognition_id': match['Face']['FaceId']}
        )
    
        print("Debug - face:", face)  # Add this line for debugging
    
        if 'Item' in face:
            print("Debug - face['Item']:", face['Item'])  # Add this line for debugging
    
            if 'name' in face['Item']:
                print("The face identified is:", face['Item']['name'])
                print("Relationship:", face['Item']['relationship'])
    
                try:
                    # Upload the image to the 'family-members' S3 bucket
                    s3.upload_fileobj(BytesIO(image_bytes), 'family-members', object_key)
                    print("Image uploaded to 'family-members' S3 bucket.")
                except Exception as e:
                    print("Error uploading image to S3:", e)
            else:
                print("No 'name' attribute found in DynamoDB item.")
        else:
            print('No match found in person lookup')
