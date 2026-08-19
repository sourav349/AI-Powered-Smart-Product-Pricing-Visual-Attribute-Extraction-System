from __future__ import annotations

import json
import sys

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEVICE = "cpu"


def main():
    if len(sys.argv) < 2:
        raise ValueError(
            "Product title argument is required."
        )

    title = str(
        sys.argv[1]
    ).strip()

    if not title:
        raise ValueError(
            "Product title cannot be empty."
        )

    model = SentenceTransformer(
        MODEL_NAME,
        device=DEVICE,
    )

    embedding = model.encode(
        [title],
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=False,
    ).astype(np.float32)

    if embedding.shape != (1, 384):
        raise RuntimeError(
            f"Expected embedding shape (1, 384), "
            f"got {embedding.shape}"
        )

    # IMPORTANT:
    # stdout must contain JSON only because
    # price_predictor.py reads this output.
    print(
        json.dumps(
            embedding[0].tolist()
        )
    )


if __name__ == "__main__":
    main()