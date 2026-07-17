# Google Search API via SearchAPI.io
import requests

def run(query, location=None, gl="us", hl="en", num_results=10, time_period=None, device="desktop", safe="off", page=1):
    """
    Perform a Google search using SearchAPI.io

    Args:
        query: Search query string (required)
        location: Geographic location for results (e.g., 'New York, United States')
        gl: Country code (default: 'us')
        hl: Interface language (default: 'en')
        num_results: Number of results (default: 10)
        time_period: Time filter - 'last_hour', 'last_day', 'last_week', 'last_month', 'last_year'
        device: Device type - 'desktop', 'mobile', 'tablet' (default: 'desktop')
        safe: SafeSearch - 'active' or 'off' (default: 'off')
        page: Page number (default: 1)

    Returns:
        dict: Search results including organic results, knowledge graph, ads, etc.
    """

    # Get API key from secrets
    api_key = secrets.get("SEARCHAPI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "SearchAPI.io API key not configured. Please add your API key in the Custom Action settings."
        }

    # Build request parameters
    params = {
        "engine": "google",
        "api_key": api_key,
        "q": query,
        "gl": gl,
        "hl": hl,
        "device": device,
        "safe": safe,
        "page": page
    }

    # Add optional parameters if provided
    if location:
        params["location"] = location

    if time_period and time_period in ["last_hour", "last_day", "last_week", "last_month", "last_year"]:
        params["time_period"] = time_period

    try:
        # Make the API request
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            # Build a clean response summary
            result = {
                "status": "success",
                "query": query,
                "search_metadata": data.get("search_metadata", {}),
                "search_information": data.get("search_information", {})
            }

            # Include all available result types
            result_types = [
                "organic_results", "knowledge_graph", "answer_box", 
                "related_questions", "ads", "shopping_ads", "local_ads",
                "top_stories", "local_results", "local_map",
                "inline_images", "inline_videos", "inline_shopping",
                "related_searches", "discussions_and_forums",
                "ai_overview", "weather_result", "sports_results",
                "jobs", "events", "courses", "scholarly_articles",
                "inline_recipes", "perspectives", "inline_tweets"
            ]

            for result_type in result_types:
                if result_type in data and data[result_type]:
                    result[result_type] = data[result_type]

            # Add pagination info if available
            if "pagination" in data:
                result["pagination"] = data["pagination"]

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
