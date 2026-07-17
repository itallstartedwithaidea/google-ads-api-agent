# Cloudinary Creative Tools — image/video transforms with Gemini-vs-gen_fill routing
import time
import requests

# =============================================================================
# GEMINI-COMPATIBLE ASPECT RATIOS
# =============================================================================

GEMINI_VALID_RATIOS = {
    '1:1': 1.0,
    '5:4': 1.25,
    '4:3': 1.333,
    '3:2': 1.5,
    '2:3': 0.667,
    '3:4': 0.75,
    '4:5': 0.8,
    '9:16': 0.5625,
    '16:9': 1.778,
    '21:9': 2.333
}

GEMINI_TOLERANCE = 0.05

# =============================================================================
# PLATFORM PRESETS
# =============================================================================

PLATFORM_PRESETS = {
    # INSTAGRAM
    'instagram_feed_square': {'width': 1080, 'height': 1080, 'ratio': '1:1', 'platform': 'Instagram', 'placement': 'Feed Square', 'gemini_compatible': True},
    'instagram_feed_portrait': {'width': 1080, 'height': 1350, 'ratio': '4:5', 'platform': 'Instagram', 'placement': 'Feed Portrait', 'gemini_compatible': True},
    'instagram_feed_tall': {'width': 1080, 'height': 1440, 'ratio': '3:4', 'platform': 'Instagram', 'placement': 'Feed Tall (2025 Grid)', 'gemini_compatible': True},
    'instagram_story': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'Instagram', 'placement': 'Story', 'gemini_compatible': True},
    'instagram_reel': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'Instagram', 'placement': 'Reel', 'gemini_compatible': True},

    # FACEBOOK
    'facebook_feed_square': {'width': 1080, 'height': 1080, 'ratio': '1:1', 'platform': 'Facebook', 'placement': 'Feed Square', 'gemini_compatible': True},
    'facebook_feed_portrait': {'width': 1080, 'height': 1350, 'ratio': '4:5', 'platform': 'Facebook', 'placement': 'Feed Portrait', 'gemini_compatible': True},
    'facebook_story': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'Facebook', 'placement': 'Story', 'gemini_compatible': True},
    'facebook_feed_landscape': {'width': 1200, 'height': 630, 'ratio': '1.91:1', 'platform': 'Facebook', 'placement': 'Feed Landscape', 'gemini_compatible': False, 'requires_gen_fill': True},

    # TIKTOK
    'tiktok': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'TikTok', 'placement': 'Video/Stories', 'gemini_compatible': True},

    # YOUTUBE
    'youtube_thumbnail': {'width': 1280, 'height': 720, 'ratio': '16:9', 'platform': 'YouTube', 'placement': 'Thumbnail', 'gemini_compatible': True},
    'youtube_shorts': {'width': 1080, 'height': 1920, 'ratio': '9:16', 'platform': 'YouTube', 'placement': 'Shorts', 'gemini_compatible': True},

    # LINKEDIN
    'linkedin_post': {'width': 1200, 'height': 627, 'ratio': '1.91:1', 'platform': 'LinkedIn', 'placement': 'Post/Link', 'gemini_compatible': False, 'requires_gen_fill': True},
    'linkedin_post_square': {'width': 1200, 'height': 1200, 'ratio': '1:1', 'platform': 'LinkedIn', 'placement': 'Post Square', 'gemini_compatible': True},

    # TWITTER/X
    'x_instream': {'width': 1600, 'height': 900, 'ratio': '16:9', 'platform': 'X/Twitter', 'placement': 'In-Stream Image', 'gemini_compatible': True},

    # PINTEREST
    'pinterest_standard': {'width': 1000, 'height': 1500, 'ratio': '2:3', 'platform': 'Pinterest', 'placement': 'Standard Pin', 'gemini_compatible': True},

    # GDN - Google Display Network (requires Cloudinary gen_fill)
    'gdn_leaderboard': {'width': 728, 'height': 90, 'ratio': '8.09:1', 'platform': 'GDN', 'placement': 'Leaderboard', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_medium_rectangle': {'width': 300, 'height': 250, 'ratio': '1.2:1', 'platform': 'GDN', 'placement': 'Medium Rectangle', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_wide_skyscraper': {'width': 160, 'height': 600, 'ratio': '0.27:1', 'platform': 'GDN', 'placement': 'Wide Skyscraper', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_mobile_leaderboard': {'width': 320, 'height': 50, 'ratio': '6.4:1', 'platform': 'GDN', 'placement': 'Mobile Leaderboard', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_half_page': {'width': 300, 'height': 600, 'ratio': '0.5:1', 'platform': 'GDN', 'placement': 'Half-Page', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_billboard': {'width': 970, 'height': 250, 'ratio': '3.88:1', 'platform': 'GDN', 'placement': 'Billboard', 'gemini_compatible': False, 'requires_gen_fill': True},
    'gdn_square': {'width': 250, 'height': 250, 'ratio': '1:1', 'platform': 'GDN', 'placement': 'Square', 'gemini_compatible': True},
}

PRESET_PACKAGES = {
    'instagram_complete': {
        'name': 'Instagram Complete',
        'presets': ['instagram_feed_square', 'instagram_feed_portrait', 'instagram_feed_tall', 'instagram_story', 'instagram_reel'],
        'description': 'All Instagram formats including the new 2025 grid'
    },
    'facebook_complete': {
        'name': 'Facebook Complete',
        'presets': ['facebook_feed_square', 'facebook_feed_landscape', 'facebook_feed_portrait', 'facebook_story'],
        'description': 'All Facebook feed and story formats'
    },
    'tiktok_reels': {
        'name': 'TikTok & Reels',
        'presets': ['tiktok', 'instagram_reel', 'youtube_shorts', 'facebook_story'],
        'description': 'Vertical video formats for all major platforms'
    },
    'gdn_essential': {
        'name': 'GDN Essential',
        'presets': ['gdn_medium_rectangle', 'gdn_leaderboard', 'gdn_wide_skyscraper', 'gdn_mobile_leaderboard'],
        'description': 'Most common Google Display Network sizes'
    },
    'multi_platform_essential': {
        'name': 'Multi-Platform Essential',
        'presets': ['instagram_feed_square', 'instagram_feed_portrait', 'instagram_story', 'facebook_feed_square', 'linkedin_post', 'x_instream', 'pinterest_standard'],
        'description': 'Essential sizes for all major social platforms'
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_credentials():
    """Get Cloudinary credentials from secrets."""
    return {
        'cloud_name': secrets.get('CLOUDINARY_CLOUD_NAME'),
        'api_key': secrets.get('CLOUDINARY_API_KEY'),
        'api_secret': secrets.get('CLOUDINARY_API_SECRET')
    }

def generate_filename(prefix='cloudinary', extension='png'):
    """Generate a unique filename with timestamp."""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}.{extension}"

def save_to_file(data, prefix='cloudinary', extension='png'):
    """Save binary data to file and return filename."""
    filename = generate_filename(prefix, extension)
    with open(filename, 'wb') as f:
        f.write(data)
    return filename

def is_gemini_compatible(width, height):
    """Check if dimensions are Gemini-compatible."""
    if width <= 0 or height <= 0:
        return {'is_compatible': False, 'ai_service': 'cloudinary', 'requires_gen_fill': True}

    numeric_ratio = width / height

    for ratio_name, ratio_value in GEMINI_VALID_RATIOS.items():
        diff = abs(numeric_ratio - ratio_value) / ratio_value
        if diff <= GEMINI_TOLERANCE:
            return {
                'is_compatible': True,
                'matched_ratio': ratio_name,
                'ai_service': 'gemini',
                'requires_gen_fill': False
            }

    return {
        'is_compatible': False,
        'numeric_ratio': round(numeric_ratio, 4),
        'ai_service': 'cloudinary',
        'requires_gen_fill': True
    }

# =============================================================================
# CLOUDINARY URL BUILDER (No API calls - just builds transform URLs)
# =============================================================================

def build_image_transform_url(cloud_name, public_id, width, height, 
                               use_gen_fill=False, gravity='center', quality='auto:best'):
    """
    Build Cloudinary transformation URL for images.
    Matches the Baymax — Creative Innovate approach.
    """
    transformations = [
        f'w_{width}',
        f'h_{height}',
    ]

    if use_gen_fill:
        # AI Generative Fill - pad mode to maintain content
        transformations.extend([
            'c_pad',
            f'g_{gravity}',
            'b_gen_fill',  # The magic!
        ])
    else:
        # Standard fill/crop
        transformations.extend([
            'c_fill',
            f'g_{gravity}',
        ])

    transformations.extend([
        f'q_{quality}',
        'f_auto'
    ])

    transform_str = ','.join(transformations)
    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{transform_str}/{public_id}"

def build_video_transform_url(cloud_name, public_id, width=None, height=None,
                               aspect_ratio=None, crop='fill', gravity='auto',
                               start_offset=None, end_offset=None, effect=None):
    """
    Build Cloudinary transformation URL for videos.
    Matches the Baymax — Creative Innovate approach.
    """
    transformations = []

    # Time-based transforms must come first
    if start_offset is not None:
        transformations.append(f'so_{start_offset}')
    if end_offset is not None:
        transformations.append(f'eo_{end_offset}')

    # Effects
    if effect:
        transformations.append(f'e_{effect}')

    # Resize
    if aspect_ratio:
        transformations.append(f'ar_{aspect_ratio}')
    if width:
        transformations.append(f'w_{width}')
    if height:
        transformations.append(f'h_{height}')

    # Crop mode
    transformations.append(f'c_{crop}')
    transformations.append(f'g_{gravity}')
    transformations.append('q_auto')

    transform_str = ','.join(transformations)
    return f"https://res.cloudinary.com/{cloud_name}/video/upload/{transform_str}/{public_id}"

# =============================================================================
# UPLOAD FUNCTIONS
# =============================================================================

def upload_with_unsigned_preset(file_url, resource_type='image', folder='cav-assets', public_id=None):
    """
    Upload using unsigned preset (like the browser tool does).
    Requires 'cav_unsigned' preset configured in Cloudinary.
    """
    creds = get_credentials()

    if not creds['cloud_name']:
        return {'status': 'error', 'message': 'Cloudinary cloud_name not configured'}

    upload_url = f"https://api.cloudinary.com/v1_1/{creds['cloud_name']}/{resource_type}/upload"

    data = {
        'file': file_url,
        'upload_preset': 'cav_unsigned',
        'folder': folder,
    }

    if public_id:
        data['public_id'] = public_id

    try:
        response = requests.post(upload_url, data=data, timeout=120)
        result = response.json()

        if 'error' in result:
            return {'status': 'error', 'message': result['error'].get('message', 'Upload failed')}

        return {
            'status': 'success',
            'public_id': result.get('public_id'),
            'url': result.get('secure_url'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'resource_type': result.get('resource_type'),
            'bytes': result.get('bytes')
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# =============================================================================
# RESIZE FUNCTIONS
# =============================================================================

def resize_image_with_gen_fill(public_id, width, height, gravity='center', 
                                quality='auto:best', save_to_file_flag=True):
    """
    Resize image using AI Generative Fill.
    Matches resizeImageWithGenFill from Baymax — Creative Innovate.
    """
    creds = get_credentials()

    if not creds['cloud_name']:
        return {'status': 'error', 'message': 'Cloudinary cloud_name not configured'}

    # Build the transform URL
    url = build_image_transform_url(
        creds['cloud_name'], 
        public_id, 
        width, 
        height,
        use_gen_fill=True,
        gravity=gravity,
        quality=quality
    )

    result = {
        'status': 'success',
        'url': url,
        'public_id': public_id,
        'dimensions': {'width': width, 'height': height},
        'used_gen_fill': True
    }

    # Download and save to file if requested
    if save_to_file_flag:
        try:
            response = requests.get(url, timeout=60)
            if response.ok:
                content_type = response.headers.get('content-type', 'image/png').split(';')[0]
                ext = 'png' if 'png' in content_type else 'jpg'
                filename = save_to_file(response.content, 'cloudinary_genfill', ext)
                result['filename'] = filename
            else:
                result['download_error'] = f'HTTP {response.status_code}'
        except Exception as e:
            result['download_error'] = str(e)

    return result

def resize_video(public_id, width=None, height=None, aspect_ratio=None,
                 crop='fill', gravity='auto', start_offset=None, end_offset=None, effect=None):
    """
    Resize video with smart cropping.
    Matches resizeVideo from Baymax — Creative Innovate.
    """
    creds = get_credentials()

    if not creds['cloud_name']:
        return {'status': 'error', 'message': 'Cloudinary cloud_name not configured'}

    url = build_video_transform_url(
        creds['cloud_name'],
        public_id,
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        crop=crop,
        gravity=gravity,
        start_offset=start_offset,
        end_offset=end_offset,
        effect=effect
    )

    return {
        'status': 'success',
        'url': url,
        'public_id': public_id,
        'dimensions': {'width': width, 'height': height, 'aspect_ratio': aspect_ratio}
    }

def resize_for_platform(public_id, platform_preset, resource_type='image', 
                        gravity='center', save_to_file_flag=True):
    """Resize asset for a specific platform preset."""
    if platform_preset not in PLATFORM_PRESETS:
        return {
            'status': 'error',
            'message': f"Unknown preset: {platform_preset}",
            'available_presets': list(PLATFORM_PRESETS.keys())
        }

    preset = PLATFORM_PRESETS[platform_preset]

    if resource_type == 'image':
        use_gen_fill = preset.get('requires_gen_fill', False)
        if use_gen_fill:
            return resize_image_with_gen_fill(
                public_id, 
                preset['width'], 
                preset['height'],
                gravity=gravity,
                save_to_file_flag=save_to_file_flag
            )
        else:
            # Standard resize (no gen_fill)
            creds = get_credentials()
            url = build_image_transform_url(
                creds['cloud_name'],
                public_id,
                preset['width'],
                preset['height'],
                use_gen_fill=False,
                gravity=gravity
            )
            result = {
                'status': 'success',
                'url': url,
                'public_id': public_id,
                'dimensions': {'width': preset['width'], 'height': preset['height']},
                'used_gen_fill': False
            }
            if save_to_file_flag:
                try:
                    response = requests.get(url, timeout=60)
                    if response.ok:
                        filename = save_to_file(response.content, 'cloudinary_resized', 'jpg')
                        result['filename'] = filename
                except Exception as e:
                    result['download_error'] = str(e)
            return result
    else:
        return resize_video(public_id, preset['width'], preset['height'])

def batch_resize_for_platforms(public_id, platform_presets, resource_type='image', save_to_file_flag=True):
    """Resize for multiple platforms at once."""
    results = {}
    filenames = []

    for preset in platform_presets:
        result = resize_for_platform(public_id, preset, resource_type, save_to_file_flag=save_to_file_flag)
        results[preset] = result
        if result.get('filename'):
            filenames.append({'preset': preset, 'filename': result['filename']})

    return {
        'status': 'success',
        'public_id': public_id,
        'results': results,
        'filenames': filenames,
        'total_variants': len(results)
    }

def batch_resize_package(public_id, package_name, resource_type='image', save_to_file_flag=True):
    """Resize using a predefined package."""
    if package_name not in PRESET_PACKAGES:
        return {
            'status': 'error',
            'message': f"Unknown package: {package_name}",
            'available_packages': list(PRESET_PACKAGES.keys())
        }

    package = PRESET_PACKAGES[package_name]
    results = batch_resize_for_platforms(public_id, package['presets'], resource_type, save_to_file_flag)
    results['package_name'] = package['name']
    results['package_description'] = package['description']
    return results

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run(action, **kwargs):
    """
    Cloudinary Creative Tools v5.16.0
    Aligned with Baymax — Creative Innovate approach - URL transforms, not API calls.

    Actions:
    - upload_image: Upload image using unsigned preset
    - upload_video: Upload video using unsigned preset
    - resize_with_gen_fill: Resize image with AI Generative Fill
    - resize_video: Resize video with smart cropping
    - resize_for_platform: Resize for specific platform preset
    - batch_resize: Resize for multiple platforms
    - batch_resize_package: Resize using a preset package
    - build_transform_url: Just build the URL without downloading
    - check_gemini_compatible: Check if ratio needs Cloudinary
    - get_platform_presets: List available presets
    - get_packages: List available packages
    """

    try:
        if action == 'upload_image':
            return upload_with_unsigned_preset(
                kwargs.get('file_url'),
                resource_type='image',
                folder=kwargs.get('folder', 'cav-assets'),
                public_id=kwargs.get('public_id')
            )

        elif action == 'upload_video':
            return upload_with_unsigned_preset(
                kwargs.get('file_url'),
                resource_type='video',
                folder=kwargs.get('folder', 'cav-assets'),
                public_id=kwargs.get('public_id')
            )

        elif action == 'resize_with_gen_fill':
            return resize_image_with_gen_fill(
                kwargs.get('public_id'),
                kwargs.get('width'),
                kwargs.get('height'),
                gravity=kwargs.get('gravity', 'center'),
                quality=kwargs.get('quality', 'auto:best'),
                save_to_file_flag=kwargs.get('save_to_file', True)
            )

        elif action == 'resize_video':
            return resize_video(
                kwargs.get('public_id'),
                width=kwargs.get('width'),
                height=kwargs.get('height'),
                aspect_ratio=kwargs.get('aspect_ratio'),
                crop=kwargs.get('crop', 'fill'),
                gravity=kwargs.get('gravity', 'auto'),
                start_offset=kwargs.get('start_offset'),
                end_offset=kwargs.get('end_offset'),
                effect=kwargs.get('effect')
            )

        elif action == 'resize_for_platform':
            return resize_for_platform(
                kwargs.get('public_id'),
                kwargs.get('platform_preset'),
                resource_type=kwargs.get('resource_type', 'image'),
                gravity=kwargs.get('gravity', 'center'),
                save_to_file_flag=kwargs.get('save_to_file', True)
            )

        elif action == 'batch_resize':
            return batch_resize_for_platforms(
                kwargs.get('public_id'),
                kwargs.get('platform_presets', []),
                resource_type=kwargs.get('resource_type', 'image'),
                save_to_file_flag=kwargs.get('save_to_file', True)
            )

        elif action == 'batch_resize_package':
            return batch_resize_package(
                kwargs.get('public_id'),
                kwargs.get('package_name'),
                resource_type=kwargs.get('resource_type', 'image'),
                save_to_file_flag=kwargs.get('save_to_file', True)
            )

        elif action == 'build_transform_url':
            creds = get_credentials()
            resource_type = kwargs.get('resource_type', 'image')
            if resource_type == 'video':
                url = build_video_transform_url(
                    creds['cloud_name'],
                    kwargs.get('public_id'),
                    width=kwargs.get('width'),
                    height=kwargs.get('height'),
                    aspect_ratio=kwargs.get('aspect_ratio'),
                    crop=kwargs.get('crop', 'fill'),
                    gravity=kwargs.get('gravity', 'auto')
                )
            else:
                url = build_image_transform_url(
                    creds['cloud_name'],
                    kwargs.get('public_id'),
                    kwargs.get('width'),
                    kwargs.get('height'),
                    use_gen_fill=kwargs.get('use_gen_fill', False),
                    gravity=kwargs.get('gravity', 'center')
                )
            return {'status': 'success', 'url': url}

        elif action == 'check_gemini_compatible':
            width = kwargs.get('width')
            height = kwargs.get('height')
            if not width or not height:
                return {'status': 'error', 'message': 'width and height required'}
            result = is_gemini_compatible(width, height)
            result['status'] = 'success'
            return result

        elif action == 'get_platform_presets':
            by_platform = {}
            for key, preset in PLATFORM_PRESETS.items():
                platform = preset['platform']
                if platform not in by_platform:
                    by_platform[platform] = []
                by_platform[platform].append({
                    'preset_key': key,
                    'placement': preset['placement'],
                    'width': preset['width'],
                    'height': preset['height'],
                    'ratio': preset['ratio'],
                    'requires_gen_fill': preset.get('requires_gen_fill', False)
                })
            return {'status': 'success', 'presets_by_platform': by_platform}

        elif action == 'get_packages':
            return {
                'status': 'success',
                'packages': {k: {'name': v['name'], 'description': v['description'], 'presets': v['presets']} for k, v in PRESET_PACKAGES.items()}
            }

        else:
            return {
                'status': 'error',
                'message': f'Unknown action: {action}',
                'available_actions': [
                    'upload_image', 'upload_video', 'resize_with_gen_fill', 'resize_video',
                    'resize_for_platform', 'batch_resize', 'batch_resize_package',
                    'build_transform_url', 'check_gemini_compatible',
                    'get_platform_presets', 'get_packages'
                ]
            }

    except Exception as e:
        return {'status': 'error', 'message': str(e), 'action': action}
