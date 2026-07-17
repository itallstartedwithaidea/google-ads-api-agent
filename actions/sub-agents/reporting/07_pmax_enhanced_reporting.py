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

def generate_pmax_preview_html(asset_group_data, channel="search"):
    """Generate HTML preview for Performance Max asset groups across channels."""
    headlines = asset_group_data.get('headlines', [])
    descriptions = asset_group_data.get('descriptions', [])
    business_name = asset_group_data.get('business_name', 'Business')
    final_url = asset_group_data.get('final_urls', [''])[0] if asset_group_data.get('final_urls') else '#'

    headline = headlines[0] if headlines else 'Headline'
    description = descriptions[0] if descriptions else 'Description'

    if channel == "search":
        preview_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 16px; border: 1px solid #dfe1e5; border-radius: 8px; background: white;">
            <div style="margin-bottom: 4px;">
                <span style="font-size: 11px; color: #202124;">Ad · </span>
                <span style="font-size: 12px; color: #202124;">{final_url.replace('https://', '').replace('http://', '').split('/')[0]}</span>
            </div>
            <div style="font-size: 18px; color: #1a0dab; margin-bottom: 4px; cursor: pointer;">{headline}</div>
            {f'<div style="font-size: 18px; color: #1a0dab; margin-bottom: 8px;">{headlines[1] if len(headlines) > 1 else ""}</div>' if len(headlines) > 1 else ''}
            <div style="font-size: 13px; color: #4d5156; line-height: 1.4;">{description}</div>
        </div>
        """
    elif channel == "display":
        preview_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white;">
            <div style="height: 150px; background: linear-gradient(135deg, #4285f4, #34a853); display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 12px;">[Marketing Image]</span>
            </div>
            <div style="padding: 12px;">
                <div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 4px;">{headline}</div>
                <div style="font-size: 12px; color: #5f6368; margin-bottom: 8px;">{description[:80]}...</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 10px; color: #70757a;">Ad · {business_name}</span>
                    <span style="background: #1a73e8; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">Learn More</span>
                </div>
            </div>
        </div>
        """
    elif channel == "youtube":
        preview_html = f"""
        <div style="font-family: 'YouTube Sans', Arial, sans-serif; max-width: 320px; background: #0f0f0f; border-radius: 12px; overflow: hidden;">
            <div style="position: relative; height: 180px; background: #272727; display: flex; align-items: center; justify-content: center;">
                <div style="width: 60px; height: 60px; background: rgba(255,0,0,0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <div style="width: 0; height: 0; border-left: 20px solid white; border-top: 12px solid transparent; border-bottom: 12px solid transparent; margin-left: 5px;"></div>
                </div>
                <div style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.8); color: #fff; padding: 2px 6px; border-radius: 2px; font-size: 10px;">Ad</div>
            </div>
            <div style="padding: 12px;">
                <div style="font-size: 14px; color: #f1f1f1; font-weight: 500; line-height: 1.3; margin-bottom: 8px;">{headline}</div>
                <div style="font-size: 12px; color: #aaa;">{business_name} · Sponsored</div>
            </div>
        </div>
        """
    elif channel == "discover":
        preview_html = f"""
        <div style="font-family: 'Google Sans', Arial, sans-serif; max-width: 340px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <div style="height: 180px; background: linear-gradient(135deg, #ea4335, #fbbc04); display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 12px;">[Discover Image]</span>
            </div>
            <div style="padding: 12px;">
                <div style="font-size: 16px; font-weight: 500; color: #202124; margin-bottom: 6px;">{headline}</div>
                <div style="font-size: 13px; color: #5f6368;">{description[:90]}...</div>
                <div style="margin-top: 8px; font-size: 11px; color: #70757a;">Sponsored · {business_name}</div>
            </div>
        </div>
        """
    elif channel == "gmail":
        preview_html = f"""
        <div style="font-family: 'Google Sans', Arial, sans-serif; max-width: 360px; background: #fff; border: 1px solid #dadce0; border-radius: 8px;">
            <div style="padding: 12px; display: flex; align-items: center; border-bottom: 1px solid #dadce0;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: #fbbc04; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                    <span style="color: white; font-size: 16px; font-weight: 500;">{business_name[0] if business_name else 'A'}</span>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 14px; font-weight: 500; color: #202124;">{business_name}</div>
                    <div style="font-size: 12px; color: #5f6368;">Ad · Sponsored</div>
                </div>
            </div>
            <div style="padding: 12px;">
                <div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 4px;">{headline}</div>
                <div style="font-size: 13px; color: #5f6368;">{description[:100]}...</div>
            </div>
        </div>
        """
    else:
        preview_html = f"<div style='padding: 16px; border: 1px solid #ddd;'>{headline}<br/>{description}</div>"

    return preview_html

