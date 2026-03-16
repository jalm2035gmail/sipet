from __future__ import annotations

import numpy as np
import pandas as pd


def build_dashboard_metrics(modules: list[dict]) -> dict:
    enabled_modules = [module for module in modules if module.get("route")]
    return {
        "total_modules": len(enabled_modules),
        "with_description": sum(1 for module in enabled_modules if str(module.get("description") or "").strip()),
    }


def compute_usage(user_id: str, modules: list[dict]) -> dict:
    events = []
    for module in modules:
        item_key = str(module.get("key") or module.get("route") or "").strip()
        route = str(module.get("route") or "").strip()
        if not item_key or not route:
            continue
        events.append(
            {
                "item_key": item_key,
                "screen_key": str(module.get("screen_access_name") or item_key).strip(),
                "widget_key": str(module.get("widget_key") or item_key).strip(),
                "recommended_weight": float(module.get("recommended_weight") or 1.0),
            }
        )
    if not events:
        return {
            "user_id": str(user_id),
            "most_used_apps": [],
            "most_used_screens": [],
            "abandoned_apps": [],
            "recommended_widgets": [],
            "total_items": 0,
        }

    df = pd.DataFrame(events)
    app_usage = (
        df.groupby("item_key")
        .size()
        .reset_index(name="usage_count")
        .sort_values(["usage_count", "item_key"], ascending=[False, True])
    )
    screen_usage = (
        df.groupby("screen_key")
        .size()
        .reset_index(name="usage_count")
        .sort_values(["usage_count", "screen_key"], ascending=[False, True])
    )
    widget_usage = (
        df.groupby("widget_key")
        .agg(
            usage_count=("widget_key", "size"),
            weight=("recommended_weight", "mean"),
        )
        .reset_index()
    )
    widget_usage["score"] = np.round(widget_usage["usage_count"] * widget_usage["weight"], 2)
    widget_usage = widget_usage.sort_values(["score", "widget_key"], ascending=[False, True])

    usage_mean = float(app_usage["usage_count"].mean())
    abandoned_apps = app_usage[app_usage["usage_count"] < usage_mean]

    return {
        "user_id": str(user_id),
        "most_used_apps": app_usage.head(5).to_dict(orient="records"),
        "most_used_screens": screen_usage.head(5).to_dict(orient="records"),
        "abandoned_apps": abandoned_apps.to_dict(orient="records"),
        "recommended_widgets": widget_usage.head(5).to_dict(orient="records"),
        "total_items": int(df.shape[0]),
    }
