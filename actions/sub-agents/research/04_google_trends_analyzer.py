# Google Trends API via SearchAPI.io
import requests

def run(q=None, data_type="TIMESERIES", geo="Worldwide", time="today 12-m", cat=0, 
        region=None, gprop="", tz=420):
    """
    Retrieve Google Trends data including interest over time, interest by region, 
    related queries, and related topics.

    Args:
        q: Search query (required for TIMESERIES with cat=0, and GEO_MAP). 
           Up to 5 queries comma-separated (e.g., 'Java,Python,JavaScript')
        data_type: Type of data to retrieve:
                   - 'TIMESERIES' (Interest Over Time) - historical indexed data
                   - 'GEO_MAP' (Interest by Region) - geographical data
                   - 'RELATED_QUERIES' - queries related to input
                   - 'RELATED_TOPICS' - topics related to input
        geo: Geographic location (default: 'Worldwide'). Use country codes like 'US', 'GB', 'DE'
        time: Time range for data:
              - 'now 1-H' (past hour)
              - 'now 4-H' (past 4 hours)
              - 'now 1-d' (past day)
              - 'now 7-d' (past 7 days)
              - 'today 1-m' (past 30 days)
              - 'today 3-m' (past 90 days)
              - 'today 12-m' (past 12 months) [DEFAULT]
              - 'today 5-y' (past 5 years)
              - 'all' (since 2004)
              - Custom: 'YYYY-MM-DD YYYY-MM-DD'
        cat: Category ID (default: 0 for All Categories)
        region: For GEO_MAP only - 'COUNTRY', 'REGION', 'DMA', 'CITY'
        gprop: Search type filter:
               - '' (Web Search) [DEFAULT]
               - 'images' (Image Search)
               - 'news' (News Search)
               - 'froogle' (Google Shopping)
               - 'youtube' (YouTube Search)
        tz: Timezone offset from UTC (-1439 to 1439, default: 420)

    Returns:
        dict: Trends data based on data_type selected
    """

    # Get API key from secrets
    api_key = secrets.get("SEARCHAPI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "SearchAPI.io API key not configured. Please add your API key in the Custom Action settings."
        }

    # Validate data_type
    valid_data_types = ["TIMESERIES", "GEO_MAP", "RELATED_QUERIES", "RELATED_TOPICS"]
    if data_type not in valid_data_types:
        return {
            "status": "error",
            "message": f"Invalid data_type. Must be one of: {', '.join(valid_data_types)}"
        }

    # Validate required query parameter
    if data_type == "GEO_MAP" and not q:
        return {
            "status": "error",
            "message": "Search query 'q' is required for GEO_MAP data_type"
        }

    if data_type == "TIMESERIES" and not q and cat == 0:
        return {
            "status": "error",
            "message": "Search query 'q' is required for TIMESERIES when cat=0 (All Categories)"
        }

    # Build request parameters
    params = {
        "engine": "google_trends",
        "api_key": api_key,
        "data_type": data_type,
        "tz": tz
    }

    # Add query if provided
    if q:
        params["q"] = q

    # Add geo location
    if geo and geo != "Worldwide":
        params["geo"] = geo

    # Add time range
    if time:
        params["time"] = time

    # Add category if not default
    if cat != 0:
        params["cat"] = cat

    # Add region for GEO_MAP
    if data_type == "GEO_MAP" and region:
        if region in ["COUNTRY", "REGION", "DMA", "CITY"]:
            params["region"] = region

    # Add search type filter
    if gprop and gprop in ["images", "news", "froogle", "youtube"]:
        params["gprop"] = gprop

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
                "data_type": data_type,
                "query": q,
                "search_metadata": data.get("search_metadata", {}),
                "search_parameters": data.get("search_parameters", {})
            }

            # Include relevant data based on data_type
            if data_type == "TIMESERIES" and "interest_over_time" in data:
                result["interest_over_time"] = data["interest_over_time"]

                # Add summary statistics
                if "averages" in data["interest_over_time"]:
                    result["averages"] = data["interest_over_time"]["averages"]

                # Count data points
                if "timeline_data" in data["interest_over_time"]:
                    result["data_points_count"] = len(data["interest_over_time"]["timeline_data"])

            elif data_type == "GEO_MAP" and "interest_by_region" in data:
                result["interest_by_region"] = data["interest_by_region"]
                result["regions_count"] = len(data["interest_by_region"])

            elif data_type == "RELATED_QUERIES" and "related_queries" in data:
                result["related_queries"] = data["related_queries"]

                # Count queries
                top_count = len(data["related_queries"].get("top", []))
                rising_count = len(data["related_queries"].get("rising", []))
                result["summary"] = {
                    "top_queries_count": top_count,
                    "rising_queries_count": rising_count
                }

            elif data_type == "RELATED_TOPICS" and "related_topics" in data:
                result["related_topics"] = data["related_topics"]

                # Count topics
                top_count = len(data["related_topics"].get("top", []))
                rising_count = len(data["related_topics"].get("rising", []))
                result["summary"] = {
                    "top_topics_count": top_count,
                    "rising_topics_count": rising_count
                }

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
