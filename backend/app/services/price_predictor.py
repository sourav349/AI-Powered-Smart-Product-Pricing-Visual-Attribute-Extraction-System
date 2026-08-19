from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix, hstack


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ============================================================
# MODEL PATHS
# ============================================================

PRICE_MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "price_prediction"
    / "final_clean_v1"
)

PRICE_MODEL_FILE = (
    PRICE_MODEL_ROOT
    / "price_model.joblib"
)

PRICE_PREPROCESSOR_FILE = (
    PRICE_MODEL_ROOT
    / "structured_preprocessor.joblib"
)

PRICE_TFIDF_FILE = (
    PRICE_MODEL_ROOT
    / "title_tfidf.joblib"
)


CLUSTER_MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "clustering_clean"
)

CLUSTER_SCALER_FILE = (
    CLUSTER_MODEL_ROOT
    / "structured_scaler_clean.joblib"
)

CLUSTER_KMEANS_FILE = (
    CLUSTER_MODEL_ROOT
    / "minibatch_kmeans_clean.joblib"
)


PCA_FILE = (
    PROJECT_ROOT
    / "models"
    / "clustering"
    / "incremental_pca.joblib"
)


# ============================================================
# EMBEDDING WORKER PATH
# ============================================================

EMBEDDING_WORKER_FILE = (
    Path(__file__).resolve().parent
    / "embedding_worker.py"
)


# ============================================================
# DEVICE LABEL
# ============================================================

DEVICE = "cpu"


# ============================================================
# VALIDATE MODEL FILES
# ============================================================

REQUIRED_FILES = [
    PRICE_MODEL_FILE,
    PRICE_PREPROCESSOR_FILE,
    PRICE_TFIDF_FILE,
    CLUSTER_SCALER_FILE,
    CLUSTER_KMEANS_FILE,
    PCA_FILE,
    EMBEDDING_WORKER_FILE,
]

for file_path in REQUIRED_FILES:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )


# ============================================================
# LOAD CLASSICAL ML ARTIFACTS
# ============================================================

print("Loading price prediction model...")

price_model = joblib.load(
    PRICE_MODEL_FILE
)


print("Loading price preprocessor...")

price_preprocessor = joblib.load(
    PRICE_PREPROCESSOR_FILE
)


print("Loading TF-IDF vectorizer...")

price_tfidf = joblib.load(
    PRICE_TFIDF_FILE
)


print("Loading clean cluster scaler...")

cluster_scaler = joblib.load(
    CLUSTER_SCALER_FILE
)


print("Loading clean KMeans model...")

cluster_kmeans = joblib.load(
    CLUSTER_KMEANS_FILE
)


print("Loading PCA model...")

text_pca = joblib.load(
    PCA_FILE
)


print(
    "✅ Classical ML artifacts loaded successfully"
)


# ============================================================
# MODEL DIMENSION VALIDATION
# ============================================================

if getattr(
    text_pca,
    "n_features_in_",
    None,
) != 384:

    raise RuntimeError(
        "PCA model must expect 384 input features."
    )


if getattr(
    text_pca,
    "n_components_",
    None,
) != 64:

    raise RuntimeError(
        "PCA model must output 64 features."
    )


if getattr(
    cluster_scaler,
    "n_features_in_",
    None,
) != 4:

    raise RuntimeError(
        "Clean cluster scaler must expect 4 features."
    )


if getattr(
    cluster_kmeans,
    "n_features_in_",
    None,
) != 68:

    raise RuntimeError(
        "Clean KMeans model must expect 68 features."
    )


# ============================================================
# SENTENCE TRANSFORMER SUBPROCESS
# ============================================================

