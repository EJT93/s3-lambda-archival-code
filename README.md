## AWS S3 Log Archival Script

### Overview

This Python script automates the process of compressing and archiving log files stored in an AWS S3 bucket. It is designed to manage and optimize storage by compressing old log files into tar.gz archives, uploading them back to S3, and applying appropriate tags for lifecycle management. The script also ensures cleanliness and efficiency by cleaning up after itself, removing all temporary files and directories it creates during its execution.

### Features

- **Selective Downloading:** Downloads only relevant log files while ignoring already compressed archives and logs within a designated logging directory in S3.
- **Dynamic Compression:** Compresses downloaded files into a tar.gz archive, reducing storage space requirements.
- **Efficient Upload:** Uses `boto3` with a `TransferConfig` configuration to efficiently upload large files to S3.
- **Lifecycle Management:** Tags archives to enable automated lifecycle policies on S3, helping transition archives to cost-effective storage solutions like Glacier.
- **Clean Operation:** Cleans up all local temporary files and directories after operations to maintain a tidy file system.
- **Robust Logging:** Logs all actions to both the console and a file, and uploads this log to S3 for auditability and transparency.

### Usage

To use this script, ensure you have the appropriate AWS credentials configured on your machine or in your environment. The script uses the `default` profile from your AWS credentials file by default.

1. **Set up AWS CLI and boto3:**
   - Make sure AWS CLI is installed and configured correctly on your system.
   - Install `boto3` and related libraries using pip:
     ```
     pip install boto3
     ```

2. **Environment Preparation:**
   - Ensure your AWS user has sufficient permissions to access the S3 bucket, perform downloads and uploads, and apply tags to S3 objects.

3. **Script Execution:**
   - Run the script using Python 3. Ensure Python and all dependencies are correctly installed:
     ```
     python3 s3_archival_script.py
     ```

### Configuration

Modify the `bucket_name` and `s3_log_directory` variables in the script to match your S3 bucket name and the directory where you want to store logs:

```python
bucket_name = "your-bucket-name"
s3_log_directory = "archival-logs"
```

### Error Handling

The script includes comprehensive error handling to manage issues related to AWS credentials, network errors, and file permissions. It logs detailed error messages to assist in troubleshooting.

### Future Development

This script is currently tailored for manual execution or scheduled runs via cron jobs. Future development could involve:

- **Lambda Integration:** Refactoring the script for deployment as an AWS Lambda function, enabling it to run in response to event triggers (such as reaching a certain date or time, or when a bucket reaches a certain size).
- **Enhanced Filtering:** Adding more sophisticated file selection logic, allowing users to specify which files to archive based on criteria like file age or last modified date.
- **Performance Optimization:** Implementing parallel processing where possible to speed up file handling operations.

### Contributing

Contributions to enhance or extend the functionality of this script are welcome. Please fork the repository, make your changes, and submit a pull request.