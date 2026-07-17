# # action Valid Values
# # Action	Required Params	Description
# # list_campaigns	—	List all Demand Gen campaigns with performance metrics
# # list_ads	—	List Demand Gen ads with multi-placement previews (paginated)
# # view_previews	—	Alias for list_ads
# # create_campaign	campaign_data	Create new Demand Gen campaign (created as PAUSED)
# # pause_campaign	campaign_id	Pause a campaign
# # enable_campaign	campaign_id	Enable a paused campaign
# # pause_ad	ad_group_id, ad_id	Pause an ad
# # enable_ad	ad_group_id, ad_id	Enable a paused ad
# # next_page	page	Fetch next page
# # prev_page	page	Fetch previous page
# # campaign_data Schema (for create_campaign)
# # {
# #   "name": "str",                                  // optional, auto-generated if omitted
# #   "daily_budget": 50.00,                          // float, default 50
# #   "bidding_strategy": "MAXIMIZE_CONVERSIONS",     // or "MAXIMIZE_CONVERSION_VALUE"
# #   "target_cpa": 10.00,                            // optional, for Max Conversions
# #   "target_roas": 4.0                              // optional, for Max Conv Value
# # }
# # Response Shape — Campaigns
# # {
# #   "status": "success",
# #   "campaign_type": "DEMAND_GEN",
# #   "count": 3,
# #   "campaigns": [
# #     {
# #       "campaign_id": 123456789,
# #       "name": "...",
# #       "status": "ENABLED",
# #       "channel_type": "DEMAND_GEN",
# #       "bidding_strategy": "MAXIMIZE_CONVERSIONS",
# #       "daily_budget": 50.00,
# #       "metrics": {
# #         "impressions": 10000,
# #         "clicks": 500,
# #         "cost": 250.00,
# #         "conversions": 30.0,
# #         "revenue": 1500.00,
# #         "roas": 6.0,
# #         "video_views": 2000
# #       }
# #     }
# #   ]
# # }
# # Response Shape — Ads
# # {
# #   "status": "success",
# #   "ad_type": "DEMAND_GEN",
# #   "ads": [
# #     {
# #       "ad_id": 123456789,
# #       "ad_name": "DemandGen-123456789",
# #       "ad_type": "DISCOVERY_MULTI_ASSET_AD",
# #       "status": "ENABLED",
# #       "approval_status": "APPROVED",
# #       "business_name": "...",
# #       "headlines": ["..."],
# #       "descriptions": ["..."],
# #       "call_to_action": "Learn More",
# #       "marketing_images_count": 3,
# #       "logo_count": 1,
# #       "final_urls": ["https://..."],
# #       "ad_group_id": 987654321,
# #       "ad_group_name": "...",
# #       "campaign_id": 111222333,
# #       "campaign_name": "...",
# #       "metrics": {
# #         "impressions": 5000,
# #         "clicks": 200,
# #         "cost": 100.00,
# #         "conversions": 15.0,
# #         "video_views": 800
# #       },
# #       "placements": ["YouTube", "YouTube Shorts", "Discover", "Gmail"],
# #       "previews": {
# #         "discover": "<div>...</div>",
# #         "youtube": "<div>...</div>",
# #         "gmail": "<div>...</div>"
# #       }
# #     }
# #   ],
# #   "pagination": { "..." }
# # }
# # Credential Configuration
try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'google-ads'])
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException

import uuid

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

