import os
import glob
from google.cloud import storage


def upload_from_directory(local_directory_path: str, dest_bucket_name: str, dest_blob_name: str):
    rel_paths = glob.glob(local_directory_path + "/**", recursive=True)
    client = storage.Client()
    bucket = client.get_bucket(dest_bucket_name)
    for local_file in rel_paths:
        relative_path = os.path.relpath(local_file, local_directory_path)
        remote_path = dest_blob_name + "/" + relative_path
        if os.path.isfile(local_file):
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)
