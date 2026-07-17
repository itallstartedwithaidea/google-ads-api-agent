# # action Valid Values
# # Action	Required Params	Description
# # list	—	List RDAs with metrics & HTML previews (paginated)
# # view_previews	—	Alias for list
# # create	ad_group_id, ad_data	Create new RDA (created as PAUSED)
# # pause	ad_group_id, ad_id	Pause an ad
# # enable	ad_group_id, ad_id	Enable a paused ad
# # next_page	page	Fetch next page
# # prev_page	page	Fetch previous page
# # ad_data Schema (for create)
# # {
# #   "headlines": ["str", "..."],                    // min 1, max 5 (required)
# #   "long_headline": "str",                         // required
# #   "descriptions": ["str", "..."],                 // min 1, max 5 (required)
# #   "business_name": "str",                         // required
# #   "final_urls": ["str", "..."],                   // min 1 (required)
# #   "marketing_image_assets": ["resource_name"],    // optional — landscape 1.91:1
# #   "square_marketing_image_assets": ["resource_name"], // optional — square 1:1
# #   "logo_image_assets": ["resource_name"],         // optional
# #   "main_color": "#hex",                           // optional
# #   "accent_color": "#hex",                         // optional
# #   "call_to_action_text": "str",                   // optional
# #   "allow_flexible_color": true,                   // optional, default true
# #   "format_setting": "ALL_FORMATS"                 // optional
# # }
# # Response Shape
# # {
# #   "status": "success",
# #   "ad_type": "RESPONSIVE_DISPLAY_AD",
# #   "ads": [
# #     {
# #       "ad_id": 123456789,
# #       "ad_name": "RDA-123456789",
# #       "status": "ENABLED",
# #       "approval_status": "APPROVED",
# #       "business_name": "...",
# #       "headlines": ["..."],
# #       "long_headline": "...",
# #       "descriptions": ["..."],
# #       "marketing_images_count": 2,
# #       "square_images_count": 1,
# #       "logo_images_count": 1,
# #       "main_color": "#1a73e8",
# #       "accent_color": "#ffffff",
# #       "call_to_action_text": "Learn More",
# #       "allow_flexible_color": true,
# #       "format_setting": "ALL_FORMATS",
# #       "final_urls": ["https://..."],
# #       "ad_group_id": 987654321,
# #       "ad_group_name": "...",
# #       "campaign_id": 111222333,
# #       "campaign_name": "...",
# #       "metrics": {
# #         "impressions": 1000,
# #         "clicks": 50,
# #         "cost": 25.00,
# #         "conversions": 3.0,
# #         "ctr": 5.0,
# #         "avg_cpc": 0.50
# #       },
# #       "preview_html": "<div>...</div>"
# #     }
# #   ],
# #   "pagination": {
# #     "current_page": 1,
# #     "page_size": 3,
# #     "total_ads": 12,
# #     "total_pages": 4,
# #     "has_next": true,
# #     "has_prev": false,
# #     "showing": "1-3 of 12"
# #   }
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