def generate_demand_gen_preview_html(ad_data, placement="discover"):
    """Generate HTML preview for Demand Gen ads across different placements."""
    headline = ad_data.get('headlines', [''])[0] if ad_data.get('headlines') else 'Headline'
    description = ad_data.get('descriptions', [''])[0] if ad_data.get('descriptions') else 'Description'
    business_name = ad_data.get('business_name', 'Business')
    final_url = ad_data.get('final_urls', [''])[0] if ad_data.get('final_urls') else '#'
    cta = ad_data.get('call_to_action', 'Learn More')
    image_url = ad_data.get('image_url', '')
    logo_url = ad_data.get('logo_url', '')

    if placement == "discover":
        preview_html = f"""
        <div style="font-family: 'Google Sans', Arial, sans-serif; max-width: 340px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <div style="position: relative; height: 180px; background: linear-gradient(135deg, #4285f4, #34a853);">
                {f'<img src="{image_url}" style="width: 100%; height: 100%; object-fit: cover;" />' if image_url else '<div style="height: 100%; display: flex; align-items: center; justify-content: center; color: white;">[Discover Image]</div>'}
                <div style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.6); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">Ad</div>
            </div>
            <div style="padding: 12px;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: #4285f4; display: flex; align-items: center; justify-content: center; margin-right: 8px;">
                        {f'<img src="{logo_url}" style="width: 20px; height: 20px; border-radius: 50%;" />' if logo_url else f'<span style="color: white; font-size: 11px;">{business_name[0]}</span>'}
                    </div>
                    <span style="font-size: 13px; color: #202124; font-weight: 500;">{business_name}</span>
                </div>
                <div style="font-size: 16px; font-weight: 500; color: #202124; margin-bottom: 6px; line-height: 1.3;">{headline}</div>
                <div style="font-size: 14px; color: #5f6368; line-height: 1.4;">{description[:100]}{'...' if len(description) > 100 else ''}</div>
            </div>
        </div>
        """
    elif placement == "youtube":
        preview_html = f"""
        <div style="font-family: 'YouTube Sans', Arial, sans-serif; max-width: 340px; background: #0f0f0f; border-radius: 12px; overflow: hidden;">
            <div style="position: relative; height: 190px; background: #272727;">
                {f'<img src="{image_url}" style="width: 100%; height: 100%; object-fit: cover;" />' if image_url else '<div style="height: 100%; display: flex; align-items: center; justify-content: center; color: #aaa;">[Video Thumbnail]</div>'}
                <div style="position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; padding: 2px 4px; border-radius: 2px; font-size: 11px;">Ad · 0:30</div>
            </div>
            <div style="padding: 12px;">
                <div style="display: flex;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: #ff0000; display: flex; align-items: center; justify-content: center; margin-right: 12px; flex-shrink: 0;">
                        {f'<img src="{logo_url}" style="width: 36px; height: 36px; border-radius: 50%;" />' if logo_url else f'<span style="color: white; font-size: 14px;">{business_name[0]}</span>'}
                    </div>
                    <div>
                        <div style="font-size: 14px; color: #f1f1f1; font-weight: 500; line-height: 1.3; margin-bottom: 4px;">{headline}</div>
                        <div style="font-size: 12px; color: #aaa;">{business_name} · Sponsored</div>
                    </div>
                </div>
            </div>
        </div>
        """
    elif placement == "gmail":
        preview_html = f"""
        <div style="font-family: 'Google Sans', Arial, sans-serif; max-width: 360px; background: #fff; border: 1px solid #dadce0; border-radius: 8px; overflow: hidden;">
            <div style="padding: 16px; border-bottom: 1px solid #dadce0;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #fbbc04; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                        {f'<img src="{logo_url}" style="width: 32px; height: 32px; border-radius: 50%;" />' if logo_url else f'<span style="color: white; font-size: 16px; font-weight: 500;">{business_name[0]}</span>'}
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 14px; font-weight: 500; color: #202124;">{business_name}</span>
                            <span style="font-size: 12px; color: #5f6368;">Ad</span>
                        </div>
                        <div style="font-size: 12px; color: #5f6368;">Sponsored</div>
                    </div>
                </div>
            </div>
            <div style="padding: 16px;">
                <div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 4px;">{headline}</div>
                <div style="font-size: 13px; color: #5f6368; line-height: 1.4;">{description[:120]}{'...' if len(description) > 120 else ''}</div>
            </div>
            {f'<div style="height: 120px; background: #f1f3f4;"><img src="{image_url}" style="width: 100%; height: 100%; object-fit: cover;" /></div>' if image_url else ''}
            <div style="padding: 12px; text-align: right;">
                <button style="background: #1a73e8; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; cursor: pointer;">{cta}</button>
            </div>
        </div>
        """
    else:
        preview_html = "<div>Preview not available</div>"

    return preview_html

