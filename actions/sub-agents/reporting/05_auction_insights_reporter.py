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

def get_auction_insights_by_campaign(client, customer_id, date_range, campaign_ids=None):
    ga_service = client.get_service("GoogleAdsService")
    where = f"segments.date DURING {date_range}"
    if campaign_ids:
        ids = ", ".join(str(i) for i in campaign_ids)
        where += f" AND campaign.id IN ({ids})"

    query = f"""
        SELECT campaign.id, campaign.name, auction_insight.domain, auction_insight.is_you,
            auction_insight.average_position, auction_insight.search_impression_share,
            auction_insight.search_overlap_rate, auction_insight.search_position_above_rate,
            auction_insight.search_top_impression_share, auction_insight.search_outranking_share
        FROM auction_insight WHERE {where} ORDER BY auction_insight.search_impression_share DESC LIMIT 500
    """

    results = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        ai = row.auction_insight
        results.append({
            "campaign_id": row.campaign.id, "campaign_name": row.campaign.name, "domain": ai.domain, "is_you": ai.is_you,
            "impression_share": round(ai.search_impression_share * 100, 1) if ai.search_impression_share else 0,
            "overlap_rate": round(ai.search_overlap_rate * 100, 1) if ai.search_overlap_rate else 0,
            "position_above_rate": round(ai.search_position_above_rate * 100, 1) if ai.search_position_above_rate else 0,
            "top_of_page_rate": round(ai.search_top_impression_share * 100, 1) if ai.search_top_impression_share else 0,
            "outranking_share": round(ai.search_outranking_share * 100, 1) if ai.search_outranking_share else 0
        })
    return results

def get_auction_insights_summary(client, customer_id, date_range):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT auction_insight.domain, auction_insight.is_you, auction_insight.search_impression_share,
            auction_insight.search_overlap_rate, auction_insight.search_position_above_rate,
            auction_insight.search_top_impression_share, auction_insight.search_outranking_share
        FROM auction_insight WHERE segments.date DURING {date_range} ORDER BY auction_insight.search_impression_share DESC LIMIT 100
    """

    your_metrics = None
    competitors = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        ai = row.auction_insight
        metrics = {
            "domain": ai.domain,
            "impression_share": round(ai.search_impression_share * 100, 1) if ai.search_impression_share else 0,
            "overlap_rate": round(ai.search_overlap_rate * 100, 1) if ai.search_overlap_rate else 0,
            "position_above_rate": round(ai.search_position_above_rate * 100, 1) if ai.search_position_above_rate else 0,
            "top_of_page_rate": round(ai.search_top_impression_share * 100, 1) if ai.search_top_impression_share else 0,
            "outranking_share": round(ai.search_outranking_share * 100, 1) if ai.search_outranking_share else 0
        }
        if ai.is_you:
            your_metrics = metrics
        else:
            competitors.append(metrics)

    competitors.sort(key=lambda x: x["impression_share"], reverse=True)
    return {"your_performance": your_metrics, "top_competitors": competitors[:20]}

def run(customer_id, date_range="LAST_30_DAYS", login_customer_id=None, campaign_ids=None, ad_group_ids=None):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")
        client = get_client(login_customer_id)

        summary = get_auction_insights_summary(client, customer_id, date_range)
        by_campaign = []
        if campaign_ids:
            by_campaign = get_auction_insights_by_campaign(client, customer_id, date_range, campaign_ids)

        analysis = []
        if summary["your_performance"] and summary["top_competitors"]:
            your_is = summary["your_performance"]["impression_share"]
            for comp in summary["top_competitors"][:10]:
                threat_level = "LOW"
                if comp["impression_share"] > your_is * 0.8:
                    threat_level = "HIGH"
                elif comp["impression_share"] > your_is * 0.5:
                    threat_level = "MEDIUM"
                analysis.append({"domain": comp["domain"], "their_impression_share": comp["impression_share"], "your_impression_share": your_is, "overlap_rate": comp["overlap_rate"], "they_beat_you_rate": comp["position_above_rate"], "threat_level": threat_level})

        return {"status": "success", "date_range": date_range, "your_performance": summary["your_performance"], "competitor_count": len(summary["top_competitors"]), "top_competitors": summary["top_competitors"][:10], "competitive_analysis": analysis, "by_campaign": by_campaign if by_campaign else None}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