def get_pmax_placements(client, customer_id, campaign_id=None, date_range="LAST_30_DAYS", limit=100):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range}"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            performance_max_placement_view.placement,
            performance_max_placement_view.placement_type,
            performance_max_placement_view.display_name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM performance_max_placement_view
        WHERE {where}
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """

    placements = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        pv = row.performance_max_placement_view
        placements.append({
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "placement": pv.placement if pv.placement else "Unknown",
            "placement_type": str(pv.placement_type.name) if pv.placement_type else "UNKNOWN",
            "display_name": pv.display_name if pv.display_name else "",
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round((row.metrics.clicks / row.metrics.impressions * 100), 2) if row.metrics.impressions > 0 else 0
            }
        })

    # Group by placement type
    by_type = {}
    for p in placements:
        pt = p["placement_type"]
        if pt not in by_type:
            by_type[pt] = {"count": 0, "impressions": 0, "clicks": 0, "cost": 0, "conversions": 0}
        by_type[pt]["count"] += 1
        by_type[pt]["impressions"] += p["metrics"]["impressions"]
        by_type[pt]["clicks"] += p["metrics"]["clicks"]
        by_type[pt]["cost"] += p["metrics"]["cost"]
        by_type[pt]["conversions"] += p["metrics"]["conversions"]

    return {"placements": placements, "summary_by_type": by_type, "total_placements": len(placements)}

def get_asset_combinations(client, customer_id, campaign_id=None, asset_group_id=None, date_range="LAST_30_DAYS", limit=50):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range}"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"
    if asset_group_id:
        where += f" AND asset_group.id = {asset_group_id}"

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group_top_combination_view.asset_group_top_combinations
        FROM asset_group_top_combination_view
        WHERE {where}
        LIMIT {limit}
    """

    combinations = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        top_combos = row.asset_group_top_combination_view.asset_group_top_combinations

        combo_data = {
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "asset_group_id": row.asset_group.id,
            "asset_group_name": row.asset_group.name,
            "top_combinations": []
        }

        if top_combos:
            for combo in top_combos:
                assets_in_combo = []
                if combo.assets:
                    for asset in combo.assets:
                        assets_in_combo.append({
                            "asset_resource": asset.asset if asset.asset else "",
                            "field_type": str(asset.asset_field_type.name) if asset.asset_field_type else "UNKNOWN"
                        })
                combo_data["top_combinations"].append({"assets": assets_in_combo})

        combinations.append(combo_data)

    return {"combinations": combinations, "total": len(combinations)}

def get_asset_performance(client, customer_id, campaign_id=None, asset_group_id=None, date_range="LAST_30_DAYS", limit=100):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range}"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"
    if asset_group_id:
        where += f" AND asset_group.id = {asset_group_id}"

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group_asset.asset,
            asset_group_asset.field_type,
            asset_group_asset.performance_label,
            asset_group_asset.status,
            asset.id,
            asset.name,
            asset.type,
            asset.text_asset.text,
            asset.image_asset.full_size.url
        FROM asset_group_asset
        WHERE {where}
        ORDER BY asset_group_asset.performance_label DESC
        LIMIT {limit}
    """

    assets = []
    performance_summary = {"BEST": 0, "GOOD": 0, "LOW": 0, "LEARNING": 0, "PENDING": 0, "UNKNOWN": 0}

    for row in ga_service.search(customer_id=customer_id, query=query):
        aga = row.asset_group_asset
        asset = row.asset

        perf_label = str(aga.performance_label.name) if aga.performance_label else "UNKNOWN"
        performance_summary[perf_label] = performance_summary.get(perf_label, 0) + 1

        # Get asset content
        content = ""
        if asset.text_asset and asset.text_asset.text:
            content = asset.text_asset.text
        elif asset.image_asset and asset.image_asset.full_size:
            content = asset.image_asset.full_size.url if asset.image_asset.full_size.url else "[Image]"

        assets.append({
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "asset_group_id": row.asset_group.id,
            "asset_group_name": row.asset_group.name,
            "asset_id": asset.id,
            "asset_name": asset.name if asset.name else "",
            "asset_type": str(asset.type_.name) if asset.type_ else "UNKNOWN",
            "field_type": str(aga.field_type.name) if aga.field_type else "UNKNOWN",
            "performance_label": perf_label,
            "status": str(aga.status.name) if aga.status else "UNKNOWN",
            "content": content[:200] if content else ""
        })

    # Sort by performance
    perf_order = {"BEST": 0, "GOOD": 1, "LOW": 2, "LEARNING": 3, "PENDING": 4, "UNKNOWN": 5}
    assets.sort(key=lambda x: perf_order.get(x["performance_label"], 5))

    return {"assets": assets, "performance_summary": performance_summary, "total": len(assets)}

def get_pmax_search_terms(client, customer_id, campaign_id=None, date_range="LAST_30_DAYS", limit=100):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range} AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign_search_term_insight.category_label,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign_search_term_insight
        WHERE {where}
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """

    search_terms = []
    try:
        for row in ga_service.search(customer_id=customer_id, query=query):
            st = row.campaign_search_term_insight
            search_terms.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "category": st.category_label if st.category_label else "Unknown",
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": round(row.metrics.cost_micros / 1000000, 2),
                    "conversions": round(row.metrics.conversions, 2)
                }
            })
    except:
        pass

    return {"search_term_categories": search_terms, "total": len(search_terms)}

