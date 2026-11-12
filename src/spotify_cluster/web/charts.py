"""Aggregate tables and formatting; figures live in figures.py."""

import pandas as pd

from spotify_cluster.config import F9


def unit(feature):
    return {"tempo": "BPM", "loudness": "dB"}.get(feature, "0–1")


def cluster_name(label):
    if label not in (0, 1):
        raise ValueError("Cluster label must be 0 or 1.")
    return f"Cluster {label}"


def selected_profiles(data, selection="Compare Both"):
    if selection not in ("Compare Both", "Cluster 0", "Cluster 1"):
        raise ValueError("Choose Cluster 0, Cluster 1 or Compare Both.")
    labels = (0, 1) if selection == "Compare Both" else (int(selection[-1]),)
    return [data["clusters"][str(i)] for i in labels]


def distribution(data):
    return pd.DataFrame(
        [
            {
                "Cluster": cluster_name(p["cluster_id"]),
                "Tracks": p["count"],
                "Share (%)": round(p["share"] * 100, 3),
            }
            for p in selected_profiles(data)
        ]
    )


def comparison(data, feature, statistic, selection="Compare Both"):
    if feature not in F9 or statistic not in ("Mean", "Median"):
        raise ValueError("Choose a supported feature and statistic.")
    return pd.DataFrame(
        [
            {
                "Cluster": cluster_name(p["cluster_id"]),
                "Value": p[statistic.lower()][feature],
            }
            for p in selected_profiles(data, selection)
        ]
    )


def profile_table(data, statistic, selection="Compare Both"):
    if statistic not in ("Mean", "Median"):
        raise ValueError("Choose Mean or Median.")
    profiles = selected_profiles(data, selection)
    rows = []
    for feature in F9:
        row = {"Feature": feature.title()}
        for profile in profiles:
            row[f"Cluster {profile['cluster_id']}"] = round(
                profile[statistic.lower()][feature], 4
            )
        row["Unit"] = unit(feature)
        rows.append(row)
    return pd.DataFrame(rows)


def detail_table(data, selection="Compare Both"):
    rows = []
    for profile in selected_profiles(data, selection):
        for feature in F9:
            row = {
                "Cluster": cluster_name(profile["cluster_id"]),
                "Feature": feature.title(),
                "Unit": unit(feature),
            }
            for stat in ("mean", "median", "std", "q1", "q3", "iqr"):
                values = profile.get(stat)
                row[stat.upper() if stat in ("q1", "q3", "iqr") else stat.title()] = (
                    round(values[feature], 4) if values else None
                )
            rows.append(row)
    return pd.DataFrame(rows)


def contributions_table(data):
    contributions = data.get("feature_contributions") or {}
    shares = contributions.get("shares") or {}
    between = contributions.get("between_ss") or {}
    if not shares:
        return pd.DataFrame(columns=["Feature", "Share (%)", "Between SS"])
    rows = [
        {
            "Feature": feature.title(),
            "Share (%)": round(shares[feature] * 100, 4),
            "Between SS": round(between.get(feature, 0), 3),
        }
        for feature in sorted(F9, key=lambda name: shares.get(name, 0), reverse=True)
    ]
    return pd.DataFrame(rows)


def distances(prediction):
    return pd.DataFrame(
        {"Cluster": ["Cluster 0", "Cluster 1"], "Distance": prediction["distances"]}
    )


def contribution_share(data, feature="instrumentalness"):
    contributions = data.get("feature_contributions") or {}
    shares = contributions.get("shares") or {}
    return shares.get(feature)


def largest_contribution(data):
    contributions = data.get("feature_contributions") or {}
    shares = contributions.get("shares") or {}
    if not shares:
        return None, None
    feature = max(F9, key=lambda name: shares.get(name, 0))
    return feature, shares[feature]
