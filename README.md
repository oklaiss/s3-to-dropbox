# S3-to-Dropbox

### Python script to transfer objects from AWS S3 to Dropbox without a local download.

1. Collect S3 objects matching a defined prefix or key
2. Generate pre-signed URLs for those objects
3. Initialize Dropbox Connection
4. Create a Dropbox folder
5. Save pre-signed URLs to Dropbox and poll Dropbox API for status
