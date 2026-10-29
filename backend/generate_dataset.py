"""Generate a reproducible synthetic road-accident dataset for demonstrations."""

import sys

import numpy as np
import pandas as pd

from config import DATASET_PATH, SEVERITY_LABELS


ROW_COUNT = 120_000
RANDOM_SEED = 42


def generate_dataset(row_count: int = ROW_COUNT) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    days = np.array(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    road_types = np.array(["Single carriageway", "Dual carriageway", "Roundabout", "One-way street", "Slip road"])
    weather = np.array(["Fine", "Rain", "Snow", "Fog", "Windy"])
    surfaces = np.array(["Dry", "Wet", "Icy", "Snow-covered"])
    lights = np.array(["Daylight", "Darkness - lit", "Darkness - unlit", "Dawn or dusk"])
    densities = np.array(["Low", "Medium", "High"])
    junctions = np.array(["Not at junction", "T-junction", "Crossroads", "Roundabout", "Private drive"])
    areas = np.array(["Urban", "Rural"])
    vehicles = np.array(["Car", "Motorcycle", "Truck", "Bus", "Van"])

    hours = rng.integers(0, 24, row_count)
    weather_values = rng.choice(weather, row_count, p=[0.69, 0.18, 0.035, 0.045, 0.05])
    road_surface = np.where(
        weather_values == "Snow",
        rng.choice(["Icy", "Snow-covered", "Wet"], row_count, p=[0.5, 0.4, 0.1]),
        np.where(
            weather_values == "Rain",
            rng.choice(["Wet", "Dry"], row_count, p=[0.82, 0.18]),
            np.where(
                weather_values == "Fine",
                rng.choice(["Dry", "Wet"], row_count, p=[0.92, 0.08]),
                rng.choice(["Dry", "Wet", "Icy"], row_count, p=[0.65, 0.3, 0.05]),
            ),
        ),
    )
    visibility = np.clip(
        rng.normal(15, 3.2, row_count)
        - np.where(weather_values == "Fog", 10, 0)
        - np.where(weather_values == "Snow", 4, 0)
        - np.where(weather_values == "Rain", 2, 0),
        0.1,
        20,
    ).round(1)
    is_night = (hours <= 5) | (hours >= 21)
    light_conditions = np.where(
        is_night,
        rng.choice(["Darkness - lit", "Darkness - unlit"], row_count, p=[0.72, 0.28]),
        np.where((hours <= 7) | (hours >= 18), "Dawn or dusk", "Daylight"),
    )
    urban_rural = rng.choice(areas, row_count, p=[0.68, 0.32])
    traffic = rng.choice(densities, row_count, p=[0.28, 0.48, 0.24])
    speed_limit = np.where(
        urban_rural == "Urban",
        rng.choice([20, 30, 40, 50], row_count, p=[0.08, 0.58, 0.29, 0.05]),
        rng.choice([30, 40, 50, 60, 70], row_count, p=[0.04, 0.1, 0.16, 0.42, 0.28]),
    )
    number_of_vehicles = np.clip(rng.poisson(1.35, row_count) + 1, 1, 8)
    vehicle_type = rng.choice(vehicles, row_count, p=[0.64, 0.1, 0.08, 0.045, 0.135])
    driver_age = np.clip(rng.normal(41, 15, row_count), 16, 95).astype(int)
    road_type = rng.choice(road_types, row_count, p=[0.55, 0.2, 0.12, 0.09, 0.04])
    junction_type = rng.choice(junctions, row_count, p=[0.4, 0.25, 0.17, 0.12, 0.06])
    day_of_week = rng.choice(days, row_count, p=[0.145, 0.145, 0.145, 0.145, 0.16, 0.14, 0.12])

    risk = (
        0.4
        + (speed_limit - 20) / 85
        + (number_of_vehicles - 1) * 0.19
        + np.where(vehicle_type == "Motorcycle", 0.43, 0)
        + np.where(vehicle_type == "Truck", 0.2, 0)
        + np.where(road_surface == "Icy", 0.75, np.where(road_surface == "Snow-covered", 0.55, np.where(road_surface == "Wet", 0.24, 0)))
        + np.where(weather_values == "Fog", 0.43, np.where(weather_values == "Snow", 0.35, np.where(weather_values == "Rain", 0.14, 0)))
        + np.where(light_conditions == "Darkness - unlit", 0.36, np.where(light_conditions == "Dawn or dusk", 0.12, 0))
        + np.where(visibility < 5, 0.5, np.where(visibility < 10, 0.18, 0))
        + np.where(urban_rural == "Rural", 0.18, 0)
        + np.where(traffic == "High", 0.1, 0)
        + np.where((driver_age < 21) | (driver_age > 75), 0.18, 0)
        + rng.normal(0, 0.42, row_count)
    )
    # Quantile cutoffs keep all four synthetic classes represented without
    # making any individual feature a perfect predictor.
    fatal_cutoff, serious_cutoff, minor_cutoff = np.quantile(risk, [0.85, 0.62, 0.28])
    severity = np.where(
        risk >= fatal_cutoff,
        1,
        np.where(risk >= serious_cutoff, 2, np.where(risk >= minor_cutoff, 3, 4)),
    )
    number_of_casualties = np.clip(
        rng.poisson(
            0.65 + (number_of_vehicles > 2) * 0.45 + (vehicle_type == "Motorcycle") * 0.15,
            row_count,
        ),
        0,
        12,
    )

    start = pd.Timestamp("2022-01-01")
    offsets = rng.integers(0, 365 * 3, row_count)
    dates = start + pd.to_timedelta(offsets, unit="D")
    # The date and weekday fields are derived consistently.
    day_of_week = dates.day_name().to_numpy()
    minutes = rng.integers(0, 60, row_count)
    time_values = np.array([f"{hour:02d}:{minute:02d}" for hour, minute in zip(hours, minutes)])
    latitude = rng.uniform(50.0, 58.5, row_count).round(5)
    longitude = rng.uniform(-5.5, 1.8, row_count).round(5)

    frame = pd.DataFrame(
        {
            "accident_id": [f"SYN-{index:06d}" for index in range(1, row_count + 1)],
            "date": dates.strftime("%Y-%m-%d"),
            "time": time_values,
            "day_of_week": day_of_week,
            "latitude": latitude,
            "longitude": longitude,
            "severity": severity.astype(int),
            "number_of_vehicles": number_of_vehicles.astype(int),
            "number_of_casualties": number_of_casualties.astype(int),
            "speed_limit": speed_limit.astype(int),
            "road_type": road_type,
            "weather_conditions": weather_values,
            "road_surface": road_surface,
            "light_conditions": light_conditions,
            "traffic_density": traffic,
            "junction_type": junction_type,
            "urban_or_rural": urban_rural,
            "driver_age": driver_age,
            "vehicle_type": vehicle_type,
            "visibility_km": visibility,
            "hour": hours.astype(int),
        }
    )
    return frame


def validate_dataset(frame: pd.DataFrame) -> None:
    required = {
        "accident_id", "date", "time", "day_of_week", "latitude", "longitude", "severity",
        "number_of_vehicles", "number_of_casualties", "speed_limit", "road_type",
        "weather_conditions", "road_surface", "light_conditions", "traffic_density",
        "junction_type", "urban_or_rural", "driver_age", "vehicle_type", "visibility_km", "hour",
    }
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")
    if frame["accident_id"].duplicated().any():
        raise ValueError("accident_id values must be unique")
    if frame[list(required)].isna().any().any():
        raise ValueError("Generated dataset contains missing values")
    if not frame["severity"].isin(SEVERITY_LABELS).all():
        raise ValueError("Unexpected severity label found")
    ranges = {
        "latitude": (-90, 90), "longitude": (-180, 180), "number_of_vehicles": (1, 10),
        "number_of_casualties": (0, 20), "speed_limit": (20, 70), "driver_age": (16, 100),
        "visibility_km": (0.1, 20), "hour": (0, 23),
    }
    for column, (minimum, maximum) in ranges.items():
        if not frame[column].between(minimum, maximum).all():
            raise ValueError(f"{column} contains values outside {minimum}–{maximum}")


def main() -> None:
    if DATASET_PATH.exists():
        print(f"Dataset already exists; not overwriting it: {DATASET_PATH}")
        return
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_dataset()
    validate_dataset(frame)
    frame.to_csv(DATASET_PATH, index=False)
    print(f"Created synthetic dataset: {DATASET_PATH}")
    print(f"Rows: {len(frame):,} | Columns: {len(frame.columns)}")
    print(f"Missing values:\n{frame.isna().sum().to_string()}")
    print(f"Severity distribution:\n{frame['severity'].map(SEVERITY_LABELS).value_counts().to_string()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Dataset generation failed: {error}", file=sys.stderr)
        raise
