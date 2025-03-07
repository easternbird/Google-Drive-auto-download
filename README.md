# Google-Drive-auto-download

This repositories is used for downloading files from Google Drive automatically, especially when it is inconvenient to download files from a folder.

## Environment Setup

Downloading following packages:

```
pip install google-api-python-client
```


Then you need to get `FOLDER_ID` from your link, you can obtain this from your sharelink which is usually in the format of `https://drive.google.com/drive/folders/FOLDDER_ID?usp=drive_link`. For instance, if your sharelink is https://drive.google.com/drive/folders/1jGt10bwTbhEZuGXLyvrCuxOIAl2qQ1FS?usp=drive_link, then the `FOLDER_ID` is `1jGt10bwTbhEZuGXLyvrCuxOIAl2qQ1FS`.


Next you should get your `ACCESS_TOKEN`. First login [Google Oauth Playground](https://developers.google.com/oauthplayground/), choose `https://www.googleapis.com/auth/drive.readonly` from `Drive API v3` and click `Authorize APIs`.

![image](https://github.com/user-attachments/assets/5f98ca0c-7677-4f3a-8ae7-2472f8c72ae1)


Then you can get your access token in Step 2 after logging in your account. Remember to click `Exchange authorization for code for tokens`. If your website goes to Step 3 automatically, just click back to Step 2.


![image](https://github.com/user-attachments/assets/f107917a-0e03-47ef-adbd-376e5570c08c)

* **Note**: the access token will expire in `3600s`, so if your file is ultra big, you need to get your access token for many times. If you want to get access token automatically, you need to apply API from Google Cloud, this is much more complex, and this takes a much slower speed when downloading.


Finally you can download automatically by replacing information in script `auto_download.py`, that is your `ACCESS_TOKEN`, `FOLDER_ID` and `OUTPUT_PATH`, `OUTPUT_PATH` is the root of your download.

```python
ACCESS_TOKEN = "YOUR_ACCESSS_TOKEN"
FOLDER_ID = "YOUR_FOLDER_ID"
OUTPUT_PATH = "/path/to/output/root"
```
  