def get_asset_group_previews(client, customer_id, campaign_id=None, page=1, page_size=3, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range} AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"

    offset = (page - 1) * page_size

    # First get asset groups
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group.status,
            asset_group.ad_strength,
            asset_group.primary_status,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM asset_group
        WHERE {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT {page_size}
        OFFSET {offset}
    """

    # Get total count
    count_query = f"SELECT asset_group.id FROM asset_group WHERE {where}"
    total_count = 0
    try:
        count_response = ga_service.search(customer_id=customer_id, query=count_query)
        total_count = sum(1 for _ in count_response)
    except:
        pass

    asset_groups = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        ag = row.asset_group

        ag_data = {
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "asset_group_id": ag.id,
            "asset_group_name": ag.name,
            "status": str(ag.status.name) if ag.status else "UNKNOWN",
            "ad_strength": str(ag.ad_strength.name) if ag.ad_strength else "UNSPECIFIED",
            "primary_status": str(ag.primary_status.name) if ag.primary_status else "UNKNOWN",
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2)
            },
            "headlines": [],
            "descriptions": [],
            "final_urls": [],
            "business_name": ""
        }

        # Get assets for this asset group
        assets_query = f"""
            SELECT
                asset_group_asset.field_type,
                asset.text_asset.text,
                asset.final_urls
            FROM asset_group_asset
            WHERE asset_group.id = {ag.id}
        """

        try:
            for asset_row in ga_service.search(customer_id=customer_id, query=assets_query):
                field_type = str(asset_row.asset_group_asset.field_type.name) if asset_row.asset_group_asset.field_type else ""
                text = asset_row.asset.text_asset.text if asset_row.asset.text_asset else ""

                if field_type == "HEADLINE" and text:
                    ag_data["headlines"].append(text)
                elif field_type == "DESCRIPTION" and text:
                    ag_data["descriptions"].append(text)
                elif field_type == "BUSINESS_NAME" and text:
                    ag_data["business_name"] = text

                if asset_row.asset.final_urls:
                    for url in asset_row.asset.final_urls:
                        if url not in ag_data["final_urls"]:
                            ag_data["final_urls"].append(url)
        except:
            pass

        # Generate previews for different channels
        ag_data["previews"] = {
            "search": generate_pmax_preview_html(ag_data, "search"),
            "display": generate_pmax_preview_html(ag_data, "display"),
            "youtube": generate_pmax_preview_html(ag_data, "youtube"),
            "discover": generate_pmax_preview_html(ag_data, "discover"),
            "gmail": generate_pmax_preview_html(ag_data, "gmail")
        }

        asset_groups.append(ag_data)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "asset_groups": asset_groups,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_asset_groups": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "showing": f"{offset + 1}-{min(offset + page_size, total_count)} of {total_count}"
        }
    }

def run(customer_id, action="get_full_report", login_customer_id=None, campaign_id=None, asset_group_id=None,
        page=1, date_range="LAST_30_DAYS", include_previews=True):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)
        page_size = 3  # Fixed at 3 per page

        if action == "get_placements":
            result = get_pmax_placements(client, customer_id, campaign_id, date_range)
            return {"status": "success", "report_type": "PMAX_PLACEMENTS", **result}

        elif action == "get_asset_combinations":
            result = get_asset_combinations(client, customer_id, campaign_id, asset_group_id, date_range)
            return {"status": "success", "report_type": "ASSET_COMBINATIONS", **result}

        elif action == "get_asset_performance":
            result = get_asset_performance(client, customer_id, campaign_id, asset_group_id, date_range)
            return {"status": "success", "report_type": "ASSET_PERFORMANCE", **result}

        elif action == "get_search_terms":
            result = get_pmax_search_terms(client, customer_id, campaign_id, date_range)
            return {"status": "success", "report_type": "PMAX_SEARCH_TERMS", **result}

        elif action == "view_asset_group_previews":
            result = get_asset_group_previews(client, customer_id, campaign_id, page, page_size, date_range)
            return {"status": "success", "report_type": "ASSET_GROUP_PREVIEWS", **result}

        elif action == "next_page":
            result = get_asset_group_previews(client, customer_id, campaign_id, page + 1, page_size, date_range)
            return {"status": "success", "report_type": "ASSET_GROUP_PREVIEWS", **result}

        elif action == "prev_page":
            result = get_asset_group_previews(client, customer_id, campaign_id, max(1, page - 1), page_size, date_range)
            return {"status": "success", "report_type": "ASSET_GROUP_PREVIEWS", **result}

        elif action == "get_full_report":
            placements = get_pmax_placements(client, customer_id, campaign_id, date_range, 50)
            asset_perf = get_asset_performance(client, customer_id, campaign_id, asset_group_id, date_range, 50)
            search_terms = get_pmax_search_terms(client, customer_id, campaign_id, date_range, 50)

            result = {
                "placements": placements,
                "asset_performance": asset_perf,
                "search_terms": search_terms
            }

            if include_previews:
                previews = get_asset_group_previews(client, customer_id, campaign_id, 1, 3, date_range)
                result["asset_group_previews"] = previews

            return {"status": "success", "report_type": "FULL_PMAX_REPORT", **result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
