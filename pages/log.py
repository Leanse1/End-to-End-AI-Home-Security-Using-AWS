import streamlit as st
import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('leanse-family-log')  # Replace 'your-table-name' with your DynamoDB table name

def retrieve_time(date, name):
    response = table.get_item(
        Key={
            'date': date,
            'name': name
        }
    )
    item = response.get('Item')
    if item:
        return item.get('time')
    else:
        return None

# Function to get unique dates from the DynamoDB table
def get_unique_dates():
    response = table.scan()
    items = response.get('Items', [])
    dates = set()
    for item in items:
        dates.add(item['date'])
    return sorted(dates)

# Function to get unique names from the DynamoDB table
def get_unique_names():
    response = table.scan()
    items = response.get('Items', [])
    names = set()
    for item in items:
        names.add(item['name'])
    return sorted(names)

# Streamlit app
def main():
    st.title('Time Retrieval App')
    
    # Dropdown box for selecting date
    dates = get_unique_dates()
    selected_date = st.selectbox('Select Date', dates)
    
    # Dropdown box for selecting name
    names = get_unique_names()
    selected_name = st.selectbox('Select Name', names)
    
    # Button to retrieve time
    if st.button('Retrieve Time'):
        time = retrieve_time(selected_date, selected_name)
        if time:
            st.success(f"{selected_name} was last seen at {time}")
        else:
            st.error("No record found for the selected date and name.")

if __name__ == "__main__":
    main()
