import aiohttp
import aiofiles
import asyncio
import json
import os  # To access environment variables

# Function to generate plate numbers
def generate_plate_numbers():
    with open('current_prefix.txt', 'r') as file:
        prefix = file.read().strip()
    for number_part in range(0, 1000):  # From '000' to '999'
        yield f'{prefix}{number_part:03d}'

# Function to refresh the bearer token
async def refresh_bearer_token(session):
    url = 'https://identity.sa.gov.au/auth/realms/sagov-idx/protocol/openid-connect/token'
    refresh_token = os.getenv('REFRESH_TOKEN')  # Retrieve the refresh token from environment variable
    if not refresh_token:
        raise ValueError("Refresh token is missing. Please set the REFRESH_TOKEN environment variable.")
    
    payload = {
        'client_id': 'DigitalPass',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    async with session.post(url, data=payload) as response:
        response.raise_for_status()  # Raise an error for bad responses
        json_response = await response.json()
        return json_response['access_token']

# Function to send a request with retry logic
async def send_request_with_retry(session, plate_number, bearer_token):
    url = f'https://api.sa.gov.au/mysagov/checkvehicles/{plate_number}'
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Ocp-Apim-Subscription-Key': '4b761fe5b77d443f883698da01afa5e3'
    }
    retries = 3
    attempt = 0

    while attempt < retries:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    print(f'HTTP 401 Unauthorized for {plate_number}. Refreshing token...')
                    return 'REFRESH'  # Indicate the need for a token refresh
                elif response.status == 404:
                    print(f'HTTP 404 error encountered for {plate_number}, giving up.')
                    return None  # Stop retrying and give up
                else:
                    print(f'Received status code {response.status} for {plate_number}')
        except aiohttp.ClientError as e:
            print(f'Attempt {attempt + 1} failed for {plate_number}: {e}')
        attempt += 1
        if attempt < retries:
            await asyncio.sleep(5)  # Wait before retrying
    return None  # Return None if all retries fail

# Function to check registration for each plate number and save the response
async def check_registration():
    async with aiohttp.ClientSession() as session:
        bearer_token = await refresh_bearer_token(session)

        # Ensure the directory exists to save the JSON files
        os.makedirs('plates', exist_ok=True)

        tasks = []
        for plate_number in generate_plate_numbers():
            task = asyncio.create_task(handle_plate_number(session, plate_number, bearer_token))
            tasks.append(task)

            if len(tasks) >= 5:  # Limit to 2 concurrent requests
                await asyncio.gather(*tasks)  # Wait for all tasks to complete
                tasks = []  # Reset the tasks list

        # Make sure to await any remaining tasks
        if tasks:
            await asyncio.gather(*tasks)

# Function to handle each plate number
async def handle_plate_number(session, plate_number, bearer_token):
    response_json = await send_request_with_retry(session, plate_number, bearer_token)
    
    # Retry with a refreshed token if a 401 response was received
    if response_json == 'REFRESH':
        bearer_token = await refresh_bearer_token(session)  # Refresh the token
        response_json = await send_request_with_retry(session, plate_number, bearer_token)  # Retry with the new token
    
    if response_json:
        # Save the response only if the status code was 200
        async with aiofiles.open(f'plates/{plate_number}.json', 'w') as f:
            await f.write(json.dumps(response_json, indent=4))
        print(f'Saved response for {plate_number}')
    else:
        print(f'Failed to retrieve or save data for {plate_number} after multiple attempts.')

if __name__ == '__main__':
    asyncio.run(check_registration())