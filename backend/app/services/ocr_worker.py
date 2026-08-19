from __future__ import annotations

import json
import sys

from app.services.attribute_extractor import (
    extract_product_attributes,
)


def main():

    if len(sys.argv) < 2:
        raise ValueError(
            "Image path argument is required."
        )

    image_path = sys.argv[1]

    result = extract_product_attributes(
        image_path
    )

    # stdout must contain JSON only
    print(
        json.dumps(
            result,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()