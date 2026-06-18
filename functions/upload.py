import re
import requests
import json

# ========== 🔑 DIRECT TOKEN ==========
HF_TOKEN = "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"          # <-- APNA TOKEN DAAL
BUCKET_NAME = "gopallikehack/Hitek-storage"

def extract_file_id(drive_url):
    patterns = [r'/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)']
    for p in patterns:
        m = re.search(p, drive_url)
        if m:
            return m.group(1)
    return None

def download_from_drive(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        r = requests.get(url, stream=True, timeout=60)
        if 'confirm' in r.text:
            c = re.search(r'confirm=([^&]+)', r.text)
            if c:
                url = f"https://drive.google.com/uc?export=download&confirm={c.group(1)}&id={file_id}"
                r = requests.get(url, stream=True, timeout=120)
        if r.status_code == 200:
            filename = "file.zip"
            if 'content-disposition' in r.headers:
                cd = r.headers['content-disposition']
                if 'filename=' in cd:
                    filename = cd.split('filename=')[-1].strip('"')
            return r.content, filename
        return None, None
    except:
        return None, None

def upload_to_hf(content, filename):
    url = f"https://huggingface.co/api/datasets/{BUCKET_NAME}/upload/{filename}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        r = requests.put(url, headers=headers, data=content)
        return r.status_code == 200
    except:
        return False

def handler(event, context):
    if event['httpMethod'] != 'POST':
        return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}
    try:
        body = json.loads(event['body'])
        url = body.get('url', '').strip()
        if not url:
            return {'statusCode': 400, 'body': json.dumps({'success': False, 'error': 'No URL'})}
        file_id = extract_file_id(url)
        if not file_id:
            return {'statusCode': 400, 'body': json.dumps({'success': False, 'error': 'Invalid link'})}
        content, filename = download_from_drive(file_id)
        if not content:
            return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': 'Download failed'})}
        if upload_to_hf(content, filename):
            link = f"https://huggingface.co/datasets/{BUCKET_NAME}/blob/main/{filename}"
            return {'statusCode': 200, 'body': json.dumps({'success': True, 'filename': filename, 'size': len(content), 'link': link})}
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': 'Upload to HF failed'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}