def generate_text_embedding(
    title: str,
) -> np.ndarray:

    title = str(
        title
    ).strip()

    if not title:
        raise ValueError(
            "Product title is required for embedding."
        )

    process = subprocess.run(
        [
            sys.executable,
            str(
                EMBEDDING_WORKER_FILE
            ),
            title,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if process.returncode != 0:
        raise RuntimeError(
            "Embedding worker failed.\n"
            f"stderr:\n{process.stderr}"
        )

    output = process.stdout.strip()

    if not output:
        raise RuntimeError(
            "Embedding worker returned empty output."
        )

    try:
        values = json.loads(
            output
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Embedding worker returned invalid JSON.\n"
            f"Output preview:\n{output[:1000]}"
        ) from error

    embedding = np.asarray(
        values,
        dtype=np.float32,
    ).reshape(
        1,
        -1,
    )

    if embedding.shape != (
        1,
        384,
    ):
        raise RuntimeError(
            f"Expected embedding shape (1, 384), "
            f"got {embedding.shape}"
        )

    return embedding


# ============================================================
# HELPERS
# ============================================================

def extract_first_number(
    text: str,
) -> float:

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        str(text),
    )

    if not numbers:
        return 0.0

    try:
        return float(
            numbers[0]
        )

    except Exception:
        return 0.0


# ============================================================
# PRICE FEATURE ENGINEERING
# ============================================================

def create_price_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    df = dataframe.copy()


    # --------------------------------------------------------
    # BASIC TEXT
    # --------------------------------------------------------

    df["title"] = (
        df["title"]
        .fillna("")
        .astype(str)
    )

    df["category_name"] = (
        df["category_name"]
        .fillna("Unknown")
        .astype(str)
    )


    # --------------------------------------------------------
    # NUMERIC FEATURES
    # --------------------------------------------------------

    df["stars"] = (
        pd.to_numeric(
            df["stars"],
            errors="coerce",
        )
        .fillna(0)
    )

    reviews = (
        pd.to_numeric(
            df["reviews"],
            errors="coerce",
        )
        .fillna(0)
    )

    bought = (
        pd.to_numeric(
            df["boughtInLastMonth"],
            errors="coerce",
        )
        .fillna(0)
    )

    df["reviews_log1p"] = np.log1p(
        reviews
    )

    df["bought_log1p"] = np.log1p(
        bought
    )

    df["isBestSeller"] = (
        df["isBestSeller"]
        .fillna(False)
        .astype(int)
    )

    df["cluster_id"] = (
        pd.to_numeric(
            df["cluster_id"],
            errors="coerce",
        )
        .fillna(-1)
        .astype(int)
    )


    # --------------------------------------------------------
    # TITLE STATISTICS
    # --------------------------------------------------------

    df["title_char_length"] = (
        df["title"]
        .str.len()
    )

    df["title_word_count"] = (
        df["title"]
        .str.split()
        .str.len()
        .fillna(0)
    )

    df["title_digit_count"] = (
        df["title"]
        .str.count(
            r"\d"
        )
    )

    df["title_uppercase_count"] = (
        df["title"]
        .apply(
            lambda text:
            sum(
                char.isupper()
                for char in text
            )
        )
    )

    df["title_first_number"] = (
        df["title"]
        .apply(
            extract_first_number
        )
    )


    # --------------------------------------------------------
    # TITLE PATTERN FEATURES
    # --------------------------------------------------------

    lower_title = (
        df["title"]
        .str.lower()
    )

    patterns = {
        "has_gb":
            r"\b\d+(?:\.\d+)?\s*gb\b",

        "has_tb":
            r"\b\d+(?:\.\d+)?\s*tb\b",

        "has_ram":
            r"\b(?:ram|memory)\b",

        "has_inch":
            r'\b\d+(?:\.\d+)?\s*(?:inch|inches|")',

        "has_cm":
            r"\b\d+(?:\.\d+)?\s*cm\b",

        "has_kg":
            r"\b\d+(?:\.\d+)?\s*kg\b",

        "has_gram":
            r"\b\d+(?:\.\d+)?\s*(?:g|gram|grams)\b",

        "has_watt":
            r"\b\d+(?:\.\d+)?\s*(?:w|watt|watts)\b",

        "has_volt":
            r"\b\d+(?:\.\d+)?\s*(?:v|volt|volts)\b",

        "has_pack":
            r"\b(?:pack|set|pair|bundle)\b",

        "has_multipack_number":
            r"\b\d+\s*[- ]?"
            r"(?:pack|piece|pcs|count|ct)\b",

        "has_pro":
            r"\bpro\b",

        "has_max":
            r"\bmax\b",

        "has_premium":
            r"\bpremium\b",

        "has_professional":
            r"\bprofessional\b",

        "has_wireless":
            r"\bwireless\b",

        "has_smart":
            r"\bsmart\b",
    }

    for (
        feature_name,
        pattern,
    ) in patterns.items():

        df[feature_name] = (
            lower_title
            .str.contains(
                pattern,
                regex=True,
            )
            .astype(int)
        )

    return df


# ============================================================
# CLEAN CLUSTER PREDICTION
# ============================================================

def predict_clean_cluster(
    *,
    title: str,
    stars: float = 0,
    reviews: int = 0,
    bought_in_last_month: int = 0,
    is_best_seller: bool = False,
) -> int:

    title = str(
        title
    ).strip()

    if not title:
        raise ValueError(
            "Product title is required "
            "for cluster prediction."
        )


    # --------------------------------------------------------
    # SENTENCE TRANSFORMER
    # RUNS IN SEPARATE PROCESS
    # --------------------------------------------------------

    embedding = generate_text_embedding(
        title
    )


    # --------------------------------------------------------
    # PCA: 384 -> 64
    # --------------------------------------------------------

    text_features = (
        text_pca
        .transform(
            embedding
        )
        .astype(
            np.float32
        )
    )

    if text_features.shape != (
        1,
        64,
    ):
        raise RuntimeError(
            f"Expected PCA shape (1, 64), "
            f"got {text_features.shape}"
        )


    # --------------------------------------------------------
    # CLEAN STRUCTURED CLUSTER FEATURES
    # --------------------------------------------------------

    stars_value = float(
        stars or 0
    )

    reviews_value = max(
        0.0,
        float(
            reviews or 0
        ),
    )

    bought_value = max(
        0.0,
        float(
            bought_in_last_month
            or 0
        ),
    )

    best_seller_value = float(
        bool(
            is_best_seller
        )
    )

    structured_raw = np.array(
        [
            [
                stars_value,

                np.log1p(
                    reviews_value
                ),

                np.log1p(
                    bought_value
                ),

                best_seller_value,
            ]
        ],
        dtype=np.float32,
    )


    # --------------------------------------------------------
    # SCALE STRUCTURED FEATURES
    # --------------------------------------------------------

    structured_scaled = (
        cluster_scaler
        .transform(
            structured_raw
        )
        .astype(
            np.float32
        )
    )

    if structured_scaled.shape != (
        1,
        4,
    ):
        raise RuntimeError(
            f"Expected structured shape (1, 4), "
            f"got {structured_scaled.shape}"
        )


    # --------------------------------------------------------
    # 64 + 4 = 68
    # --------------------------------------------------------

    cluster_features = (
        np.concatenate(
            [
                text_features,
                structured_scaled,
            ],
            axis=1,
        )
        .astype(
            np.float32
        )
    )

    if cluster_features.shape != (
        1,
        68,
    ):
        raise RuntimeError(
            f"Expected cluster feature shape (1, 68), "
            f"got {cluster_features.shape}"
        )


    # --------------------------------------------------------
    # KMEANS
    # --------------------------------------------------------

    cluster_id = int(
        cluster_kmeans
        .predict(
            cluster_features
        )[0]
    )

    return cluster_id


# ============================================================
# FINAL PRICE PREDICTION
# ============================================================

def predict_product_price(
    *,
    title: str,
    category_name: str,
    stars: float = 0,
    reviews: int = 0,
    bought_in_last_month: int = 0,
    is_best_seller: bool = False,
) -> dict:

    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

    title = str(
        title
    ).strip()

    category_name = str(
        category_name
    ).strip()


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not title:
        raise ValueError(
            "Product title is required."
        )

    if not category_name:
        raise ValueError(
            "Category is required."
        )

    if stars < 0 or stars > 5:
        raise ValueError(
            "Stars must be between 0 and 5."
        )

    if reviews < 0:
        raise ValueError(
            "Reviews cannot be negative."
        )

    if bought_in_last_month < 0:
        raise ValueError(
            "Bought in last month cannot be negative."
        )


    # --------------------------------------------------------
    # AUTOMATIC CLEAN CLUSTER
    # --------------------------------------------------------

    cluster_id = predict_clean_cluster(
        title=title,
        stars=stars,
        reviews=reviews,
        bought_in_last_month=(
            bought_in_last_month
        ),
        is_best_seller=(
            is_best_seller
        ),
    )


    # --------------------------------------------------------
    # RAW PRODUCT
    # --------------------------------------------------------

    raw_product = pd.DataFrame(
        [
            {
                "title":
                    title,

                "category_name":
                    category_name,

                "stars":
                    stars,

                "reviews":
                    reviews,

                "boughtInLastMonth":
                    bought_in_last_month,

                "isBestSeller":
                    is_best_seller,

                "cluster_id":
                    cluster_id,
            }
        ]
    )


    # --------------------------------------------------------
    # PRICE FEATURE ENGINEERING
    # --------------------------------------------------------

    product_df = (
        create_price_features(
            raw_product
        )
    )


    # --------------------------------------------------------
    # STRUCTURED FEATURES
    # --------------------------------------------------------

    structured_features = (
        price_preprocessor
        .transform(
            product_df
        )
    )


    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    text_features = (
        price_tfidf
        .transform(
            product_df[
                "title"
            ]
        )
    )


    # --------------------------------------------------------
    # FINAL FEATURE MATRIX
    # --------------------------------------------------------

    final_features = hstack(
        [
            csr_matrix(
                structured_features
            ),

            text_features,
        ],
        format="csr",
    )


    # --------------------------------------------------------
    # LIGHTGBM PREDICTION
    # --------------------------------------------------------

    predicted_log_price = float(
        price_model
        .predict(
            final_features
        )[0]
    )


    # --------------------------------------------------------
    # REVERSE LOG1P
    # --------------------------------------------------------

    predicted_price = float(
        np.expm1(
            predicted_log_price
        )
    )

    predicted_price = max(
        0.0,
        predicted_price,
    )


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "predicted_price":
            round(
                predicted_price,
                2,
            ),

        "cluster_id":
            cluster_id,

        "model_version":
            "final_clean_v1",

        "device":
            DEVICE,
    }