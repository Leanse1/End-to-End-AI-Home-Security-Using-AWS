import os
import boto3
from PIL import Image, ImageDraw
import credentials

# AWS credentials and region
reko_access_key = 'AKIAU6GDXAQ5KBQTR64S'
reko_secret_key = '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'

# Initialize AWS Rekognition client
rekognition = boto3.client('rekognition',
                          aws_access_key_id=reko_access_key,
                          aws_secret_access_key=reko_secret_key)

# Directory paths
input_dir = 'motion_images'
human_output_dir = 'human_detected'
unknown_output_dir = 'unknown_motion'

# Create output directories if they don't exist
for directory in [human_output_dir, unknown_output_dir]:
    os.makedirs(directory, exist_ok=True)

# Function to draw bounding boxes on images
def draw_bounding_boxes(image, bounding_boxes, detected_label):
    draw = ImageDraw.Draw(image)
    for box in bounding_boxes:
        left, top, width, height = box['Left'], box['Top'], box['Width'], box['Height']
        img_width, img_height = image.size
        left, top, right, bottom = left * img_width, top * img_height, (left + width) * img_width, (top + height) * img_height
        draw.rectangle([left, top, right, bottom], outline='red', width=3)
        draw.text((left, top), detected_label, fill='red')
    return image

# Function to detect humans in images using Rekognition
def detect_human(image_path):
    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()
        response = rekognition.detect_faces(Image={'Bytes': image_bytes})

        # If faces are detected, consider it as human presence
        if response['FaceDetails']:
            image = Image.open(image_path)
            bounding_boxes = [{'Left': face['BoundingBox']['Left'],
                               'Top': face['BoundingBox']['Top'],
                               'Width': face['BoundingBox']['Width'],
                               'Height': face['BoundingBox']['Height']} for face in response['FaceDetails']]
            modified_image = draw_bounding_boxes(image, bounding_boxes, 'Human Detected')
            return modified_image, True
        else:
            return None, False


# Main function to process images
def process_images():
    for filename in os.listdir(input_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_dir, filename)
            human_output_path = os.path.join(human_output_dir, filename)
            unknown_output_path = os.path.join(unknown_output_dir, filename)
            print(f"Processing {filename}...")
            modified_image, human_detected = detect_human(input_path)
            if human_detected:
                modified_image.save(human_output_path)
                print(f"Human detected image saved to {human_output_path}")
            else:
                modified_image = Image.open(input_path)  # Open original image
                modified_image.save(unknown_output_path)
                print(f"Unknown motion image saved to {unknown_output_path}")

if __name__ == "__main__":
    process_images()