def list_demand_gen_campaigns(client, customer_id, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.video_views
        FROM campaign
        WHERE campaign.advertising_channel_type = 'DEMAND_GEN'
            AND campaign.status != 'REMOVED'
            AND segments.date DURING {date_range}
        ORDER BY metrics.cost_micros DESC
    """

    campaigns = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        roas = row.metrics.conversions_value / (row.metrics.cost_micros / 1000000) if row.metrics.cost_micros > 0 else 0
        campaigns.append({
            "campaign_id": row.campaign.id,
            "name": row.campaign.name,
            "status": str(row.campaign.status.name),
            "channel_type": "DEMAND_GEN",
            "bidding_strategy": str(row.campaign.bidding_strategy_type.name) if row.campaign.bidding_strategy_type else "UNKNOWN",
            "daily_budget": round(row.campaign_budget.amount_micros / 1000000, 2) if row.campaign_budget.amount_micros else 0,
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2),
                "revenue": round(row.metrics.conversions_value, 2),
                "roas": round(roas, 2),
                "video_views": row.metrics.video_views if row.metrics.video_views else 0
            }
        })
    return campaigns

def list_demand_gen_ads(client, customer_id, campaign_id=None, ad_group_id=None, page=1, page_size=3, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    where_clauses = [
        f"segments.date DURING {date_range}",
        "campaign.advertising_channel_type = 'DEMAND_GEN'",
        "ad_group_ad.status != 'REMOVED'"
    ]

    if campaign_id:
        where_clauses.append(f"campaign.id = {campaign_id}")
    if ad_group_id:
        where_clauses.append(f"ad_group.id = {ad_group_id}")

    offset = (page - 1) * page_size

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.name,
            ad_group_ad.ad.type,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.discovery_multi_asset_ad.headlines,
            ad_group_ad.ad.discovery_multi_asset_ad.descriptions,
            ad_group_ad.ad.discovery_multi_asset_ad.marketing_images,
            ad_group_ad.ad.discovery_multi_asset_ad.square_marketing_images,
            ad_group_ad.ad.discovery_multi_asset_ad.portrait_marketing_images,
            ad_group_ad.ad.discovery_multi_asset_ad.logo_images,
            ad_group_ad.ad.discovery_multi_asset_ad.business_name,
            ad_group_ad.ad.discovery_multi_asset_ad.call_to_action_text,
            ad_group_ad.ad.discovery_carousel_ad.headlines,
            ad_group_ad.ad.discovery_carousel_ad.description,
            ad_group_ad.ad.discovery_carousel_ad.business_name,
            ad_group_ad.ad.discovery_carousel_ad.logo_image,
            ad_group_ad.ad.discovery_carousel_ad.call_to_action_text,
            ad_group_ad.ad.discovery_video_responsive_ad.headlines,
            ad_group_ad.ad.discovery_video_responsive_ad.long_headlines,
            ad_group_ad.ad.discovery_video_responsive_ad.descriptions,
            ad_group_ad.ad.discovery_video_responsive_ad.business_name,
            ad_group_ad.status,
            ad_group_ad.policy_summary.approval_status,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.video_views
        FROM ad_group_ad
        WHERE {" AND ".join(where_clauses)}
        ORDER BY metrics.impressions DESC
        LIMIT {page_size}
        OFFSET {offset}
    """

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
        ad = row.ad_group_ad.ad
        ad_type = str(ad.type_.name) if ad.type_ else "UNKNOWN"

        headlines = []
        descriptions = []
        business_name = ""
        cta = "Learn More"

        if ad.discovery_multi_asset_ad:
            dma = ad.discovery_multi_asset_ad
            headlines = [h.text for h in dma.headlines] if dma.headlines else []
            descriptions = [d.text for d in dma.descriptions] if dma.descriptions else []
            business_name = dma.business_name if dma.business_name else ""
            cta = dma.call_to_action_text if dma.call_to_action_text else "Learn More"
            marketing_images_count = len(dma.marketing_images) if dma.marketing_images else 0
            logo_count = len(dma.logo_images) if dma.logo_images else 0
        elif ad.discovery_carousel_ad:
            dca = ad.discovery_carousel_ad
            headlines = [h.text for h in dca.headlines] if dca.headlines else []
            descriptions = [dca.description.text] if dca.description else []
            business_name = dca.business_name if dca.business_name else ""
            cta = dca.call_to_action_text if dca.call_to_action_text else "Learn More"
            marketing_images_count = 0
            logo_count = 1 if dca.logo_image else 0
        elif ad.discovery_video_responsive_ad:
            dvra = ad.discovery_video_responsive_ad
            headlines = [h.text for h in dvra.headlines] if dvra.headlines else []
            descriptions = [d.text for d in dvra.descriptions] if dvra.descriptions else []
            business_name = dvra.business_name if dvra.business_name else ""
            cta = "Watch Now"
            marketing_images_count = 0
            logo_count = 0
        else:
            marketing_images_count = 0
            logo_count = 0

        ad_data = {
            "ad_id": ad.id,
            "ad_name": ad.name if ad.name else f"DemandGen-{ad.id}",
            "ad_type": ad_type,
            "status": str(row.ad_group_ad.status.name) if row.ad_group_ad.status else "UNKNOWN",
            "approval_status": str(row.ad_group_ad.policy_summary.approval_status.name) if row.ad_group_ad.policy_summary.approval_status else "UNKNOWN",
            "business_name": business_name,
            "headlines": headlines,
            "descriptions": descriptions,
            "call_to_action": cta,
            "marketing_images_count": marketing_images_count,
            "logo_count": logo_count,
            "final_urls": list(ad.final_urls) if ad.final_urls else [],
            "ad_group_id": row.ad_group.id,
            "ad_group_name": row.ad_group.name,
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "metrics": {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": round(row.metrics.cost_micros / 1000000, 2),
                "conversions": round(row.metrics.conversions, 2),
                "video_views": row.metrics.video_views if row.metrics.video_views else 0
            },
            "placements": ["YouTube", "YouTube Shorts", "Discover", "Gmail"]
        }

        ad_data["previews"] = {
            "discover": generate_demand_gen_preview_html(ad_data, "discover"),
            "youtube": generate_demand_gen_preview_html(ad_data, "youtube"),
            "gmail": generate_demand_gen_preview_html(ad_data, "gmail")
        }

        ads.append(ad_data)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "ads": ads,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_ads": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "showing": f"{offset + 1}-{min(offset + page_size, total_count)} of {total_count}"
        }
    }

