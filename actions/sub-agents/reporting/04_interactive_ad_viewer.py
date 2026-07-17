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

def get_sort_field(sort_by):
    sort_map = {
        "impressions": "metrics.impressions",
        "clicks": "metrics.clicks",
        "cost": "metrics.cost_micros",
        "conversions": "metrics.conversions",
        "ctr": "metrics.ctr",
        "ad_strength": "ad_group_ad.ad_strength"
    }
    return sort_map.get(sort_by, "metrics.impressions")

def view_ads_paginated(client, customer_id, campaign_id=None, ad_group_id=None,
                       batch_size=3, page=1, sort_by="impressions", sort_order="desc",
                       filters=None, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    # Build WHERE clauses
    where_clauses = [
        f"segments.date DURING {date_range}",
        "ad_group_ad.status != 'REMOVED'"
    ]

    if campaign_id:
        where_clauses.append(f"campaign.id = {campaign_id}")
    if ad_group_id:
        where_clauses.append(f"ad_group.id = {ad_group_id}")

    if filters:
        if filters.get("status"):
            where_clauses.append(f"ad_group_ad.status = '{filters['status']}'")
        if filters.get("ad_type"):
            where_clauses.append(f"ad_group_ad.ad.type = '{filters['ad_type']}'")
        if filters.get("ad_strength"):
            where_clauses.append(f"ad_group_ad.ad_strength = '{filters['ad_strength']}'")
        if filters.get("min_impressions"):
            where_clauses.append(f"metrics.impressions >= {filters['min_impressions']}")
        if filters.get("min_clicks"):
            where_clauses.append(f"metrics.clicks >= {filters['min_clicks']}")

    # Calculate offset
    batch_size = min(max(batch_size, 1), 3)  # Enforce 1-3 range
    offset = (page - 1) * batch_size

    # Build sort
    sort_field = get_sort_field(sort_by)
    order = "DESC" if sort_order.lower() == "desc" else "ASC"

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.responsive_search_ad.path1,
            ad_group_ad.ad.responsive_search_ad.path2,
            ad_group_ad.ad.expanded_text_ad.headline_part1,
            ad_group_ad.ad.expanded_text_ad.headline_part2,
            ad_group_ad.ad.expanded_text_ad.headline_part3,
            ad_group_ad.ad.expanded_text_ad.description,
            ad_group_ad.ad.expanded_text_ad.description2,
            ad_group_ad.status,
            ad_group_ad.ad_strength,
            ad_group_ad.policy_summary.approval_status,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM ad_group_ad
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {sort_field} {order}
        LIMIT {batch_size}
        OFFSET {offset}
    """

    # Also get total count
    count_query = f"""
        SELECT ad_group_ad.ad.id
        FROM ad_group_ad
        WHERE {" AND ".join(where_clauses)}
    """

    total_count = 0
    try:
        count_response = ga_service.search(customer_id=customer_id, query=count_query)
        total_count = sum(1 for _ in count_response)
    except:
        pass

    ads = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        ad_data = {
            "ad_id": row.ad_group_ad.ad.id,
            "ad_type": str(row.ad_group_ad.ad.type_.name) if row.ad_group_ad.ad.type_ else "UNKNOWN",
            "status": str(row.ad_group_ad.status.name) if row.ad_group_ad.status else "UNKNOWN",
            "ad_strength": str(row.ad_group_ad.ad_strength.name) if row.ad_group_ad.ad_strength else "UNSPECIFIED",
            "approval_status": str(row.ad_group_ad.policy_summary.approval_status.name) if row.ad_group_ad.policy_summary.approval_status else "UNKNOWN",
            "final_urls": list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else [],
            "ad_group_id": row.ad_group.id,
            "ad_group_name": row.ad_group.name,
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2),
                "ctr": round(row.metrics.ctr * 100, 2) if row.metrics.ctr else 0,
                "avg_cpc": round(row.metrics.average_cpc / 1000000, 2) if row.metrics.average_cpc else 0
            }
        }

        # Handle RSA ads
        if row.ad_group_ad.ad.responsive_search_ad:
            rsa = row.ad_group_ad.ad.responsive_search_ad
            ad_data["rsa_details"] = {
                "headlines": [],
                "descriptions": [],
                "path1": rsa.path1 if rsa.path1 else "",
                "path2": rsa.path2 if rsa.path2 else ""
            }
            for h in rsa.headlines:
                pinned = ""
                if h.pinned_field:
                    pinned = f" [PINNED: {h.pinned_field.name}]"
                ad_data["rsa_details"]["headlines"].append({
                    "text": h.text,
                    "pinned": str(h.pinned_field.name) if h.pinned_field and h.pinned_field != 0 else None
                })
            for d in rsa.descriptions:
                ad_data["rsa_details"]["descriptions"].append({
                    "text": d.text,
                    "pinned": str(d.pinned_field.name) if d.pinned_field and d.pinned_field != 0 else None
                })

        # Handle ETA ads (legacy)
        if row.ad_group_ad.ad.expanded_text_ad:
            eta = row.ad_group_ad.ad.expanded_text_ad
            ad_data["eta_details"] = {
                "headline1": eta.headline_part1 if eta.headline_part1 else "",
                "headline2": eta.headline_part2 if eta.headline_part2 else "",
                "headline3": eta.headline_part3 if eta.headline_part3 else "",
                "description1": eta.description if eta.description else "",
                "description2": eta.description2 if eta.description2 else ""
            }

        ads.append(ad_data)

    # Calculate pagination info
    total_pages = (total_count + batch_size - 1) // batch_size if total_count > 0 else 1

    return {
        "ads": ads,
        "pagination": {
            "current_page": page,
            "batch_size": batch_size,
            "total_ads": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "showing": f"{offset + 1}-{min(offset + batch_size, total_count)} of {total_count}"
        },
        "sort": {
            "by": sort_by,
            "order": sort_order
        },
        "filters_applied": filters or {}
    }

def get_ad_detail(client, customer_id, ad_group_id, ad_id, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.responsive_search_ad.path1,
            ad_group_ad.ad.responsive_search_ad.path2,
            ad_group_ad.status,
            ad_group_ad.ad_strength,
            ad_group_ad.policy_summary.approval_status,
            ad_group_ad.policy_summary.policy_topic_entries,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_per_conversion
        FROM ad_group_ad
        WHERE ad_group_ad.ad.id = {ad_id}
            AND ad_group.id = {ad_group_id}
            AND segments.date DURING {date_range}
    """

    for row in ga_service.search(customer_id=customer_id, query=query):
        ad = row.ad_group_ad.ad
        detail = {
            "ad_id": ad.id,
            "ad_type": str(ad.type_.name) if ad.type_ else "UNKNOWN",
            "status": str(row.ad_group_ad.status.name),
            "ad_strength": str(row.ad_group_ad.ad_strength.name) if row.ad_group_ad.ad_strength else "UNSPECIFIED",
            "approval_status": str(row.ad_group_ad.policy_summary.approval_status.name) if row.ad_group_ad.policy_summary.approval_status else "UNKNOWN",
            "final_urls": list(ad.final_urls) if ad.final_urls else [],
            "ad_group": {"id": row.ad_group.id, "name": row.ad_group.name},
            "campaign": {"id": row.campaign.id, "name": row.campaign.name},
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2),
                "revenue": round(row.metrics.conversions_value, 2),
                "ctr": round(row.metrics.ctr * 100, 2) if row.metrics.ctr else 0,
                "avg_cpc": round(row.metrics.average_cpc / 1000000, 2) if row.metrics.average_cpc else 0,
                "cpa": round(row.metrics.cost_per_conversion / 1000000, 2) if row.metrics.cost_per_conversion else 0
            },
            "policy_issues": []
        }

        # Policy issues
        if row.ad_group_ad.policy_summary.policy_topic_entries:
            for entry in row.ad_group_ad.policy_summary.policy_topic_entries:
                detail["policy_issues"].append({
                    "topic": entry.topic if entry.topic else "Unknown",
                    "type": str(entry.type_.name) if entry.type_ else "UNKNOWN"
                })

        # RSA details
        if ad.responsive_search_ad:
            rsa = ad.responsive_search_ad
            detail["rsa_assets"] = {
                "headlines": [{"text": h.text, "pinned": str(h.pinned_field.name) if h.pinned_field and h.pinned_field != 0 else None} for h in rsa.headlines],
                "descriptions": [{"text": d.text, "pinned": str(d.pinned_field.name) if d.pinned_field and d.pinned_field != 0 else None} for d in rsa.descriptions],
                "path1": rsa.path1 if rsa.path1 else "",
                "path2": rsa.path2 if rsa.path2 else "",
                "headline_count": len(rsa.headlines),
                "description_count": len(rsa.descriptions)
            }

            # Ad strength recommendations
            detail["recommendations"] = []
            if len(rsa.headlines) < 10:
                detail["recommendations"].append(f"Add {10 - len(rsa.headlines)} more headlines (have {len(rsa.headlines)}/15)")
            if len(rsa.descriptions) < 3:
                detail["recommendations"].append(f"Add {3 - len(rsa.descriptions)} more descriptions (have {len(rsa.descriptions)}/4)")

        return detail

    return None

def run(customer_id, action="view_ads", login_customer_id=None, campaign_id=None, ad_group_id=None,
        batch_size=3, page=1, sort_by="impressions", sort_order="desc", filters=None,
        ad_id=None, date_range="LAST_30_DAYS"):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)

        if action == "view_ads":
            result = view_ads_paginated(
                client, customer_id, campaign_id, ad_group_id,
                batch_size, page, sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        elif action == "view_ad_detail":
            if not ad_id or not ad_group_id:
                return {"status": "error", "message": "ad_id and ad_group_id required"}
            detail = get_ad_detail(client, customer_id, ad_group_id, ad_id, date_range)
            if detail:
                return {"status": "success", "ad_detail": detail}
            else:
                return {"status": "error", "message": "Ad not found"}

        elif action == "next_page":
            result = view_ads_paginated(
                client, customer_id, campaign_id, ad_group_id,
                batch_size, page + 1, sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        elif action == "prev_page":
            result = view_ads_paginated(
                client, customer_id, campaign_id, ad_group_id,
                batch_size, max(1, page - 1), sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
