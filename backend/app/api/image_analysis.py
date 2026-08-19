from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Image Analysis"],
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


OCR_WORKER = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "ocr_worker.py"
)


@router.post("/analyze-image")
async def analyze_product_image(
    image: UploadFile = File(...),
):

    total_start = time.time()

    temporary_path = None

    try:

        print("\n==============================")
        print("IMAGE ANALYSIS STARTED")
        print("==============================")

        # ----------------------------------------------------
        # VALIDATE FILE
        # ----------------------------------------------------

        if image.content_type not in ALLOWED_TYPES:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only JPG, PNG and WEBP "
                    "images are supported."
                ),
            )

        # ----------------------------------------------------
        # READ UPLOAD
        # ----------------------------------------------------

        print("1. Reading uploaded image...")

        start = time.time()

        contents = await image.read()

        print(
            "   Upload read:",
            round(
                time.time() - start,
                3,
            ),
            "seconds",
        )

        # ----------------------------------------------------
        # SAVE TEMPORARY FILE
        # ----------------------------------------------------

        print("2. Saving image...")

        suffix = Path(
            image.filename or "product.jpg"
        ).suffix

        if not suffix:
            suffix = ".jpg"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(
                contents
            )

            temporary_path = (
                temp_file.name
            )

        print(
            "   Temporary path:",
            temporary_path,
        )

        # ----------------------------------------------------
        # RUN OCR IN SEPARATE PROCESS
        # ----------------------------------------------------

        print(
            "3. Starting OCR worker..."
        )

        start = time.time()

        process = subprocess.run(
    [
        sys.executable,
        "-m",
        "app.services.ocr_worker",
        temporary_path,
    ],
    capture_output=True,
    text=True,
    timeout=60,
    cwd=str(
        Path(__file__).resolve().parents[2]
    ),
)

        print(
            "   OCR worker time:",
            round(
                time.time() - start,
                3,
            ),
            "seconds",
        )

        # ----------------------------------------------------
        # CHECK WORKER
        # ----------------------------------------------------

        if process.returncode != 0:

            print(
                "OCR WORKER STDERR:"
            )

            print(
                process.stderr
            )

            raise RuntimeError(
                "OCR worker failed."
            )

        # ----------------------------------------------------
        # WORKER OUTPUT
        #
        # EasyOCR prints messages before JSON.
        # So take the LAST non-empty line.
        # ----------------------------------------------------

        output_lines = [
            line.strip()
            for line
            in process.stdout.splitlines()
            if line.strip()
        ]

        if not output_lines:

            raise RuntimeError(
                "OCR worker returned no output."
            )

        json_output = (
            output_lines[-1]
        )

        try:

            result = json.loads(
                json_output
            )

        except json.JSONDecodeError as error:

            print(
                "OCR WORKER OUTPUT:"
            )

            print(
                process.stdout
            )

            raise RuntimeError(
                "OCR worker returned "
                "invalid JSON."
            ) from error

        # ----------------------------------------------------
        # PRINT RESULT
        # ----------------------------------------------------

        print("\n==============================")
        print("IMAGE RESULT")
        print("==============================")

        print(
            "Product Type:",
            result.get(
                "product_type"
            ),
        )

        print(
            "Attributes:",
            result.get(
                "attributes"
            ),
        )

        print(
            "TOTAL TIME:",
            round(
                time.time()
                - total_start,
                3,
            ),
            "seconds",
        )

        print("==============================\n")

        return {
            "filename":
                image.filename,

            **result,
        }

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=504,
            detail=(
                "Image analysis timed out."
            ),
        )

    except HTTPException:
        raise

    except Exception as error:

        print(
            "IMAGE ANALYSIS ERROR:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if (
            temporary_path
            and os.path.exists(
                temporary_path
            )
        ):

            os.remove(
                temporary_path
            )

            print(
                "Temporary image deleted."
            )