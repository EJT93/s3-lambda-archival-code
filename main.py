import tarfile
import gzip
import os
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import logging
import time

# Setup logging to print to both file and stdout
log_filename = '/tmp/s3_compression_log.txt'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),
                        logging.StreamHandler()
                    ])

def configure_aws():
    """Configure AWS SDK and return an S3 resource. Includes  c error handling."""
    try:
        # Attempt to create a session using an AWS CLI profile name
        session = boto3.Session(profile_name='default')
        # Creating S3 resource from the session
        s3 = session.resource('s3')
        logging.info("AWS SDK configured successfully.")
        return s3
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials issue: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise

def download_files(s3, bucket_name, ignore_patterns=None):
    """Download all files from the S3 bucket except for ignored patterns."""
    if ignore_patterns is None:
        ignore_patterns = []
    
    bucket = s3.Bucket(bucket_name)
    local_dir = '/tmp/s3_files/'
    os.makedirs(local_dir, exist_ok=True)
    
    for obj in bucket.objects.all():
        if any(obj.key.endswith(pattern) for pattern in ignore_patterns):
            logging.info(f"Skipping {obj.key} due to ignore pattern.")
            continue  # Skip ignored files

        local_file_path = os.path.join(local_dir, obj.key)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        bucket.download_file(obj.key, local_file_path)
        logging.info(f"Downloaded {obj.key} to {local_file_path}")
    
    return local_dir

def cleanup_local_resources():
    """Remove local temporary files and directories."""
    # Paths of temporary files and directories created by the script
    temp_paths = [
        '/tmp/s3_files/',  # Directory where S3 files are downloaded
        '/tmp/weekly-archive.tar.gz',  # The compressed tar file
        '/tmp/s3_compression_log.txt'  # Log file
    ]
    
    for path in temp_paths:
        if os.path.isdir(path):
            # Remove directory and all its content
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(path)
        elif os.path.isfile(path):
            # Remove file
            os.remove(path)
    
    logging.info("Cleaned up all local temporary resources.")

def create_tar_gz_archive(source_dir, output_filename):
    """Create a tarball from the directory and compress it using gzip."""
    tar_path = f"{output_filename}.tar"
    gz_path = f"{output_filename}.tar.gz"
    with tarfile.open(tar_path, 'w') as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    with open(tar_path, 'rb') as tar_file:
        with gzip.open(gz_path, 'wb') as gz_file:
            gz_file.writelines(tar_file)
    os.remove(tar_path)
    logging.info(f"Created archive {gz_path}")
    return gz_path

def upload_archive_to_s3(s3, bucket_name, file_path, archive_name):
    """Upload the created archive to S3."""
    config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10,
                            multipart_chunksize=1024 * 25, use_threads=True)
    s3.meta.client.upload_file(file_path, bucket_name, archive_name,
                               ExtraArgs={'ContentType': 'application/gzip'},
                               Config=config)
    logging.info(f"Uploaded {archive_name} to S3 bucket {bucket_name}")

def tag_archive(s3, bucket_name, archive_name, tags):
    """Apply tags to the uploaded S3 object."""
    tagging = {'TagSet': [{'Key': str(k), 'Value': str(v)} for k, v in tags.items()]}
    s3.meta.client.put_object_tagging(Bucket=bucket_name, Key=archive_name, Tagging=tagging)
    logging.info(f"Tagged {archive_name} with {tags}")

def calculate_size_savings(original_size, compressed_size):
    """Calculate the size savings and return it."""
    savings = original_size - compressed_size
    savings_percent = (savings / original_size) * 100
    return savings, savings_percent

def upload_log_to_s3(s3, bucket_name, local_log_path, s3_log_directory, timestamp):
    """Upload the log file to the specified S3 path."""
    s3_log_path = f"{s3_log_directory}/python-log-{timestamp}.txt"
    s3.meta.client.upload_file(local_log_path, bucket_name, s3_log_path)
    logging.info(f"Uploaded log file to S3 at {s3_log_path}")

def main():
    bucket_name = "my-app-090823"
    s3_log_directory = "archival-logs"
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    s3 = configure_aws()
    
    # Define patterns to ignore when downloading files
    ignore_patterns = [".tar.gz", s3_log_directory + "/"]
    
    # Download files from S3 bucket
    local_dir = download_files(s3, bucket_name, ignore_patterns=ignore_patterns)
    
    # Create tar.gz archive from downloaded files
    archive_path = create_tar_gz_archive(local_dir, '/tmp/weekly-archive')
    archive_name = f"weekly-archive-{timestamp}.tar.gz"
    
    # Upload the archive to the S3 bucket
    upload_archive_to_s3(s3, bucket_name, archive_path, archive_name)
    
    # Tag the uploaded archive
    tag_archive(s3, bucket_name, archive_name, {"ArchiveStatus": "ReadyForGlacier"})
    
    # After all operations, upload the log file to S3
    upload_log_to_s3(s3, bucket_name, log_filename, s3_log_directory, timestamp)
    
    # Clean up local files and directories after all other operations are completed
    cleanup_local_resources()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred in the main execution: {str(e)}")
        # Attempt to clean up even if an error occurs
        cleanup_local_resources()