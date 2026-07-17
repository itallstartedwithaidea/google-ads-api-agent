# Google Ads Transparency Center API via SearchAPI.io
import requests

def run(advertiser_id=None, domain=None, region="anywhere", platform=None, ad_format=None, 
        time_period=None, num=40, next_page_token=None):
    """
    Retrieve information about advertisers and their ad campaigns from Google Ads Transparency Center.

    Args:
        advertiser_id: Advertiser's unique ID (starts with 'AR'). Required if domain not provided.
                      Multiple IDs can be comma-separated.
        domain: Advertiser's verified domain (e.g., 'tesla.com'). Required if advertiser_id not provided.
        region: Region for search (default: 'anywhere')
        platform: Filter by platform - 'google_play', 'google_maps', 'google_search', 'youtube', 'google_shopping'
        ad_format: Filter by format - 'text', 'image', 'video'
        time_period: Time filter - 'today', 'yesterday', 'last_7_days', 'last_30_days' or 'YYYY-MM-DD..YYYY-MM-DD'
        num: Number of results (default: 40, max: 100)
        next_page_token: Token for fetching next page of results

    Returns:
        dict: Ad creatives with details including format, dates shown, advertiser info, and preview links
    """

    # Get API key from secrets
    api_key = secrets.get("SEARCHAPI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "SearchAPI.io API key not configured. Please add your API key in the Custom Action settings."
        }

    # Validate required parameters
    if not advertiser_id and not domain:
        return {
            "status": "error",
            "message": "Either 'advertiser_id' or 'domain' is required."
        }

    # Build request parameters
    params = {
        "engine": "google_ads_transparency_center",
        "api_key": api_key,
        "region": region,
        "num": min(num, 100)  # Cap at 100
    }

    # Add advertiser identifier
    if advertiser_id:
        params["advertiser_id"] = advertiser_id
    elif domain:
        params["domain"] = domain

    # Add optional filters
    if platform and platform in ["google_play", "google_maps", "google_search", "youtube", "google_shopping"]:
        params["platform"] = platform

    if ad_format and ad_format in ["text", "image", "video"]:
        params["ad_format"] = ad_format

    if time_period:
        params["time_period"] = time_period

    if next_page_token:
        params["next_page_token"] = next_page_token

    try:
        # Make the API request
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            # Build response
            result = {
                "status": "success",
                "search_metadata": data.get("search_metadata", {}),
                "search_parameters": data.get("search_parameters", {}),
                "search_information": data.get("search_information", {})
            }

            # Include ad creatives
            if "ad_creatives" in data:
                result["ad_creatives"] = data["ad_creatives"]
                result["total_ads_returned"] = len(data["ad_creatives"])

                # Summarize ad formats
                format_counts = {}
                for ad in data["ad_creatives"]:
                    fmt = ad.get("format", "unknown")
                    format_counts[fmt] = format_counts.get(fmt, 0) + 1
                result["format_summary"] = format_counts

            # Include pagination token for next page
            if "pagination" in data:
                result["pagination"] = data["pagination"]
                result["has_more_results"] = "next_page_token" in data.get("pagination", {})

            return result

        elif response.status_code == 401:
            return {
                "status": "error",
                "message": "Invalid API key. Please check your SearchAPI.io API key.",
                "status_code": 401
            }
        elif response.status_code == 429:
            return {
                "status": "error",
                "message": "Rate limit exceeded. Please wait before making more requests.",
                "status_code": 429
            }
        else:
            return {
                "status": "error",
                "message": f"API returned status code {response.status_code}",
                "status_code": response.status_code,
                "details": response.text[:500] if response.text else None
            }

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Request timed out. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
