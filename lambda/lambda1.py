from __future__ import print_function
import boto3
from datetime import datetime, timedelta
import json

print('Loading function')

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
familyLogTable = dynamodb.Table('leanse-family-log')
leanseFamily = dynamodb.Table('leanse-family-db')

def lambda_handler(event, context):
    if 'Records' in event and 's3' in event['Records'][0]:
        # S3 trigger
        process_s3_event(event)
    elif 'Records' in event and 'Sns' in event['Records'][0]:
        # SNS trigger
        process_sns_event(event)
    else:
        print("Unsupported event type")

def process_s3_event(event):
    # Get the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    timestamp = datetime.now()
    adjusted_timestamp = timestamp + timedelta(hours=5, minutes=30)
    date_time_str = adjusted_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    print("Date-time:", date_time_str)  # Add this line for debugging
    
    timestamp1 = datetime.now()
    adjusted_timestamp1 = timestamp + timedelta(hours=5, minutes=30)
    year_month_day = adjusted_timestamp1.strftime("%Y-%m-%d")
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

        # Get the name associated with the detected face
        face_id = match['Face']['FaceId']
        name = get_name_from_face_id(face_id)

        # Store the detection in the family-log DynamoDB table
        familyLogTable.put_item(
            Item={
                'date': date_time_str[:10], 
                'name': name,      # Extracting date from date-time string
                'time': date_time_str[11:19]   # Extracting time from date-time string
            }
        )
    
    # If the detected person is "Unknown", send an SNS notification
    if name == 'Unknown':
        send_sns_notification(name, date_time_str)

def process_sns_event(event):
    # Process SNS event
    # Your logic for handling SNS events goes here
    pass

def get_name_from_face_id(face_id):
    # Perform a query to retrieve the name associated with the face ID
    try:
        response = leanseFamily.get_item(
                    Key={'rekognition_id': face_id}
                     )
        item = response.get('Item')
        if item:
            return item.get('name')
        else:
            return 'Unknown'  # If no matching name found for the face ID
    except Exception as e:
        print("Error:", e)
        return 'Unknown'  # Handle errors gracefully

def send_sns_notification(name, date_time_str):
    # Send an SNS notification
    message = f"Unknown person detected at {date_time_str}."
    sns.publish(
        TopicArn='',
        Message=message
    )
    print("SNS notification sent:", message)
