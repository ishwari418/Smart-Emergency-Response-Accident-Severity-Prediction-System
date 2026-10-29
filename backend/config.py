from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATASET_PATH = DATA_DIR / "accidents.csv"
MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "accident_severity_model.joblib"
METRICS_PATH = MODEL_DIR / "model_metrics.json"

SEVERITY_LABELS = {
    1: "Fatal",
    2: "Serious Injury",
    3: "Minor Injury",
    4: "Property Damage Only",
}

FEATURE_COLUMNS = [
    "number_of_vehicles",
    "number_of_casualties",
    "speed_limit",
    "road_type",
    "weather_conditions",
    "road_surface",
    "light_conditions",
    "traffic_density",
    "junction_type",
    "urban_or_rural",
    "driver_age",
    "vehicle_type",
    "visibility_km",
    "hour",
    "day_of_week",
]

CATEGORICAL_FEATURES = [
    "road_type",
    "weather_conditions",
    "road_surface",
    "light_conditions",
    "traffic_density",
    "junction_type",
    "urban_or_rural",
    "vehicle_type",
    "day_of_week",
]
NUMERIC_FEATURES = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_FEATURES]

CATEGORY_VALUES = {
    "road_type": ["Single carriageway", "Dual carriageway", "Roundabout", "One-way street", "Slip road"],
    "weather_conditions": ["Fine", "Rain", "Snow", "Fog", "Windy"],
    "road_surface": ["Dry", "Wet", "Icy", "Snow-covered"],
    "light_conditions": ["Daylight", "Darkness - lit", "Darkness - unlit", "Dawn or dusk"],
    "traffic_density": ["Low", "Medium", "High"],
    "junction_type": ["Not at junction", "T-junction", "Crossroads", "Roundabout", "Private drive"],
    "urban_or_rural": ["Urban", "Rural"],
    "vehicle_type": ["Car", "Motorcycle", "Truck", "Bus", "Van"],
    "day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}

NUMERIC_RANGES = {
    "number_of_vehicles": (1, 10),
    "number_of_casualties": (0, 20),
    "speed_limit": (20, 70),
    "driver_age": (16, 100),
    "visibility_km": (0.1, 20),
    "hour": (0, 23),
}
