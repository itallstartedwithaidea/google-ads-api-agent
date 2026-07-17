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

def get_report_config(report_type):
    configs = {
        "campaign": {
            "resource": "campaign",
            "fields": ["campaign.id", "campaign.name", "campaign.status", "campaign.advertising_channel_type", "campaign.bidding_strategy_type"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.conversions_value", "metrics.ctr", "metrics.average_cpc", "metrics.cost_per_conversion", "metrics.search_impression_share"]
        },
        "ad_group": {
            "resource": "ad_group",
            "fields": ["ad_group.id", "ad_group.name", "ad_group.status", "ad_group.type", "campaign.id", "campaign.name"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.conversions_value", "metrics.ctr", "metrics.average_cpc", "metrics.cost_per_conversion"]
        },
        "keyword": {
            "resource": "keyword_view",
            "fields": ["ad_group_criterion.criterion_id", "ad_group_criterion.keyword.text", "ad_group_criterion.keyword.match_type", "ad_group_criterion.status", "ad_group_criterion.quality_info.quality_score", "ad_group.id", "ad_group.name", "campaign.id", "campaign.name"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.ctr", "metrics.average_cpc", "metrics.cost_per_conversion", "metrics.historical_quality_score"]
        },
        "ad": {
            "resource": "ad_group_ad",
            "fields": ["ad_group_ad.ad.id", "ad_group_ad.ad.type", "ad_group_ad.ad.final_urls", "ad_group_ad.status", "ad_group_ad.policy_summary.approval_status", "ad_group.id", "ad_group.name", "campaign.id", "campaign.name"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.ctr", "metrics.average_cpc"]
        },
        "search_term": {
            "resource": "search_term_view",
            "fields": ["search_term_view.search_term", "search_term_view.status", "ad_group.id", "ad_group.name", "campaign.id", "campaign.name", "segments.keyword.info.text", "segments.keyword.info.match_type"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.ctr", "metrics.average_cpc", "metrics.cost_per_conversion"]
        },
        "device": {
            "resource": "campaign",
            "fields": ["campaign.id", "campaign.name", "segments.device"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.ctr", "metrics.average_cpc"]
        },
        "geo": {
            "resource": "geographic_view",
            "fields": ["geographic_view.country_criterion_id", "geographic_view.location_type", "campaign.id", "campaign.name"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.ctr", "metrics.average_cpc"]
        },
        "hour_of_day": {
            "resource": "campaign",
            "fields": ["campaign.id", "campaign.name", "segments.hour"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions"]
        },
        "day_of_week": {
            "resource": "campaign",
            "fields": ["campaign.id", "campaign.name", "segments.day_of_week"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions"]
        },
        "account": {
            "resource": "customer",
            "fields": ["customer.id", "customer.descriptive_name"],
            "metrics": ["metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.conversions_value"]
        }
    }
    return configs.get(report_type)

def build_date_clause(date_range):
    if date_range in ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "THIS_MONTH", "LAST_MONTH", "THIS_QUARTER", "LAST_QUARTER", "THIS_YEAR", "LAST_YEAR"]:
        return f"segments.date DURING {date_range}"
    elif "," in date_range:
        start, end = date_range.split(",")
        return f"segments.date BETWEEN '{start.strip()}' AND '{end.strip()}'"
    return "segments.date DURING LAST_30_DAYS"

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

def run(customer_id, report_type, date_range="LAST_30_DAYS", login_customer_id=None, filters=None, metrics=None, limit=1000):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        config = get_report_config(report_type)
        if not config:
            return {"status": "error", "message": f"Unknown report type: {report_type}. Valid: campaign, ad_group, keyword, ad, search_term, device, geo, hour_of_day, day_of_week, account"}

        client = get_client(login_customer_id)
        ga_service = client.get_service("GoogleAdsService")

        all_fields = config["fields"] + (metrics or config["metrics"])
        select_clause = ", ".join(all_fields)

        where_clauses = [build_date_clause(date_range)]

        if filters:
            if filters.get("campaign_ids"):
                ids = ", ".join(str(i) for i in filters["campaign_ids"])
                where_clauses.append(f"campaign.id IN ({ids})")
            if filters.get("ad_group_ids"):
                ids = ", ".join(str(i) for i in filters["ad_group_ids"])
                where_clauses.append(f"ad_group.id IN ({ids})")
            if filters.get("status"):
                if report_type == "campaign":
                    where_clauses.append(f"campaign.status = '{filters['status']}'")
                elif report_type == "ad_group":
                    where_clauses.append(f"ad_group.status = '{filters['status']}'")

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT {select_clause}
            FROM {config['resource']}
            WHERE {where_clause}
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        results = []
        for row in response:
            row_dict = {}
            for field in all_fields:
                value = extract_value(row, field)
                if value is not None:
                    if "_micros" in field and isinstance(value, (int, float)):
                        row_dict[field.replace("_micros", "")] = round(value / 1000000, 2)
                    elif isinstance(value, (int, float, str, bool)):
                        row_dict[field] = value
                    else:
                        row_dict[field] = str(value)
            results.append(row_dict)

        summary = {}
        if results:
            total_impressions = sum(r.get("metrics.impressions", 0) or 0 for r in results)
            total_clicks = sum(r.get("metrics.clicks", 0) or 0 for r in results)
            total_cost = sum(r.get("metrics.cost", 0) or 0 for r in results)
            total_conversions = sum(r.get("metrics.conversions", 0) or 0 for r in results)

            summary = {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_cost": round(total_cost, 2),
                "total_conversions": round(total_conversions, 2),
                "overall_ctr": round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0,
                "overall_cpc": round(total_cost / total_clicks, 2) if total_clicks > 0 else 0,
                "overall_cpa": round(total_cost / total_conversions, 2) if total_conversions > 0 else 0
            }

        return {
            "status": "success",
            "report_type": report_type,
            "date_range": date_range,
            "row_count": len(results),
            "summary": summary,
            "results": results
        }

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
