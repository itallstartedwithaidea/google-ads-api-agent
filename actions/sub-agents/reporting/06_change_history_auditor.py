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

def get_change_summary(client, customer_id, date_range, resource_type=None, limit=500):
    ga_service = client.get_service("GoogleAdsService")

    where_clauses = [f"segments.date DURING {date_range}"]
    if resource_type:
        where_clauses.append(f"change_event.change_resource_type = '{resource_type}'")

    query = f"""
        SELECT
            change_event.change_date_time,
            change_event.change_resource_type,
            change_event.resource_change_operation,
            change_event.changed_fields,
            change_event.user_email,
            change_event.client_type,
            change_event.campaign,
            change_event.ad_group,
            change_event.old_resource,
            change_event.new_resource
        FROM change_event
        WHERE {" AND ".join(where_clauses)}
        ORDER BY change_event.change_date_time DESC
        LIMIT {limit}
    """

    results = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        event = row.change_event

        changed_fields = []
        if event.changed_fields:
            for path in event.changed_fields.paths:
                changed_fields.append(path)

        results.append({
            "timestamp": event.change_date_time,
            "resource_type": str(event.change_resource_type.name) if event.change_resource_type else "UNKNOWN",
            "operation": str(event.resource_change_operation.name) if event.resource_change_operation else "UNKNOWN",
            "user_email": event.user_email if event.user_email else "API/System",
            "client_type": str(event.client_type.name) if event.client_type else "UNKNOWN",
            "campaign": event.campaign if event.campaign else None,
            "ad_group": event.ad_group if event.ad_group else None,
            "changed_fields": changed_fields,
            "has_details": bool(event.old_resource or event.new_resource)
        })

    return results

def get_change_details(client, customer_id, date_range, limit=100):
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            change_event.change_date_time,
            change_event.change_resource_type,
            change_event.resource_change_operation,
            change_event.changed_fields,
            change_event.user_email,
            change_event.old_resource,
            change_event.new_resource,
            change_event.campaign,
            change_event.ad_group
        FROM change_event
        WHERE segments.date DURING {date_range}
        ORDER BY change_event.change_date_time DESC
        LIMIT {limit}
    """

    results = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        event = row.change_event
        resource_type = str(event.change_resource_type.name) if event.change_resource_type else "UNKNOWN"

        old_values = {}
        new_values = {}

        if event.old_resource:
            if hasattr(event.old_resource, 'campaign') and event.old_resource.campaign:
                old_values["campaign_name"] = event.old_resource.campaign.name
                old_values["campaign_status"] = str(event.old_resource.campaign.status.name) if event.old_resource.campaign.status else None
            if hasattr(event.old_resource, 'ad_group') and event.old_resource.ad_group:
                old_values["ad_group_name"] = event.old_resource.ad_group.name
                old_values["ad_group_status"] = str(event.old_resource.ad_group.status.name) if event.old_resource.ad_group.status else None
            if hasattr(event.old_resource, 'ad_group_criterion') and event.old_resource.ad_group_criterion:
                if event.old_resource.ad_group_criterion.keyword.text:
                    old_values["keyword"] = event.old_resource.ad_group_criterion.keyword.text
                if event.old_resource.ad_group_criterion.cpc_bid_micros:
                    old_values["cpc_bid"] = round(event.old_resource.ad_group_criterion.cpc_bid_micros / 1000000, 2)

        if event.new_resource:
            if hasattr(event.new_resource, 'campaign') and event.new_resource.campaign:
                new_values["campaign_name"] = event.new_resource.campaign.name
                new_values["campaign_status"] = str(event.new_resource.campaign.status.name) if event.new_resource.campaign.status else None
            if hasattr(event.new_resource, 'ad_group') and event.new_resource.ad_group:
                new_values["ad_group_name"] = event.new_resource.ad_group.name
                new_values["ad_group_status"] = str(event.new_resource.ad_group.status.name) if event.new_resource.ad_group.status else None
            if hasattr(event.new_resource, 'ad_group_criterion') and event.new_resource.ad_group_criterion:
                if event.new_resource.ad_group_criterion.keyword.text:
                    new_values["keyword"] = event.new_resource.ad_group_criterion.keyword.text
                if event.new_resource.ad_group_criterion.cpc_bid_micros:
                    new_values["cpc_bid"] = round(event.new_resource.ad_group_criterion.cpc_bid_micros / 1000000, 2)

        results.append({
            "timestamp": event.change_date_time,
            "resource_type": resource_type,
            "operation": str(event.resource_change_operation.name) if event.resource_change_operation else "UNKNOWN",
            "user_email": event.user_email if event.user_email else "API/System",
            "campaign": event.campaign if event.campaign else None,
            "ad_group": event.ad_group if event.ad_group else None,
            "old_values": old_values,
            "new_values": new_values
        })

    return results

def run(customer_id, date_range="LAST_7_DAYS", login_customer_id=None, resource_type=None, 
        change_type=None, detailed=False, limit=500):
    try:
        customer_id = str(customer_id).replace("-", "")
        if login_customer_id:
            login_customer_id = str(login_customer_id).replace("-", "")

        client = get_client(login_customer_id)

        if detailed:
            changes = get_change_details(client, customer_id, date_range, min(limit, 100))
        else:
            changes = get_change_summary(client, customer_id, date_range, resource_type, limit)

        by_type = {}
        by_operation = {}
        by_user = {}

        for change in changes:
            t = change.get("resource_type", "UNKNOWN")
            o = change.get("operation", "UNKNOWN")
            u = change.get("user_email", "Unknown")

            by_type[t] = by_type.get(t, 0) + 1
            by_operation[o] = by_operation.get(o, 0) + 1
            by_user[u] = by_user.get(u, 0) + 1

        return {
            "status": "success",
            "customer_id": customer_id,
            "date_range": date_range,
            "total_changes": len(changes),
            "summary": {
                "by_resource_type": by_type,
                "by_operation": by_operation,
                "by_user": by_user
            },
            "changes": changes
        }

    except GoogleAdsException as ex:
        errors = [{"code": str(e.error_code), "message": e.message} for e in ex.failure.errors]
        return {"status": "error", "request_id": ex.request_id, "errors": errors}
    except Exception as e:
        return {"status": "error", "message": str(e)}
