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
        "cpc": "metrics.average_cpc",
        "quality_score": "ad_group_criterion.quality_info.quality_score",
        "bid": "ad_group_criterion.cpc_bid_micros"
    }
    return sort_map.get(sort_by, "metrics.cost_micros")

def view_keywords_paginated(client, customer_id, campaign_id=None, ad_group_id=None,
                            page=1, page_size=100, sort_by="cost", sort_order="desc",
                            filters=None, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    # Enforce page size limits
    page_size = min(max(page_size, 25), 100)

    # Build WHERE clauses
    where_clauses = [
        f"segments.date DURING {date_range}",
        "ad_group_criterion.status != 'REMOVED'",
        "ad_group_criterion.type = 'KEYWORD'"
    ]

    if campaign_id:
        where_clauses.append(f"campaign.id = {campaign_id}")
    if ad_group_id:
        where_clauses.append(f"ad_group.id = {ad_group_id}")

    if filters:
        if filters.get("status"):
            where_clauses.append(f"ad_group_criterion.status = '{filters['status']}'")
        if filters.get("match_type"):
            where_clauses.append(f"ad_group_criterion.keyword.match_type = '{filters['match_type']}'")
        if filters.get("min_quality_score"):
            where_clauses.append(f"ad_group_criterion.quality_info.quality_score >= {filters['min_quality_score']}")
        if filters.get("max_quality_score"):
            where_clauses.append(f"ad_group_criterion.quality_info.quality_score <= {filters['max_quality_score']}")
        if filters.get("min_impressions"):
            where_clauses.append(f"metrics.impressions >= {filters['min_impressions']}")
        if filters.get("min_conversions"):
            where_clauses.append(f"metrics.conversions >= {filters['min_conversions']}")
        if filters.get("has_conversions") is True:
            where_clauses.append("metrics.conversions > 0")
        if filters.get("has_conversions") is False:
            where_clauses.append("metrics.conversions = 0")

    offset = (page - 1) * page_size
    sort_field = get_sort_field(sort_by)
    order = "DESC" if sort_order.lower() == "desc" else "ASC"

    query = f"""
        SELECT
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            ad_group_criterion.cpc_bid_micros,
            ad_group_criterion.effective_cpc_bid_micros,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group_criterion.position_estimates.first_page_cpc_micros,
            ad_group_criterion.position_estimates.top_of_page_cpc_micros,
            ad_group_criterion.position_estimates.first_position_cpc_micros,
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
            metrics.cost_per_conversion,
            metrics.search_impression_share
        FROM keyword_view
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {sort_field} {order}
        LIMIT {page_size}
        OFFSET {offset}
    """

    # Get total count
    count_query = f"""
        SELECT ad_group_criterion.criterion_id
        FROM keyword_view
        WHERE {" AND ".join(where_clauses)}
    """

    total_count = 0
    try:
        count_response = ga_service.search(customer_id=customer_id, query=count_query)
        total_count = sum(1 for _ in count_response)
    except:
        pass

    keywords = []
    summary_stats = {"total_cost": 0, "total_conversions": 0, "total_clicks": 0, "low_qs_count": 0}

    for row in ga_service.search(customer_id=customer_id, query=query):
        crit = row.ad_group_criterion
        qs = crit.quality_info.quality_score if crit.quality_info.quality_score else None

        if qs and qs < 5:
            summary_stats["low_qs_count"] += 1

        cost = row.metrics.cost_micros / 1000000 if row.metrics.cost_micros else 0
        summary_stats["total_cost"] += cost
        summary_stats["total_conversions"] += row.metrics.conversions if row.metrics.conversions else 0
        summary_stats["total_clicks"] += row.metrics.clicks if row.metrics.clicks else 0

        keyword_data = {
            "criterion_id": crit.criterion_id,
            "keyword": crit.keyword.text,
            "match_type": str(crit.keyword.match_type.name),
            "status": str(crit.status.name),
            "bid": round(crit.cpc_bid_micros / 1000000, 2) if crit.cpc_bid_micros else None,
            "effective_bid": round(crit.effective_cpc_bid_micros / 1000000, 2) if crit.effective_cpc_bid_micros else None,
            "quality_score": qs,
            "qs_components": {
                "expected_ctr": str(crit.quality_info.search_predicted_ctr.name) if crit.quality_info.search_predicted_ctr else None,
                "ad_relevance": str(crit.quality_info.creative_quality_score.name) if crit.quality_info.creative_quality_score else None,
                "landing_page": str(crit.quality_info.post_click_quality_score.name) if crit.quality_info.post_click_quality_score else None
            },
            "position_estimates": {
                "first_page_cpc": round(crit.position_estimates.first_page_cpc_micros / 1000000, 2) if crit.position_estimates.first_page_cpc_micros else None,
                "top_of_page_cpc": round(crit.position_estimates.top_of_page_cpc_micros / 1000000, 2) if crit.position_estimates.top_of_page_cpc_micros else None,
                "first_position_cpc": round(crit.position_estimates.first_position_cpc_micros / 1000000, 2) if crit.position_estimates.first_position_cpc_micros else None
            },
            "ad_group_id": row.ad_group.id,
            "ad_group_name": row.ad_group.name,
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(cost, 2),
                "conversions": round(row.metrics.conversions, 2) if row.metrics.conversions else 0,
                "revenue": round(row.metrics.conversions_value, 2) if row.metrics.conversions_value else 0,
                "ctr": round(row.metrics.ctr * 100, 2) if row.metrics.ctr else 0,
                "avg_cpc": round(row.metrics.average_cpc / 1000000, 2) if row.metrics.average_cpc else 0,
                "cpa": round(row.metrics.cost_per_conversion / 1000000, 2) if row.metrics.cost_per_conversion else 0,
                "impression_share": round(row.metrics.search_impression_share * 100, 1) if row.metrics.search_impression_share else None
            }
        }

        # Add recommendation flags
        keyword_data["flags"] = []
        if qs and qs < 5:
            keyword_data["flags"].append("LOW_QS")
        if cost > 50 and (not row.metrics.conversions or row.metrics.conversions == 0):
            keyword_data["flags"].append("HIGH_COST_NO_CONV")
        if row.metrics.conversions and row.metrics.conversions > 5 and row.metrics.search_impression_share and row.metrics.search_impression_share < 0.5:
            keyword_data["flags"].append("CONVERTING_LOW_IS")

        keywords.append(keyword_data)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "keywords": keywords,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_keywords": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "showing": f"{offset + 1}-{min(offset + page_size, total_count)} of {total_count}"
        },
        "sort": {"by": sort_by, "order": sort_order},
        "filters_applied": filters or {},
        "page_summary": {
            "total_cost": round(summary_stats["total_cost"], 2),
            "total_conversions": round(summary_stats["total_conversions"], 2),
            "total_clicks": summary_stats["total_clicks"],
            "low_qs_keywords": summary_stats["low_qs_count"]
        }
    }

