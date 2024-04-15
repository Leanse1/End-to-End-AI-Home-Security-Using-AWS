import streamlit as st
import cv2
import boto3
import re

st.set_page_config(page_title='Registration Form')
st.subheader('Registration Form')

# Initialize AWS Rekognition and DynamoDB clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('leanse-family-db')  # Replace 'leanse-family-db' with your DynamoDB table name

# Create the collection if it doesn't exist
collection_id = 'family_members'
existing_collections = rekognition.list_collections()['CollectionIds']
if collection_id not in existing_collections:
    rekognition.create_collection(CollectionId=collection_id)

# Form inputs
person_name = st.text_input(label='Name', placeholder='First & Last Name')
role = st.selectbox(label='Select your Relationship with Leanse', options=('Myself', 'Family', 'Friend', 'Neighbor', 'Others'))

# Function to capture image from webcam and send to AWS Rekognition
def capture_and_send_to_rekognition(frame):
    # Convert captured frame to bytes
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_bytes = img_encoded.tobytes()

    # Modify person_name to ensure it contains valid characters
    person_name_modified = re.sub(r'[^a-zA-Z0-9_.\-:]', '', person_name)

    # Call AWS Rekognition to detect faces
    response = rekognition.index_faces(
        CollectionId=collection_id,
        Image={'Bytes': img_bytes},
        ExternalImageId=person_name_modified,
        DetectionAttributes=['DEFAULT']
    )

    # Extract face details if available
    if len(response.get('FaceRecords', [])) > 0:
        for face_record in response['FaceRecords']:
            face_id = face_record['Face']['FaceId']
            # Store face details in DynamoDB
            try:
                table.put_item(
                    Item={
                        'rekognition_id': face_id,
                        'name': person_name,
                        'relationship': role
                    }
                )
                st.success("Data successfully submitted and uploaded to DynamoDB.")
            except Exception as e:
                st.error(f"Error adding item to DynamoDB: {e}")

# Display live video stream from webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    st.error("Error: Unable to open webcam.")
else:
    ret, frame = cap.read()
    st.image(frame, caption='Live Video Stream', channels='BGR')

# Button to capture image and display it
if st.button('Capture Image'):
    st.image(frame, caption='Captured Image', channels='BGR')
    # capture_and_send_to_rekognition(frame)

# Button to submit registration data
if st.button('Submit'):
    # Perform recognition on the captured image
    capture_and_send_to_rekognition(frame)
