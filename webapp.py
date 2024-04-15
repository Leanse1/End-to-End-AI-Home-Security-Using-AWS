import cv2
import time
import os
import streamlit as st
import boto3
import credentials
from datetime import datetime

s3 = boto3.client("s3", aws_access_key_id=credentials.aws_access_key,
                           aws_secret_access_key=credentials.aws_secret_key)


def upload_to_s3(local_file, bucket, s3_file_key):
    # Extract year, month, and day from the current timestamp
    timestamp = datetime.now()
    year_month = timestamp.strftime("%Y-%m")
    day = timestamp.strftime("%d")

    # Define the S3 file key with folder structure
    s3_file_key = f"{year_month}/{day}/{s3_file_key}"

    # Upload the file to S3
    s3.upload_file(local_file, bucket, s3_file_key)



def main():
    # Create a VideoCapture object
    cap = cv2.VideoCapture(0)

    # Set up initial frame for motion detection
    _, frame1 = cap.read()
    _, frame2 = cap.read()

    # Create an output directory for motion images
    output_directory = "motion_images"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    if not cap.isOpened():
        st.error("Error opening video!")
        exit()

    # Set up Streamlit UI
    st.title("Motion Detection Streamlit App")
    st.sidebar.header("Settings")

    threshold = st.sidebar.slider("Motion Threshold", min_value=1, max_value=100, value=30, step=1)
    st.sidebar.markdown("Adjust the motion threshold to control sensitivity.")

    st.sidebar.markdown("---")

    st.sidebar.header("Motion History")
    motion_history = st.sidebar.empty()

    st.sidebar.markdown("---")

    st.sidebar.header("Saved Images")
    saved_images = st.sidebar.empty()

    st.sidebar.markdown("---")


    # Create a placeholder for the video player
    video_placeholder = st.empty()

    while True:
        ret, frame3 = cap.read()
        
        if not ret:
           break

        # Calculate frame differences
        diff1 = cv2.absdiff(frame1, frame2)
        diff2 = cv2.absdiff(frame2, frame3)

        # Get the thresholded difference
        _, thresh1 = cv2.threshold(diff1, threshold, 255, cv2.THRESH_BINARY)
        _, thresh2 = cv2.threshold(diff2, threshold, 255, cv2.THRESH_BINARY)

        # Combine the thresholded differences
        motion_diff = cv2.bitwise_and(thresh1, thresh2)
        motion_diff_gray = cv2.cvtColor(motion_diff, cv2.COLOR_BGR2GRAY)

        # Display grayscale motion difference image
        video_placeholder.image(frame3, channels="BGR", caption="Motion Detection", width=800, use_column_width=False, output_format='JPEG')

        # Update frames
        frame1 = frame2
        frame2 = frame3

        # Get the frame rate of the camera
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Display motion history count
        motion_count = cv2.countNonZero(motion_diff_gray)
        motion_history.markdown(f"Motion Detected: **{motion_count} pixels**")

        # Save image if motion is detected
        if motion_count > 3000:
            # Save the image with a timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_directory, f"motion_{timestamp}.png")
            cv2.imwrite(filename, frame3)
            saved_images.success(f"Motion detected! Image saved: {filename}")
            
            s3_file_key = f"motion_{timestamp}.png"
            upload_to_s3(filename, "home-security-bucket", s3_file_key)



        # Sleep for an interval based on the frame rate
        # Check if the frame rate is valid (not zero)
        if fps > 0:
            # Sleep for an interval based on the frame rate
            time.sleep(1 / fps)
        else:
            # If the frame rate is zero, sleep for a default interval
            time.sleep(0.1)

        
    cap.release()

if __name__ == "__main__":
    main()