def get_quality_analysis(client, customer_id, campaign_id=None, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    where = f"segments.date DURING {date_range} AND ad_group_criterion.status = 'ENABLED'"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            campaign.name,
            ad_group.name,
            metrics.cost_micros,
            metrics.impressions
        FROM keyword_view
        WHERE {where}
            AND metrics.impressions > 100
        ORDER BY metrics.cost_micros DESC
        LIMIT 500
    """

    qs_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, "unknown": 0}
    component_issues = {"expected_ctr": [], "ad_relevance": [], "landing_page": []}
    priority_fixes = []

    for row in ga_service.search(customer_id=customer_id, query=query):
        qs = row.ad_group_criterion.quality_info.quality_score
        cost = row.metrics.cost_micros / 1000000 if row.metrics.cost_micros else 0

        if qs:
            qs_distribution[qs] += 1

            if qs < 5:
                fix_item = {
                    "keyword": row.ad_group_criterion.keyword.text,
                    "quality_score": qs,
                    "campaign": row.campaign.name,
                    "ad_group": row.ad_group.name,
                    "cost": round(cost, 2),
                    "issues": []
                }

                qi = row.ad_group_criterion.quality_info
                if qi.search_predicted_ctr and "BELOW" in str(qi.search_predicted_ctr.name):
                    fix_item["issues"].append("Expected CTR: Below Average")
                    component_issues["expected_ctr"].append(row.ad_group_criterion.keyword.text)
                if qi.creative_quality_score and "BELOW" in str(qi.creative_quality_score.name):
                    fix_item["issues"].append("Ad Relevance: Below Average")
                    component_issues["ad_relevance"].append(row.ad_group_criterion.keyword.text)
                if qi.post_click_quality_score and "BELOW" in str(qi.post_click_quality_score.name):
                    fix_item["issues"].append("Landing Page: Below Average")
                    component_issues["landing_page"].append(row.ad_group_criterion.keyword.text)

                priority_fixes.append(fix_item)
        else:
            qs_distribution["unknown"] += 1

    # Sort priority fixes by cost
    priority_fixes.sort(key=lambda x: x["cost"], reverse=True)

    # Generate recommendations
    recommendations = []
    if len(component_issues["expected_ctr"]) > 5:
        recommendations.append({
            "issue": "Expected CTR issues",
            "count": len(component_issues["expected_ctr"]),
            "fix": "Improve ad copy relevance and include keywords in headlines"
        })
    if len(component_issues["ad_relevance"]) > 5:
        recommendations.append({
            "issue": "Ad Relevance issues",
            "count": len(component_issues["ad_relevance"]),
            "fix": "Create more tightly themed ad groups with specific ad copy"
        })
    if len(component_issues["landing_page"]) > 5:
        recommendations.append({
            "issue": "Landing Page issues",
            "count": len(component_issues["landing_page"]),
            "fix": "Improve landing page relevance, speed, and mobile experience"
        })

    return {
        "quality_score_distribution": qs_distribution,
        "average_qs": round(sum(k * v for k, v in qs_distribution.items() if isinstance(k, int)) / max(sum(v for k, v in qs_distribution.items() if isinstance(k, int)), 1), 1),
        "priority_fixes": priority_fixes[:20],
        "recommendations": recommendations,
        "summary": {
            "low_qs_keywords": sum(qs_distribution.get(i, 0) for i in range(1, 5)),
            "average_qs_keywords": sum(qs_distribution.get(i, 0) for i in range(5, 7)),
            "high_qs_keywords": sum(qs_distribution.get(i, 0) for i in range(7, 11))
        }
    }

def run(customer_id, action="view_keywords", login_customer_id=None, campaign_id=None, ad_group_id=None,
        page=1, page_size=100, sort_by="cost", sort_order="desc", filters=None,
        keyword_id=None, date_range="LAST_30_DAYS"):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)

        if action == "view_keywords":
            result = view_keywords_paginated(
                client, customer_id, campaign_id, ad_group_id,
                page, page_size, sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        elif action == "get_quality_analysis":
            analysis = get_quality_analysis(client, customer_id, campaign_id, date_range)
            return {"status": "success", **analysis}

        elif action == "next_page":
            result = view_keywords_paginated(
                client, customer_id, campaign_id, ad_group_id,
                page + 1, page_size, sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        elif action == "prev_page":
            result = view_keywords_paginated(
                client, customer_id, campaign_id, ad_group_id,
                max(1, page - 1), page_size, sort_by, sort_order, filters, date_range
            )
            return {"status": "success", **result}

        elif action == "filter_low_qs":
            filters = filters or {}
            filters["max_quality_score"] = 4
            result = view_keywords_paginated(
                client, customer_id, campaign_id, ad_group_id,
                1, page_size, "cost", "desc", filters, date_range
            )
            return {"status": "success", **result}

        elif action == "filter_no_conversions":
            filters = filters or {}
            filters["has_conversions"] = False
            result = view_keywords_paginated(
                client, customer_id, campaign_id, ad_group_id,
                1, page_size, "cost", "desc", filters, date_range
            )
            return {"status": "success", **result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
