import requests
import os
from tqdm import tqdm

from googleapiclient.discovery import build
from google.oauth2 import credentials

# Replace with your actual content
ACCESS_TOKEN = "YOUR_ACCESSS_TOKEN"
FOLDER_ID = "YOUR_FOLDER_ID"
OUTPUT_PATH = "/path/to/output/root"


def list_files_in_folder(folder_id):
    """
    Lists files and subfolders within a specified Google Drive folder.

    Args:
        folder_id: The ID of the Google Drive folder.

    Returns:
        A list of file/folder dictionaries, or an empty list if an error occurs.  Each
        dictionary contains 'id', 'name', and 'mimeType' keys.
    """
    url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents&fields=files(id,name,mimeType)"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    return response.json().get("files", [])  # Default to an empty list if 'files' key is missing


def get_google_drive_file_size_by_id_with_token(file_id, access_token=ACCESS_TOKEN):
    """
    Retrieves the size (in bytes) of a Google Drive file using its ID and an Access Token.

    Args:
        file_id: The ID of the Google Drive file.
        access_token: A valid Google Drive API Access Token.

    Returns:
        The file size in bytes (as an integer).  Returns 0 if:
            - The file size is not found in the metadata.
            - The file is a Google Docs/Sheets/Slides file (which have no inherent size).
            - An error occurs during the API request.

    Raises:
        #  The original code had a bare 'Exception', which is generally bad practice.
        #  It's better to catch specific exceptions if you know what they might be.
        #  However, since we're just printing the error and returning 0, it's
        #  acceptable in this case to keep it broad, but we document it.
        Exception:  If the Google Drive API request fails for any other reason.
    """
    try:
        # Create Credentials object using the Access Token
        creds = credentials.Credentials(token=access_token)

        # Build the Google Drive API service
        service = build('drive', 'v3', credentials=creds)

        # Get file metadata (request only necessary fields for efficiency)
        file_metadata = service.files().get(fileId=file_id, fields='size, name, mimeType, shared').execute()

        file_size = file_metadata.get('size')

        if file_size is not None:
            return int(file_size)  # Convert to integer for consistency
        else:
            # Google Docs/Sheets/Slides don't have a 'size' property.
            if file_metadata.get("mimeType") and "google-apps" in file_metadata.get("mimeType"):
                print(f"File '{file_metadata.get('name')}' is a Google Docs/Sheets/Slides file (no file size).")
                return 0  # Return 0 for Google Docs/Sheets/Slides
            else:
                print(f"File size not found in metadata for file ID: {file_id}")
                return 0  # Return 0 if size is missing for any other reason

    except Exception as e:
        print(f"An error occurred: {e}")  # Log the exception for debugging
        return 0  # Return 0 on error


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
        return True  # Skip size check if we couldn't get the size or it's a Google Doc
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        if actual_size == expected_size:
            print(f"Skipping {file_path}, file already exists and size matches ({expected_size} bytes).")
            return True  # File exists and size matches
        else:
            print(f"File {file_path} exists but size mismatch, expected {expected_size} bytes, actual {actual_size} bytes. Re-downloading...")
            return False  # File exists, but size doesn't match
    return False  # File doesn't exist


def download_file(file_id, file_name, output_path):
    """
    Downloads a file from Google Drive and displays a progress bar.

    Args:
        file_id: The ID of the Google Drive file.
        file_name: The name of the file.
        output_path: The local directory to save the file.
    """
    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    # Get the file data stream
    response = requests.get(download_url, headers=headers, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    # Get the total file size
    total_size = get_google_drive_file_size_by_id_with_token(file_id)

    # File save path
    file_path = os.path.join(output_path, file_name)

    # Check if the file has already been downloaded and the size is correct
    if is_file_valid(file_path, total_size):
        return  # Skip download if file is valid

    # Write the file in binary mode and display download progress
    with open(file_path, "wb") as f:
        # Use tqdm to display the download progress of a single file (with percentage)
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name, ncols=100) as pbar:
            for data in response.iter_content(chunk_size=1024):  # Read in 1KB chunks
                if data:  # Ensure data is not empty
                    f.write(data)
                    pbar.update(len(data))  # Update single file progress bar

    print(f"Downloaded {file_name}")


def traverse_folder(folder_id, output_path):
    """
    Recursively traverses a Google Drive folder and downloads all files (excluding Google Docs/Sheets/Slides).

    Args:
        folder_id: The ID of the Google Drive folder.
        output_path: The local directory to save files and subfolders.
    """
    # Get files and subfolders in the current folder
    files = list_files_in_folder(folder_id)

    # Iterate through files and folders
    for file in files:
        file_id = file["id"]
        file_name = file["name"]
        mime_type = file["mimeType"]

        # If it's a folder, recursively traverse it
        if mime_type == "application/vnd.google-apps.folder":
            # Create a local folder
            folder_path = os.path.join(output_path, file_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            # Recursively traverse the subfolder
            traverse_folder(file_id, folder_path)
        else:
            # If it's a file, download it and show progress
            download_file(file_id, file_name, output_path)


if __name__ == '__main__':
    # Create output folder if it doesn't exist
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Start traversing and downloading
    traverse_folder(FOLDER_ID, OUTPUT_PATH)

    print("Download completed!")