def generate_rda_preview_html(ad_data):
    """Generate HTML preview for a Responsive Display Ad."""
    headline = ad_data.get('headlines', [''])[0] if ad_data.get('headlines') else 'Headline'
    long_headline = ad_data.get('long_headline', 'Long Headline')
    description = ad_data.get('descriptions', [''])[0] if ad_data.get('descriptions') else 'Description'
    business_name = ad_data.get('business_name', 'Business')
    final_url = ad_data.get('final_urls', [''])[0] if ad_data.get('final_urls') else '#'
    main_color = ad_data.get('main_color', '#1a73e8')
    accent_color = ad_data.get('accent_color', '#ffffff')
    cta = ad_data.get('call_to_action_text', 'Learn More')
    marketing_image = ad_data.get('marketing_image_url', '')
    logo_url = ad_data.get('logo_url', '')

    preview_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 336px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="position: relative;">
            <div style="background: linear-gradient(135deg, {main_color}, {accent_color}); height: 176px; display: flex; align-items: center; justify-content: center;">
                {f'<img src="{marketing_image}" style="width: 100%; height: 100%; object-fit: cover;" />' if marketing_image else f'<span style="color: white; font-size: 14px;">[Marketing Image]</span>'}
            </div>
        </div>
        <div style="padding: 12px; background: white;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: {main_color}; display: flex; align-items: center; justify-content: center; margin-right: 8px;">
                    {f'<img src="{logo_url}" style="width: 24px; height: 24px; border-radius: 50%;" />' if logo_url else f'<span style="color: white; font-size: 12px;">{business_name[0] if business_name else "B"}</span>'}
                </div>
                <span style="font-size: 12px; color: #5f6368;">{business_name}</span>
            </div>
            <div style="font-size: 16px; font-weight: 500; color: #202124; margin-bottom: 4px; line-height: 1.3;">{headline}</div>
            <div style="font-size: 14px; color: #5f6368; margin-bottom: 8px; line-height: 1.4;">{description[:90]}{'...' if len(description) > 90 else ''}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #70757a;">Ad · {final_url.replace('https://', '').replace('http://', '').split('/')[0][:30]}</span>
                <button style="background: {main_color}; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; cursor: pointer;">{cta}</button>
            </div>
        </div>
    </div>
    """
    return preview_html

def list_responsive_display_ads(client, customer_id, campaign_id=None, ad_group_id=None, page=1, page_size=3, date_range="LAST_30_DAYS"):
    ga_service = client.get_service("GoogleAdsService")

    where_clauses = [
        f"segments.date DURING {date_range}",
        "ad_group_ad.ad.type = 'RESPONSIVE_DISPLAY_AD'",
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
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.responsive_display_ad.business_name,
            ad_group_ad.ad.responsive_display_ad.headlines,
            ad_group_ad.ad.responsive_display_ad.long_headline,
            ad_group_ad.ad.responsive_display_ad.descriptions,
            ad_group_ad.ad.responsive_display_ad.marketing_images,
            ad_group_ad.ad.responsive_display_ad.square_marketing_images,
            ad_group_ad.ad.responsive_display_ad.logo_images,
            ad_group_ad.ad.responsive_display_ad.square_logo_images,
            ad_group_ad.ad.responsive_display_ad.main_color,
            ad_group_ad.ad.responsive_display_ad.accent_color,
            ad_group_ad.ad.responsive_display_ad.call_to_action_text,
            ad_group_ad.ad.responsive_display_ad.allow_flexible_color,
            ad_group_ad.ad.responsive_display_ad.format_setting,
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
            metrics.ctr,
            metrics.average_cpc
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
        rda = row.ad_group_ad.ad.responsive_display_ad

        headlines = [h.text for h in rda.headlines] if rda.headlines else []
        descriptions = [d.text for d in rda.descriptions] if rda.descriptions else []
        long_headline = rda.long_headline.text if rda.long_headline else ""
        marketing_images = [img.asset for img in rda.marketing_images] if rda.marketing_images else []
        square_images = [img.asset for img in rda.square_marketing_images] if rda.square_marketing_images else []
        logo_images = [img.asset for img in rda.logo_images] if rda.logo_images else []

        ad_data = {
            "ad_id": row.ad_group_ad.ad.id,
            "ad_name": row.ad_group_ad.ad.name if row.ad_group_ad.ad.name else f"RDA-{row.ad_group_ad.ad.id}",
            "status": str(row.ad_group_ad.status.name) if row.ad_group_ad.status else "UNKNOWN",
            "approval_status": str(row.ad_group_ad.policy_summary.approval_status.name) if row.ad_group_ad.policy_summary.approval_status else "UNKNOWN",
            "business_name": rda.business_name if rda.business_name else "",
            "headlines": headlines,
            "long_headline": long_headline,
            "descriptions": descriptions,
            "marketing_images_count": len(marketing_images),
            "square_images_count": len(square_images),
            "logo_images_count": len(logo_images),
            "main_color": rda.main_color if rda.main_color else "#1a73e8",
            "accent_color": rda.accent_color if rda.accent_color else "#ffffff",
            "call_to_action_text": rda.call_to_action_text if rda.call_to_action_text else "Learn More",
            "allow_flexible_color": rda.allow_flexible_color if rda.allow_flexible_color else False,
            "format_setting": str(rda.format_setting.name) if rda.format_setting else "ALL_FORMATS",
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

        ad_data["preview_html"] = generate_rda_preview_html(ad_data)
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

def create_responsive_display_ad(client, customer_id, ad_group_id, ad_data):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    asset_service = client.get_service("AssetService")

    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create
    ad_group_ad.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

    rda = ad_group_ad.ad.responsive_display_ad

    rda.business_name = ad_data.get("business_name", "Business")

    for headline in ad_data.get("headlines", [])[:5]:
        headline_asset = client.get_type("AdTextAsset")
        headline_asset.text = headline
        rda.headlines.append(headline_asset)

    if ad_data.get("long_headline"):
        rda.long_headline.text = ad_data["long_headline"]

    for desc in ad_data.get("descriptions", [])[:5]:
        desc_asset = client.get_type("AdTextAsset")
        desc_asset.text = desc
        rda.descriptions.append(desc_asset)

    if ad_data.get("final_urls"):
        ad_group_ad.ad.final_urls.extend(ad_data["final_urls"])

    if ad_data.get("main_color"):
        rda.main_color = ad_data["main_color"]
    if ad_data.get("accent_color"):
        rda.accent_color = ad_data["accent_color"]

    if ad_data.get("call_to_action_text"):
        rda.call_to_action_text = ad_data["call_to_action_text"]

    rda.allow_flexible_color = ad_data.get("allow_flexible_color", True)

    if ad_data.get("format_setting"):
        rda.format_setting = client.enums.DisplayAdFormatSettingEnum[ad_data["format_setting"]]

    if ad_data.get("marketing_image_assets"):
        for asset_name in ad_data["marketing_image_assets"]:
            img = client.get_type("AdImageAsset")
            img.asset = asset_name
            rda.marketing_images.append(img)

    if ad_data.get("square_marketing_image_assets"):
        for asset_name in ad_data["square_marketing_image_assets"]:
            img = client.get_type("AdImageAsset")
            img.asset = asset_name
            rda.square_marketing_images.append(img)

    if ad_data.get("logo_image_assets"):
        for asset_name in ad_data["logo_image_assets"]:
            img = client.get_type("AdImageAsset")
            img.asset = asset_name
            rda.logo_images.append(img)

    response = ad_group_ad_service.mutate_ad_group_ads(customer_id=customer_id, operations=[operation])

    return {
        "resource_name": response.results[0].resource_name,
        "status": "created",
        "ad_type": "RESPONSIVE_DISPLAY_AD"
    }

def update_rda_status(client, customer_id, ad_group_id, ad_id, new_status):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    operation = client.get_type("AdGroupAdOperation")

    ad_group_ad = operation.update
    ad_group_ad.resource_name = f"customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}"
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum[new_status]
    operation.update_mask.paths.append("status")

    response = ad_group_ad_service.mutate_ad_group_ads(customer_id=customer_id, operations=[operation])
    return {"resource_name": response.results[0].resource_name, "new_status": new_status}

def run(customer_id, action="list", login_customer_id=None, campaign_id=None, ad_group_id=None,
        ad_id=None, page=1, ad_data=None, date_range="LAST_30_DAYS"):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)
        page_size = 3

        if action in ["list", "view_previews"]:
            result = list_responsive_display_ads(client, customer_id, campaign_id, ad_group_id, page, page_size, date_range)
            return {"status": "success", "ad_type": "RESPONSIVE_DISPLAY_AD", **result}

        elif action == "create":
            if not ad_group_id or not ad_data:
                return {"status": "error", "message": "ad_group_id and ad_data required"}
            if not ad_data.get("headlines") or len(ad_data["headlines"]) < 1:
                return {"status": "error", "message": "At least 1 headline required"}
            if not ad_data.get("long_headline"):
                return {"status": "error", "message": "long_headline required"}
            if not ad_data.get("descriptions") or len(ad_data["descriptions"]) < 1:
                return {"status": "error", "message": "At least 1 description required"}
            if not ad_data.get("business_name"):
                return {"status": "error", "message": "business_name required"}
            if not ad_data.get("final_urls"):
                return {"status": "error", "message": "At least 1 final URL required"}
            result = create_responsive_display_ad(client, customer_id, ad_group_id, ad_data)
            return {"status": "success", **result}

        elif action == "pause":
            if not ad_group_id or not ad_id:
                return {"status": "error", "message": "ad_group_id and ad_id required"}
            result = update_rda_status(client, customer_id, ad_group_id, ad_id, "PAUSED")
            return {"status": "success", **result}

        elif action == "enable":
            if not ad_group_id or not ad_id:
                return {"status": "error", "message": "ad_group_id and ad_id required"}
            result = update_rda_status(client, customer_id, ad_group_id, ad_id, "ENABLED")
            return {"status": "success", **result}

        elif action == "next_page":
            result = list_responsive_display_ads(client, customer_id, campaign_id, ad_group_id, page + 1, page_size, date_range)
            return {"status": "success", "ad_type": "RESPONSIVE_DISPLAY_AD", **result}

        elif action == "prev_page":
            result = list_responsive_display_ads(client, customer_id, campaign_id, ad_group_id, max(1, page - 1), page_size, date_range)
            return {"status": "success", "ad_type": "RESPONSIVE_DISPLAY_AD", **result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}. Valid: list, view_previews, create, pause, enable, next_page, prev_page"}

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
