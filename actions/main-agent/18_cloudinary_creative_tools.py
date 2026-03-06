# ============================================
import requests, json, hashlib, time, base64
from urllib.parse import urlencode
from datetime import datetime

PLATFORM_PRESETS = {
    'instagram_story': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'Instagram'},
    'instagram_feed': {'width': 1080, 'height': 1080, 'ratio': '1:1', 'platform': 'Instagram'},
    'tiktok': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'TikTok'},
    'youtube_shorts': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'YouTube'},
    'youtube_standard': {'width': 1920, 'height': 1080, 'ratio': '16:9', 'platform': 'YouTube'},
    'facebook_feed': {'width': 1080, 'height': 1080, 'ratio': '1:1', 'platform': 'Facebook'},
    'linkedin': {'width': 1200, 'height': 628, 'ratio': '1.91:1', 'platform': 'LinkedIn'},
    'leaderboard_728x90': {'width': 728, 'height': 90, 'platform': 'Display', 'requires_gen_fill': True},
    'skyscraper_160x600': {'width': 160, 'height': 600, 'platform': 'Display', 'requires_gen_fill': True},
    'medium_rectangle_300x250': {'width': 300, 'height': 250, 'platform': 'Display', 'requires_gen_fill': True},
    'billboard_970x250': {'width': 970, 'height': 250, 'platform': 'Display', 'requires_gen_fill': True},
}

def get_credentials():
    return {'cloud_name': secrets.get('CLOUDINARY_CLOUD_NAME'), 'api_key': secrets.get('CLOUDINARY_API_KEY'), 'api_secret': secrets.get('CLOUDINARY_API_SECRET')}

def generate_signature(params, api_secret):
    sorted_params = sorted(params.items())
    to_sign = '&'.join([f"{k}={v}" for k, v in sorted_params if v is not None]) + api_secret
    return hashlib.sha256(to_sign.encode()).hexdigest()

def build_transform_url(cloud_name, public_id, resource_type='image', transformations=None):
    base_url = f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload"
    if transformations:
        transform_str = ','.join([f"{k}_{v}" for k, v in transformations.items() if v])
        return f"{base_url}/{transform_str}/{public_id}"
    return f"{base_url}/{public_id}"

def upload_asset(file_url, resource_type='image', folder='cav-assets', public_id=None, tags=None):
    creds = get_credentials()
    if not creds['cloud_name']: return {'status': 'error', 'message': 'Cloudinary credentials not configured'}
    timestamp = int(time.time())
    params = {'timestamp': timestamp, 'folder': folder}
    if public_id: params['public_id'] = public_id
    if tags: params['tags'] = ','.join(tags) if isinstance(tags, list) else tags
    params['signature'] = generate_signature(params, creds['api_secret'])
    params['api_key'] = creds['api_key']; params['file'] = file_url
    try:
        response = requests.post(f"https://api.cloudinary.com/v1_1/{creds['cloud_name']}/{resource_type}/upload", data=params, timeout=120)
        result = response.json()
        if 'error' in result: return {'status': 'error', 'message': result['error'].get('message')}
        return {'status': 'success', 'public_id': result.get('public_id'), 'url': result.get('secure_url'), 'width': result.get('width'), 'height': result.get('height'), 'format': result.get('format'), 'bytes': result.get('bytes')}
    except Exception as e: return {'status': 'error', 'message': str(e)}

def resize_image(public_id, width, height, crop='fill', gravity='auto', quality='auto', format='auto', background=None, use_gen_fill=False, gen_fill_prompt=None):
    creds = get_credentials()
    transformations = {'w': width, 'h': height, 'c': crop, 'g': gravity, 'q': quality, 'f': format}
    if use_gen_fill:
        transformations['b'] = f"gen_fill:{gen_fill_prompt}" if gen_fill_prompt else 'gen_fill'
        transformations['c'] = 'pad'
    elif background:
        transformations['b'] = 'blurred:400:15' if background == 'blur' else background
    return {'status': 'success', 'url': build_transform_url(creds['cloud_name'], public_id, 'image', transformations), 'dimensions': {'width': width, 'height': height}, 'used_gen_fill': use_gen_fill}

def run(action, **kwargs):
    if action == 'upload_image': return upload_asset(kwargs.get('file_url'), 'image', kwargs.get('folder', 'cav-assets'), kwargs.get('public_id'), kwargs.get('tags'))
    elif action == 'upload_video': return upload_asset(kwargs.get('file_url'), 'video', kwargs.get('folder', 'cav-assets'), kwargs.get('public_id'), kwargs.get('tags'))
    elif action == 'resize_image': return resize_image(kwargs.get('public_id'), kwargs.get('width'), kwargs.get('height'), kwargs.get('crop', 'fill'), kwargs.get('gravity', 'auto'), kwargs.get('quality', 'auto'), kwargs.get('format', 'auto'), kwargs.get('background'), kwargs.get('use_gen_fill', False), kwargs.get('gen_fill_prompt'))
    elif action == 'get_platform_presets': return {'status': 'success', 'presets': PLATFORM_PRESETS}
    elif action == 'resize_for_platform':
        preset = PLATFORM_PRESETS.get(kwargs.get('platform_preset'))
        if not preset: return {'status': 'error', 'message': f"Unknown preset", 'available': list(PLATFORM_PRESETS.keys())}
        return resize_image(kwargs.get('public_id'), preset['width'], preset['height'], use_gen_fill=preset.get('requires_gen_fill', False))
    elif action == 'batch_resize':
        results = {}
        for p in kwargs.get('platform_presets', []):
            preset = PLATFORM_PRESETS.get(p)
            if preset: results[p] = resize_image(kwargs.get('public_id'), preset['width'], preset['height'], use_gen_fill=preset.get('requires_gen_fill', False))
        return {'status': 'success', 'results': results, 'total_variants': len(results)}
    else: return {'status': 'error', 'message': f"Unknown action: {action}"}