def create_demand_gen_campaign(client, customer_id, campaign_data):
    campaign_service = client.get_service("CampaignService")
    budget_service = client.get_service("CampaignBudgetService")

    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"DemandGen_Budget_{uuid.uuid4().hex[:8]}"
    budget.amount_micros = int(float(campaign_data.get("daily_budget", 50)) * 1000000)
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

    budget_response = budget_service.mutate_campaign_budgets(customer_id=customer_id, operations=[budget_op])
    budget_resource = budget_response.results[0].resource_name

    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.create
    campaign.name = campaign_data.get("name", f"DemandGen_Campaign_{uuid.uuid4().hex[:8]}")
    campaign.campaign_budget = budget_resource
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.DEMAND_GEN
    campaign.status = client.enums.CampaignStatusEnum.PAUSED

    bidding = campaign_data.get("bidding_strategy", "MAXIMIZE_CONVERSIONS")
    if bidding == "MAXIMIZE_CONVERSIONS":
        if campaign_data.get("target_cpa"):
            campaign.maximize_conversions.target_cpa_micros = int(float(campaign_data["target_cpa"]) * 1000000)
        else:
            campaign.maximize_conversions.target_cpa_micros = 0
    elif bidding == "MAXIMIZE_CONVERSION_VALUE":
        if campaign_data.get("target_roas"):
            campaign.maximize_conversion_value.target_roas = float(campaign_data["target_roas"])

    response = campaign_service.mutate_campaigns(customer_id=customer_id, operations=[campaign_op])

    return {
        "resource_name": response.results[0].resource_name,
        "budget_resource": budget_resource,
        "campaign_type": "DEMAND_GEN",
        "status": "created"
    }

