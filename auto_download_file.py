import requests
import os
from tqdm import tqdm

from googleapiclient.discovery import build
from google.oauth2 import credentials

# Replace with your actual content
ACCESS_TOKEN = "YOUR_ACCESSS_TOKEN"
FILE_ID = "YOUR_FILE_ID"
OUTPUT_PATH = "/path/to/output/path"


def list_files_in_folder(folder_id):
    """
    Lists files and subfolders within a specified Google Drive folder.

    Args:
        folder_id: The ID of the Google Drive folder.

    Returns:
        A list of file/folder dictionaries, or an empty list if an error occurs.
        Each dictionary contains 'id', 'name', and 'mimeType' keys.
    """
    url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents&fields=files(id,name,mimeType)"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check for HTTP errors
    return response.json().get("files", [])


def get_google_drive_file_size_by_id_with_token(file_id, access_token=ACCESS_TOKEN):
    """
    Retrieves the size (in bytes) of a Google Drive file using its ID and an Access Token.

    Args:
        file_id: The ID of the Google Drive file.
        access_token: A valid Google Drive API Access Token.

    Returns:
        The file size in bytes (as an integer). Returns 0 if:
            - The file size is not found in the metadata.
            - The file is a Google Docs/Sheets/Slides file (which have no inherent size).
            - An error occurs during the API request.

    Raises:
        Exception: If the Google Drive API request fails for any other reason.
    """
    try:
        # Create Credentials object
        creds = credentials.Credentials(token=access_token)

        # Build the Google Drive API service
        service = build('drive', 'v3', credentials=creds)

        # Get file metadata (request only necessary fields)
        file_metadata = service.files().get(fileId=file_id, fields='size,name,mimeType,shared').execute()

        file_size = file_metadata.get('size')

        if file_size is not None:
            return int(file_size)
        else:
            # Handle Google Docs/Sheets/Slides (no size)
            if file_metadata.get("mimeType") and "google-apps" in file_metadata.get("mimeType"):
                print(f"File '{file_metadata.get('name')}' is a Google Docs/Sheets/Slides file (no file size).")
                return 0
            else:
                print(f"File size not found in metadata for file ID: {file_id}")
                return 0

    except Exception as e:
        print(f"An error occurred: {e}")
        return 0


def is_file_valid(file_path, expected_size):
    """
    Checks if a file exists locally and has the expected size.

    Args:
        file_path: The local path to the file.
        expected_size: The expected file size in bytes.

    Returns:
        True if the file exists and has the correct size, or if expected_size is 0.
        False otherwise.
    """
    if expected_size == 0:
        print("Unable to obtain file size or file is a Google Doc, skipping size check.")
        return True  # Skip if we can't get size or if it's a Google Doc/Sheet/Slide
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        if actual_size == expected_size:
            print(f"Skipping {file_path}, file already exists and size matches ({expected_size} bytes).")
            return True
        else:
            print(f"File {file_path} exists but size mismatch, expected {expected_size} bytes, actual {actual_size}. Re-downloading...")
            return False
    return False


def download_single_file(file_id, output_path):
    """
    Downloads a single file from Google Drive using its ID and saves it to the specified path.

    Args:
        file_id: The ID of the Google Drive file.
        output_path: The local path where the file should be saved.  This should
                     include the desired filename.
    """
    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    # Get file data stream
    response = requests.get(download_url, headers=headers, stream=True)
    response.raise_for_status() # Raise HTTPError for bad requests (4XX, 5XX)

    # Get total file size
    total_size = get_google_drive_file_size_by_id_with_token(file_id)

    # Check if the file has already been downloaded and has correct size
    if is_file_valid(output_path, total_size):
        return

    # Extract filename from output_path, or use a default if output_path is a directory
    file_name = os.path.basename(output_path)
    if not file_name: # Check if output_path is a directory
        print("Error: output_path must include a filename.")
        return
      
    # Download the file and show progress
    with open(output_path, "wb") as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name, ncols=100) as pbar:
            for data in response.iter_content(chunk_size=1024):
                if data:  # Ensure data is not empty
                    f.write(data)
                    pbar.update(len(data))

    print(f"Downloaded {file_name}")


if __name__ == '__main__':
    download_single_file(FILE_ID, OUTPUT_PATH)
    print("Download completed!")