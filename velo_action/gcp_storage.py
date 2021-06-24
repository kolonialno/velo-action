import os
import glob
import logging

logger = logging.getLogger(name="gcp_storage")


def upload_from_directory(client, path, dest_bucket_name, dest_blob_name):

    rel_paths = []
    for p in path.rglob("*"):
        rel_paths.append(p)

    bucket = client.get_bucket(dest_bucket_name)

    for local_file in rel_paths:
        relative_path = os.path.relpath(local_file, path)
        remote_path = os.path.join(dest_blob_name, relative_path)
        if os.path.isfile(local_file):
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)