def update_campaign_status(client, customer_id, campaign_id, new_status):
    campaign_service = client.get_service("CampaignService")
    operation = client.get_type("CampaignOperation")

    campaign = operation.update
    campaign.resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
    campaign.status = client.enums.CampaignStatusEnum[new_status]
    operation.update_mask.paths.append("status")

    response = campaign_service.mutate_campaigns(customer_id=customer_id, operations=[operation])
    return {"resource_name": response.results[0].resource_name, "new_status": new_status}

def update_ad_status(client, customer_id, ad_group_id, ad_id, new_status):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    operation = client.get_type("AdGroupAdOperation")

    ad_group_ad = operation.update
    ad_group_ad.resource_name = f"customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}"
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum[new_status]
    operation.update_mask.paths.append("status")

    response = ad_group_ad_service.mutate_ad_group_ads(customer_id=customer_id, operations=[operation])
    return {"resource_name": response.results[0].resource_name, "new_status": new_status}

def run(customer_id, action="list_campaigns", login_customer_id=None, campaign_id=None, ad_group_id=None,
        ad_id=None, page=1, campaign_data=None, ad_data=None, date_range="LAST_30_DAYS"):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)
        page_size = 3

        if action == "list_campaigns":
            campaigns = list_demand_gen_campaigns(client, customer_id, date_range)
            return {"status": "success", "campaign_type": "DEMAND_GEN", "count": len(campaigns), "campaigns": campaigns}

        elif action in ["list_ads", "view_previews"]:
            result = list_demand_gen_ads(client, customer_id, campaign_id, ad_group_id, page, page_size, date_range)
            return {"status": "success", "ad_type": "DEMAND_GEN", **result}

        elif action == "create_campaign":
            if not campaign_data:
                return {"status": "error", "message": "campaign_data required"}
            result = create_demand_gen_campaign(client, customer_id, campaign_data)
            return {"status": "success", **result}

        elif action == "pause_campaign":
            if not campaign_id:
                return {"status": "error", "message": "campaign_id required"}
            result = update_campaign_status(client, customer_id, campaign_id, "PAUSED")
            return {"status": "success", **result}

        elif action == "enable_campaign":
            if not campaign_id:
                return {"status": "error", "message": "campaign_id required"}
            result = update_campaign_status(client, customer_id, campaign_id, "ENABLED")
            return {"status": "success", **result}

        elif action == "pause_ad":
            if not ad_group_id or not ad_id:
                return {"status": "error", "message": "ad_group_id and ad_id required"}
            result = update_ad_status(client, customer_id, ad_group_id, ad_id, "PAUSED")
            return {"status": "success", **result}

        elif action == "enable_ad":
            if not ad_group_id or not ad_id:
                return {"status": "error", "message": "ad_group_id and ad_id required"}
            result = update_ad_status(client, customer_id, ad_group_id, ad_id, "ENABLED")
            return {"status": "success", **result}

        elif action == "next_page":
            result = list_demand_gen_ads(client, customer_id, campaign_id, ad_group_id, page + 1, page_size, date_range)
            return {"status": "success", "ad_type": "DEMAND_GEN", **result}

        elif action == "prev_page":
            result = list_demand_gen_ads(client, customer_id, campaign_id, ad_group_id, max(1, page - 1), page_size, date_range)
            return {"status": "success", "ad_type": "DEMAND_GEN", **result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
