# handler.py
def handler(event, context):
    """ AWS S3 event handler """
    print("Event received.")
    for record in event['Records']:
        s3 = record['s3']
        bucket = s3['bucket']['name']
        key = s3['object']['key']

        print(f"New object {key} uploaded to {bucket}")
    return {"statusCode": 200}