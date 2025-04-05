# S3-to-Dropbox
## Python script to transfer objects directly from AWS S3 to Dropbox. No intermediate local download/upload needed.

### Setup and use.
1. Configure the AWS CLI. Ensure you are authenticated with an active session and AWS credentials are available via environment variables or an active profile. Your profile must have read access to the S3 bucket you're attempting to access and permissions to create pre-signed URLs.
2. Update the `AWS_REGION`, `S3_BUCKET`, and `PREFIX` configuration constants.
3. Configure a Dropbox Application with `files.content.write` scope. Generate Dropbox Access Token in [DBX App Console](https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps) and add it to the `DROPBOX_ACCESS_TOKEN` constant.
4. Install `boto3` and `dropbox` packages.
5. Run the script `python main.py`

### Script Processing Steps:
1. Collect S3 objects matching a defined prefix or key
2. Generate pre-signed URLs for those objects
3. Initialize Dropbox Connection and create a new folder
4. Save pre-signed URLs to Dropbox and poll Dropbox API for status. This is done with 20x parallelization and a 30 minute timeout.