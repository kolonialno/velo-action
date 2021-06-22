import os
import glob
from google.cloud import storage

# def authenticate_gcp(key):
#     credentials, _ = google.auth.default()
#     credentials.refresh(gauth_requests.Request())
#     if getattr(credentials, "id_token", None) is None:
#         credentials = compute_engine.IDTokenCredentials(gauth_requests.Request(), "my-audience", use_metadata_identity_endpoint=True)
#         credentials.refresh(gauth_requests.Request())
#         headers = {"authorization": f"Bearer {credentials.token}"}
#     else:
#         headers = {"authorization": f"Bearer {credentials.id_token}"}
#     # print(headers)  # This header dict can be used to make authorized requests!


def upload_from_directory(local_directory_path: str, dest_bucket_name: str, dest_blob_name: str, project: str = "nube-velo-prod"):

    try:
        client = storage.Client()
    except Exception as e:
        print(e)
        raise

    rel_paths = glob.glob(local_directory_path + "/**", recursive=True)
    bucket = client.get_bucket(dest_bucket_name)

    for local_file in rel_paths:
        relative_path = os.path.relpath(local_file, local_directory_path)
        remote_path = dest_blob_name + "/" + relative_path
        if os.path.isfile(local_file):
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)


def github_action_output(key, value):
    os.system(f'echo "::set-output name={key}::{value}"')
