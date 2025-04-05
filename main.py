import boto3
import dropbox
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
AWS_REGION = 'us-east-1'
S3_BUCKET = 'your-s3-bucket-name'
PREFIX = 'your_s3_prefix'  # Replace with the s3 folder prefix you want to process
PRESIGNED_URL_EXPIRATION = 3600  # seconds

DROPBOX_ACCESS_TOKEN = 'your_dropbox_access_token'

# --- AWS S3 Client ---
s3_client = boto3.client('s3', region_name=AWS_REGION)

def list_source_objects(prefix):
    """
    List all objects in the S3 bucket for a given prefix.
    Expected key format: {prefix}/...
    """
    prefix = f"{prefix}/"
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    
    source_objects = []
    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            
            # Parse path here for specific objects as needed
            parts = key.split('/')

            source_objects.append(key)
    return source_objects

def generate_presigned_urls(keys):
    """
    Generate pre-signed URLs for a list of S3 object keys.
    """
    urls = {}
    for key in keys:
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        urls[key] = url
    return urls

def create_dropbox_folder(dbx):
    """
    Create a Dropbox folder with a random 10-digit numeric name.
    """
    folder_name = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    dropbox_path = f"/{folder_name}"
    try:
        dbx.files_create_folder_v2(dropbox_path)
        print(f"Created Dropbox folder: {dropbox_path}")
    except dropbox.exceptions.ApiError as err:
        print(f"Failed to create folder {dropbox_path}: {err}")
        raise
    return dropbox_path

def save_files_to_dropbox(dbx, dropbox_folder, urls):
    """
    For each pre-signed URL, use Dropbox API to save the file into the Dropbox folder.
    Parallelize the Dropbox API calls, limiting to 20 concurrent tasks.
    """
    def save_file(key, url):
        """
        Save a single file to Dropbox and poll for its status.
        """
        parts = key.split('/')
        file_name = parts[-1]
        dropbox_destination = f"{dropbox_folder}/{file_name}"
        try:
            result = dbx.files_save_url(dropbox_destination, url)
            print(f"Initiated saving file to {dropbox_destination}: {result}")
            
            async_job_id = result.get_async_job_id()
            for _ in range(1800):  # Poll every 2 seconds, max 1 hour
                status = dbx.files_save_url_check_job_status(async_job_id)
                if status.is_complete():
                    return f"Success: {dropbox_destination}"
                time.sleep(2)
            return f"Timeout: {dropbox_destination}"
        except dropbox.exceptions.ApiError as err:
            return f"Error saving file {dropbox_destination}: {err}"

    # Use ThreadPoolExecutor to parallelize the API calls
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_key = {executor.submit(save_file, key, url): key for key, url in urls.items()}
        for future in as_completed(future_to_key):
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"Error processing file {future_to_key[future]}: {e}")

def main():
    # List S3 objects for the given prefix
    source_keys = list_source_objects(PREFIX)
    if not source_keys:
        print("No matching source objects found.")
        return

    print(f"Found {len(source_keys)} source object(s) for prefix {PREFIX}.")
    
    # Generate pre-signed URLs for the objects
    presigned_urls = generate_presigned_urls(source_keys)
    
    # Initialize Dropbox client
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    # Create a new Dropbox folder with a random 10-digit numeric name
    dropbox_folder = create_dropbox_folder(dbx)
    
    # Save files from pre-signed URLs into the Dropbox folder
    save_files_to_dropbox(dbx, dropbox_folder, presigned_urls)

if __name__ == "__main__":
    main()
