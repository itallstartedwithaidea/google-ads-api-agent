try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'google-ads'])
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException

def get_client(login_customer_id=None):
    credentials = {
        "developer_token": secrets["DEVELOPER_TOKEN"],
        "client_id": secrets["CLIENT_ID"],
        "client_secret": secrets["CLIENT_SECRET"],
        "refresh_token": secrets["REFRESH_TOKEN"],
        "use_proto_plus": True
    }
    if login_customer_id:
        credentials["login_customer_id"] = str(login_customer_id).replace("-", "")
    return GoogleAdsClient.load_from_dict(credentials, version="v18")

def generate_keyword_ideas(client, customer_id, keywords=None, url=None, language_id="1000", geo_target_ids=None, limit=100):
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")

    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = f"languageConstants/{language_id}"

    # Add geo targets
    if geo_target_ids:
        for geo_id in geo_target_ids:
            request.geo_target_constants.append(f"geoTargetConstants/{geo_id}")
    else:
        # Default to US
        request.geo_target_constants.append("geoTargetConstants/2840")

    # Set keyword seed or URL seed
    if keywords:
        request.keyword_seed.keywords.extend(keywords)
    elif url:
        request.url_seed.url = url
    else:
        return []

    request.include_adult_keywords = False
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS

    results = []
    response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

    for idea in response:
        metrics = idea.keyword_idea_metrics
        results.append({
            "keyword": idea.text,
            "avg_monthly_searches": metrics.avg_monthly_searches if metrics else 0,
            "competition": str(metrics.competition.name) if metrics and metrics.competition else "UNKNOWN",
            "competition_index": metrics.competition_index if metrics else 0,
            "low_top_of_page_bid": round(metrics.low_top_of_page_bid_micros / 1000000, 2) if metrics and metrics.low_top_of_page_bid_micros else 0,
            "high_top_of_page_bid": round(metrics.high_top_of_page_bid_micros / 1000000, 2) if metrics and metrics.high_top_of_page_bid_micros else 0
        })

        if len(results) >= limit:
            break

    return results

def get_historical_metrics(client, customer_id, keywords, language_id="1000", geo_target_ids=None):
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")

    request = client.get_type("GenerateKeywordHistoricalMetricsRequest")
    request.customer_id = customer_id
    request.keywords.extend(keywords)
    request.language = f"languageConstants/{language_id}"

    if geo_target_ids:
        for geo_id in geo_target_ids:
            request.geo_target_constants.append(f"geoTargetConstants/{geo_id}")
    else:
        request.geo_target_constants.append("geoTargetConstants/2840")

    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS

    results = []
    response = keyword_plan_idea_service.generate_keyword_historical_metrics(request=request)

    for result in response.results:
        metrics = result.keyword_metrics

        # Get monthly search volumes
        monthly_volumes = []
        if metrics and metrics.monthly_search_volumes:
            for vol in metrics.monthly_search_volumes:
                monthly_volumes.append({
                    "year": vol.year,
                    "month": str(vol.month.name) if vol.month else "UNKNOWN",
                    "searches": vol.monthly_searches
                })

        results.append({
            "keyword": result.text,
            "avg_monthly_searches": metrics.avg_monthly_searches if metrics else 0,
            "competition": str(metrics.competition.name) if metrics and metrics.competition else "UNKNOWN",
            "low_top_of_page_bid": round(metrics.low_top_of_page_bid_micros / 1000000, 2) if metrics and metrics.low_top_of_page_bid_micros else 0,
            "high_top_of_page_bid": round(metrics.high_top_of_page_bid_micros / 1000000, 2) if metrics and metrics.high_top_of_page_bid_micros else 0,
            "monthly_volumes": monthly_volumes[-12:]  # Last 12 months
        })

    return results

def run(customer_id, action, login_customer_id=None, keywords=None, url=None, 
        language_id="1000", geo_target_ids=None, include_adult=False, limit=100):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)

        if action == "generate_ideas":
            if not keywords and not url:
                return {"status": "error", "message": "keywords or url required"}
            ideas = generate_keyword_ideas(client, customer_id, keywords, url, language_id, geo_target_ids, limit)

            # Sort by search volume
            ideas.sort(key=lambda x: x["avg_monthly_searches"], reverse=True)

            return {
                "status": "success",
                "count": len(ideas),
                "seed_keywords": keywords,
                "seed_url": url,
                "keyword_ideas": ideas
            }

        elif action == "get_historical_metrics":
            if not keywords:
                return {"status": "error", "message": "keywords list required"}
            metrics = get_historical_metrics(client, customer_id, keywords, language_id, geo_target_ids)
            return {
                "status": "success",
                "count": len(metrics),
                "historical_metrics": metrics
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}. Use 'generate_ideas' or 'get_historical_metrics'"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
