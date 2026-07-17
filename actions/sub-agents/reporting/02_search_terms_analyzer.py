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
    return GoogleAdsClient.load_from_dict(credentials, version="v19")

def extract_value(obj, path):
    parts = path.split('.')
    current = obj
    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    if hasattr(current, 'name'):
        return current.name
    return current

def get_search_terms(client, customer_id, date_range, campaign_ids=None, limit=5000):
    ga_service = client.get_service("GoogleAdsService")

    where_clauses = [f"segments.date DURING {date_range}", "metrics.impressions > 0"]
    if campaign_ids:
        ids = ", ".join(str(i) for i in campaign_ids)
        where_clauses.append(f"campaign.id IN ({ids})")

    query = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            segments.keyword.info.text,
            segments.keyword.info.match_type,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM search_term_view
        WHERE {" AND ".join(where_clauses)}
        ORDER BY metrics.cost_micros DESC
        LIMIT {limit}
    """

    results = []
    response = ga_service.search(customer_id=customer_id, query=query)

    for row in response:
        results.append({
            "search_term": row.search_term_view.search_term,
            "status": str(row.search_term_view.status.name) if row.search_term_view.status else "UNKNOWN",
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "ad_group_id": row.ad_group.id,
            "ad_group_name": row.ad_group.name,
            "matched_keyword": row.segments.keyword.info.text if row.segments.keyword.info.text else "",
            "match_type": str(row.segments.keyword.info.match_type.name) if row.segments.keyword.info.match_type else "UNKNOWN",
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(row.metrics.cost_micros / 1000000, 2),
            "conversions": round(row.metrics.conversions, 2),
            "conversion_value": round(row.metrics.conversions_value, 2)
        })

    return results

def analyze_wasted_spend(search_terms, min_cost=10, min_clicks=5):
    wasted = []
    for term in search_terms:
        if term["conversions"] == 0 and term["cost"] >= min_cost and term["clicks"] >= min_clicks:
            wasted.append({
                **term,
                "recommendation": "PAUSE or ADD_NEGATIVE",
                "potential_savings": term["cost"]
            })

    wasted.sort(key=lambda x: x["cost"], reverse=True)
    total_waste = sum(t["cost"] for t in wasted)

    return {
        "count": len(wasted),
        "total_wasted_spend": round(total_waste, 2),
        "terms": wasted[:100]
    }

def analyze_opportunities(search_terms, min_conversions=1):
    opportunities = []
    for term in search_terms:
        if term["conversions"] >= min_conversions and term["status"] != "ADDED":
            cpa = term["cost"] / term["conversions"] if term["conversions"] > 0 else 0
            roas = term["conversion_value"] / term["cost"] if term["cost"] > 0 else 0
            opportunities.append({
                **term,
                "cpa": round(cpa, 2),
                "roas": round(roas, 2),
                "recommendation": "ADD_AS_KEYWORD",
                "suggested_match_type": "PHRASE" if term["clicks"] < 50 else "EXACT"
            })

    opportunities.sort(key=lambda x: x["conversions"], reverse=True)

    return {
        "count": len(opportunities),
        "total_conversions": sum(t["conversions"] for t in opportunities),
        "terms": opportunities[:100]
    }

def analyze_negatives(search_terms, min_clicks=3):
    negative_indicators = [
        "free", "cheap", "download", "torrent", "crack", "hack",
        "reddit", "youtube", "video", "tutorial", "how to",
        "job", "jobs", "career", "salary", "interview",
        "wiki", "wikipedia", "definition", "meaning"
    ]

    negatives = []
    for term in search_terms:
        search_lower = term["search_term"].lower()

        is_negative_candidate = False
        matched_indicator = None

        for indicator in negative_indicators:
            if indicator in search_lower:
                is_negative_candidate = True
                matched_indicator = indicator
                break

        if term["clicks"] >= min_clicks and term["conversions"] == 0:
            is_negative_candidate = True
            if not matched_indicator:
                matched_indicator = "zero_conversions"

        if is_negative_candidate and term["status"] != "EXCLUDED":
            negatives.append({
                **term,
                "reason": matched_indicator,
                "recommendation": "ADD_AS_NEGATIVE",
                "suggested_level": "CAMPAIGN" if term["clicks"] > 10 else "AD_GROUP"
            })

    negatives.sort(key=lambda x: x["cost"], reverse=True)

    return {
        "count": len(negatives),
        "potential_savings": round(sum(t["cost"] for t in negatives), 2),
        "terms": negatives[:100]
    }

def run(customer_id, analysis_type="all", date_range="LAST_30_DAYS", login_customer_id=None,
        min_cost=10, min_clicks=5, min_conversions=1, campaign_ids=None):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)

        search_terms = get_search_terms(client, customer_id, date_range, campaign_ids)

        if not search_terms:
            return {
                "status": "success",
                "message": "No search term data found for the specified criteria",
                "total_search_terms": 0
            }

        result = {
            "status": "success",
            "customer_id": customer_id,
            "date_range": date_range,
            "total_search_terms": len(search_terms),
            "total_cost": round(sum(t["cost"] for t in search_terms), 2),
            "total_conversions": round(sum(t["conversions"] for t in search_terms), 2)
        }

        if analysis_type in ["wasted_spend", "all"]:
            result["wasted_spend"] = analyze_wasted_spend(search_terms, min_cost, min_clicks)

        if analysis_type in ["opportunities", "all"]:
            result["opportunities"] = analyze_opportunities(search_terms, min_conversions)

        if analysis_type in ["negatives", "all"]:
            result["negatives"] = analyze_negatives(search_terms, min_clicks)

        return result

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
