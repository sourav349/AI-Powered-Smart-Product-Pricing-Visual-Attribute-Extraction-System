import { useState } from "react";

import {
  analyzeImage,
  predictPrice,
} from "./api";

import "./App.css";


function App() {

  // =========================================================
  // PRICE FORM STATE
  // =========================================================

  const [form, setForm] = useState({
    title: "",
    category_name: "",
    stars: 4.5,
    reviews: 0,
    bought_in_last_month: 0,
    is_best_seller: false,
  });


  // =========================================================
  // PRICE PREDICTION STATE
  // =========================================================

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  // =========================================================
  // IMAGE ANALYSIS STATE
  // =========================================================

  const [imageFile, setImageFile] =
    useState(null);

  const [imagePreview, setImagePreview] =
    useState(null);

  const [imageResult, setImageResult] =
    useState(null);

  const [imageLoading, setImageLoading] =
    useState(false);

  const [imageError, setImageError] =
    useState("");


  // =========================================================
  // FORM INPUT
  // =========================================================

  const handleChange = (event) => {

    const {
      name,
      value,
      type,
      checked,
    } = event.target;


    setForm(
      (previous) => ({
        ...previous,

        [name]:
          type === "checkbox"
            ? checked
            : value,
      })
    );
  };


  // =========================================================
  // IMAGE SELECT
  // =========================================================

  const handleImageChange = (
    event
  ) => {

    const file =
      event.target.files?.[0];


    if (!file) {
      return;
    }


    // Remove previous temporary preview URL
    if (imagePreview) {

      URL.revokeObjectURL(
        imagePreview
      );
    }


    const preview =
      URL.createObjectURL(
        file
      );


    setImageFile(
      file
    );


    setImagePreview(
      preview
    );


    // Clear previous image result
    setImageResult(
      null
    );


    setImageError(
      ""
    );
  };


  // =========================================================
  // ATTRIBUTE VALUE HELPER
  //
  // Backend may return:
  //
  // [
  //   {
  //      value: "65 ml",
  //      confidence: "medium",
  //      source: "OCR-corrupted ml unit recovered"
  //   }
  // ]
  //
  // or sometimes:
  //
  // ["65 ml"]
  // =========================================================

  const getFirstAttributeValue = (
    values
  ) => {

    if (
      !values ||
      values.length === 0
    ) {
      return "";
    }


    const first =
      values[0];


    if (
      typeof first === "string"
    ) {
      return first;
    }


    return (
      first?.value || ""
    );
  };


  // =========================================================
  // CLEAN VARIANT
  //
  // Example:
  //
  // "2 in 1 | Classic Clean"
  //
  // becomes:
  //
  // "2 in 1 Classic Clean"
  // =========================================================

  const cleanVariant = (
    variant
  ) => {

    if (!variant) {
      return "";
    }


    return (
      variant
        .replaceAll(
          "|",
          " "
        )
        .replace(
          /\s+/g,
          " "
        )
        .trim()
    );
  };


  // =========================================================
  // IMAGE ANALYSIS
  // =========================================================

  const handleImageAnalysis =
    async () => {

      if (!imageFile) {

        setImageError(
          "Please select an image first."
        );

        return;
      }


      setImageLoading(
        true
      );


      setImageError(
        ""
      );


      setImageResult(
        null
      );


      try {

        // ===================================================
        // 1. SEND IMAGE TO BACKEND
        // ===================================================

        const data =
          await analyzeImage(
            imageFile
          );


        console.log(
          "IMAGE ANALYSIS RESULT:",
          data
        );


        // ===================================================
        // 2. SAVE RESULT FOR UI
        // ===================================================

        setImageResult(
          data
        );


        // ===================================================
        // 3. GET PRODUCT IDENTITY
        // ===================================================

        const brand =
          data?.brand ||
          "";


        const productType =
          data?.product_type ||
          "";


        const variant =
          cleanVariant(
            data?.variant
          );


        // ===================================================
        // 4. GET USEFUL ATTRIBUTES
        // ===================================================

        const volume =
          getFirstAttributeValue(
            data?.attributes
              ?.volume
          );


        const weight =
          getFirstAttributeValue(
            data?.attributes
              ?.weight
          );


        const storage =
          getFirstAttributeValue(
            data?.attributes
              ?.storage
          );


        // ===================================================
        // 5. BUILD PRODUCT TITLE AUTOMATICALLY
        //
        // Example:
        //
        // Head & Shoulders
        // +
        // 2 in 1 Classic Clean
        // +
        // Shampoo
        // +
        // 700 ml
        //
        // =
        //
        // Head & Shoulders 2 in 1 Classic Clean
        // Shampoo 700 ml
        // ===================================================

        const titleParts = [
          brand,
          variant,
          productType,
          volume,
          weight,
          storage,
        ];


        const generatedTitle =
          titleParts
            .filter(
              Boolean
            )
            .join(
              " "
            )
            .replace(
              /\s+/g,
              " "
            )
            .trim();


        // ===================================================
        // 6. AUTO-FILL PRICE FORM
        // ===================================================

        setForm(
          (previous) => ({
            ...previous,

            title:
              generatedTitle ||
              productType ||
              previous.title,

            category_name:
              productType ||
              previous.category_name,
          })
        );


        // ===================================================
        // 7. CLEAR OLD PRICE RESULT
        //
        // Important:
        // Existing result may belong to an older product.
        // ===================================================

        setResult(
          null
        );


        setError(
          ""
        );


      } catch (err) {

        console.error(
          "IMAGE ANALYSIS ERROR:",
          err
        );


        setImageError(
          err.response
            ?.data
            ?.detail ||
          "Image analysis failed."
        );

      } finally {

        setImageLoading(
          false
        );

      }
    };


  // =========================================================
  // PRICE PREDICTION
  // =========================================================

  const handleSubmit =
    async (
      event
    ) => {

      event.preventDefault();


      setLoading(
        true
      );


      setError(
        ""
      );


      setResult(
        null
      );


      try {

        // ===================================================
        // CREATE REQUEST PAYLOAD
        // ===================================================

        const payload = {

          title:
            form.title,

          category_name:
            form.category_name,

          stars:
            Number(
              form.stars
            ),

          reviews:
            Number(
              form.reviews
            ),

          bought_in_last_month:
            Number(
              form.bought_in_last_month
            ),

          is_best_seller:
            form.is_best_seller,
        };


        console.log(
          "PRICE PREDICTION PAYLOAD:",
          payload
        );


        // ===================================================
        // CALL BACKEND
        // ===================================================

        const data =
          await predictPrice(
            payload
          );


        console.log(
          "PRICE PREDICTION RESULT:",
          data
        );


        // ===================================================
        // SAVE RESULT
        // ===================================================

        setResult(
          data
        );


      } catch (err) {

        console.error(
          "PRICE PREDICTION ERROR:",
          err
        );


        setError(
          err.response
            ?.data
            ?.detail ||
          "Prediction failed."
        );


      } finally {

        setLoading(
          false
        );

      }
    };


  // =========================================================
  // PRICE FORMAT
  // =========================================================

  const formattedPrice =
    result
      ?.predicted_price != null

      ? new Intl.NumberFormat(
          "en-US",
          {
            style:
              "currency",

            currency:
              "USD",
          }
        ).format(
          result
            .predicted_price
        )

      : null;


  // =========================================================
  // CONFIDENCE LABEL
  // =========================================================

  const confidenceLabel = (
    confidence
  ) => {

    if (!confidence) {

      return "Unknown";
    }


    return (
      confidence
        .charAt(0)
        .toUpperCase()

      +

      confidence
        .slice(1)
    );
  };


  // =========================================================
  // ATTRIBUTE RENDER HELPER
  // =========================================================

  const renderAttribute = (
    label,
    values
  ) => {

    // =======================================================
    // NOTHING DETECTED
    // =======================================================

    if (
      !values ||
      values.length === 0
    ) {

      return (

        <div
          className="attribute-item"
        >

          <span
            className="attribute-label"
          >

            {label}

          </span>


          <strong
            className="not-detected"
          >

            Not detected

          </strong>

        </div>
      );
    }


    // =======================================================
    // ATTRIBUTE DETECTED
    // =======================================================

    return (

      <div
        className="attribute-item"
      >

        <span
          className="attribute-label"
        >

          {label}

        </span>


        {
          values.map(
            (
              item,
              index
            ) => (

              <div
                key={
                  `${label}-${index}`
                }
                className="attribute-value-block"
              >

                {/* ==========================================
                    VALUE
                ========================================== */}

                <strong
                  className="attribute-main-value"
                >

                  {
                    typeof item === "string"
                      ? item
                      : item.value
                  }

                </strong>


                {/* ==========================================
                    CONFIDENCE + SOURCE
                ========================================== */}

                {
                  typeof item !== "string" &&
                  (

                    <div
                      className="attribute-meta"
                    >

                      <span
                        className={
                          `confidence-badge confidence-${item.confidence || "unknown"}`
                        }
                      >

                        {
                          confidenceLabel(
                            item.confidence
                          )
                        }

                      </span>


                      {
                        item.source && (

                          <small>

                            {
                              item.source
                            }

                          </small>

                        )
                      }

                    </div>

                  )
                }

              </div>
            )
          )
        }

      </div>
    );
  };


  // =========================================================
  // UI
  // =========================================================

  return (

    <div
      className="app"
    >

      {/* ====================================================
          NAVBAR
      ==================================================== */}

      <header
        className="navbar"
      >

        <div>

          <h2>
            SmartPrice AI
          </h2>


          <span>
            Product Intelligence Platform
          </span>

        </div>


        <div
          className="status"
        >

          <span
            className="status-dot"
          />


          final_clean_v1

        </div>

      </header>


      <main
        className="container"
      >


        {/* ==================================================
            HERO
        ================================================== */}

        <section
          className="hero"
        >

          <div
            className="hero-badge"
          >

            AI-Powered Product Pricing

          </div>


          <h1>

            Price smarter.

            <br />

            Understand products better.

          </h1>


          <p>

            Predict product prices and
            extract visual attributes
            from product images using
            your trained AI pipeline.

          </p>

        </section>


        {/* ==================================================
            IMAGE ANALYSIS
        ================================================== */}

        <section
          className="image-section"
        >

          <div
            className="section-title"
          >

            <p
              className="small-label"
            >

              VISUAL ATTRIBUTE EXTRACTION

            </p>


            <h2>

              Analyze Product Image

            </h2>

          </div>


          <div
            className="image-grid"
          >


            {/* ==============================================
                IMAGE UPLOAD
            ============================================== */}

            <div
              className="image-upload-card"
            >

              {
                !imagePreview
                  ? (

                    <label
                      className="upload-zone"
                    >

                      <div
                        className="upload-icon"
                      >

                        +

                      </div>


                      <h3>

                        Upload product image

                      </h3>


                      <p>

                        JPG, PNG or WEBP

                      </p>


                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={
                          handleImageChange
                        }
                        hidden
                      />

                    </label>

                  )
                  : (

                    <div
                      className="preview-wrapper"
                    >

                      <img
                        src={
                          imagePreview
                        }
                        alt="Product preview"
                        className="image-preview"
                      />


                      <label
                        className="change-image"
                      >

                        Change Image


                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          onChange={
                            handleImageChange
                          }
                          hidden
                        />

                      </label>

                    </div>

                  )
              }


              <button
                type="button"
                className="analyze-button"
                onClick={
                  handleImageAnalysis
                }
                disabled={
                  !imageFile ||
                  imageLoading
                }
              >

                {
                  imageLoading
                    ? "Analyzing Image..."
                    : "Analyze Image"
                }

              </button>


              {
                imageError && (

                  <div
                    className="error-box"
                  >

                    {
                      imageError
                    }

                  </div>

                )
              }

            </div>


            {/* ==============================================
                IMAGE ANALYSIS RESULT
            ============================================== */}

            <div
              className="image-result-card"
            >

              {
                !imageResult &&
                !imageLoading &&
                (

                  <div
                    className="image-empty"
                  >

                    <h3>

                      Extracted attributes
                      will appear here

                    </h3>


                    <p>

                      Upload and analyze
                      a product image.

                    </p>

                  </div>

                )
              }


              {
                imageLoading &&
                (

                  <div
                    className="image-empty"
                  >

                    <div
                      className="loader"
                    />


                    <h3>

                      Running OCR...

                    </h3>


                    <p>

                      Extracting product
                      identity and measurable
                      attributes.

                    </p>

                  </div>

                )
              }


              {
                imageResult &&
                (

                  <div
                    className="image-analysis-result"
                  >


                    {/* ======================================
                        PRODUCT IDENTITY
                    ====================================== */}

                    <p
                      className="small-label"
                    >

                      PRODUCT IDENTITY

                    </p>


                    <div
                      className="identity-section"
                    >


                      <div
                        className="identity-item"
                      >

                        <span>

                          Product Type

                        </span>


                        <strong>

                          {
                            imageResult
                              .product_type
                            ||
                            "Not detected"
                          }

                        </strong>

                      </div>


                      <div
                        className="identity-item"
                      >

                        <span>

                          Brand

                        </span>


                        <strong>

                          {
                            imageResult
                              .brand
                            ||
                            "Not detected"
                          }

                        </strong>

                      </div>


                      <div
                        className="identity-item"
                      >

                        <span>

                          Variant

                        </span>


                        <strong>

                          {
                            imageResult
                              .variant
                            ||
                            "Not detected"
                          }

                        </strong>

                      </div>

                    </div>


                    {/* ======================================
                        EXTRACTED ATTRIBUTES
                    ====================================== */}

                    <p
                      className="small-label attribute-heading"
                    >

                      EXTRACTED ATTRIBUTES

                    </p>


                    <div
                      className="attributes-grid"
                    >

                      {
                        renderAttribute(
                          "Price",
                          imageResult
                            .attributes
                            ?.price
                        )
                      }


                      {
                        renderAttribute(
                          "Weight",
                          imageResult
                            .attributes
                            ?.weight
                        )
                      }


                      {
                        renderAttribute(
                          "Volume",
                          imageResult
                            .attributes
                            ?.volume
                        )
                      }


                      {
                        renderAttribute(
                          "Storage",
                          imageResult
                            .attributes
                            ?.storage
                        )
                      }


                      {
                        renderAttribute(
                          "Wattage",
                          imageResult
                            .attributes
                            ?.wattage
                        )
                      }


                      {
                        renderAttribute(
                          "Voltage",
                          imageResult
                            .attributes
                            ?.voltage
                        )
                      }


                      {
                        renderAttribute(
                          "Quantity",
                          imageResult
                            .attributes
                            ?.quantity
                        )
                      }


                      {
                        renderAttribute(
                          "Dimensions",
                          imageResult
                            .attributes
                            ?.dimensions
                        )
                      }

                    </div>


                    {/* ======================================
                        OCR TEXT
                    ====================================== */}

                    <div
                      className="ocr-box"
                    >

                      <span>

                        OCR Text

                      </span>


                      <p>

                        {
                          imageResult
                            .ocr_text
                          ||
                          "No text detected"
                        }

                      </p>

                    </div>

                  </div>

                )
              }

            </div>

          </div>

        </section>


        {/* ==================================================
            PRICE PREDICTION
        ================================================== */}

        <section
          className="dashboard"
        >


          {/* ==============================================
              PRODUCT FORM
          ============================================== */}

          <div
            className="form-card"
          >

            <div
              className="card-header"
            >

              <p
                className="small-label"
              >

                PRICE PREDICTION

              </p>


              <h2>

                Product Details

              </h2>

            </div>


            <form
              onSubmit={
                handleSubmit
              }
            >


              {/* ============================================
                  PRODUCT TITLE
              ============================================ */}

              <div
                className="field"
              >

                <label>

                  Product title

                </label>


                <input
                  name="title"
                  value={
                    form.title
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="Example: Head & Shoulders Shampoo 700 ml"
                  required
                />

              </div>


              {/* ============================================
                  CATEGORY
              ============================================ */}

              <div
                className="field"
              >

                <label>

                  Category

                </label>


                <input
                  name="category_name"
                  value={
                    form.category_name
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="Example: Shampoo"
                  required
                />

              </div>


              {/* ============================================
                  OTHER STRUCTURED FEATURES
              ============================================ */}

              <div
                className="form-grid"
              >


                <div
                  className="field"
                >

                  <label>

                    Rating

                  </label>


                  <input
                    type="number"
                    name="stars"
                    min="0"
                    max="5"
                    step="0.1"
                    value={
                      form.stars
                    }
                    onChange={
                      handleChange
                    }
                  />

                </div>


                <div
                  className="field"
                >

                  <label>

                    Reviews

                  </label>


                  <input
                    type="number"
                    name="reviews"
                    min="0"
                    value={
                      form.reviews
                    }
                    onChange={
                      handleChange
                    }
                  />

                </div>


                <div
                  className="field"
                >

                  <label>

                    Bought Last Month

                  </label>


                  <input
                    type="number"
                    name="bought_in_last_month"
                    min="0"
                    value={
                      form
                        .bought_in_last_month
                    }
                    onChange={
                      handleChange
                    }
                  />

                </div>


                <div
                  className="field"
                >

                  <label>

                    Best Seller

                  </label>


                  <div
                    className="checkbox-wrapper"
                  >

                    <input
                      type="checkbox"
                      name="is_best_seller"
                      checked={
                        form
                          .is_best_seller
                      }
                      onChange={
                        handleChange
                      }
                    />


                    <span>

                      {
                        form
                          .is_best_seller
                          ? "Yes"
                          : "No"
                      }

                    </span>

                  </div>

                </div>

              </div>


              {/* ============================================
                  PREDICT BUTTON
              ============================================ */}

              <button
                type="submit"
                className="predict-button"
                disabled={
                  loading
                }
              >

                {
                  loading
                    ? "Running AI Model..."
                    : "Predict Price"
                }

              </button>


              {
                error &&
                (

                  <div
                    className="error-box"
                  >

                    {
                      error
                    }

                  </div>

                )
              }

            </form>

          </div>


          {/* ==============================================
              PRICE RESULT
          ============================================== */}

          <div
            className="result-card"
          >

            {
              !result &&
              !loading &&
              (

                <div
                  className="empty-result"
                >

                  <div
                    className="price-icon"
                  >

                    $

                  </div>


                  <h2>

                    Your prediction
                    will appear here

                  </h2>

                </div>

              )
            }


            {
              loading &&
              (

                <div
                  className="empty-result"
                >

                  <div
                    className="loader"
                  />


                  <h2>

                    Running prediction...

                  </h2>

                </div>

              )
            }


            {
              result &&
                (

                  <div
                    className="prediction-result"
                  >

                    <p
                      className="small-label"
                    >

                      PREDICTED PRICE

                    </p>


                    <div
                      className="price-value"
                    >

                      {
                        formattedPrice
                      }

                    </div>


                    <div
                      className="metrics"
                    >


                      <div
                        className="metric"
                      >

                        <span>

                          Cluster

                        </span>


                        <strong>

                          #
                          {
                            result
                              .cluster_id
                          }

                        </strong>

                      </div>


                      <div
                        className="metric"
                      >

                        <span>

                          Model

                        </span>


                        <strong>

                          {
                            result
                              .model_version
                          }

                        </strong>

                      </div>


                      <div
                        className="metric"
                      >

                        <span>

                          Device

                        </span>


                        <strong>

                          {
                            result
                              .device
                          }

                        </strong>

                      </div>

                    </div>

                  </div>

                )
            }

          </div>

        </section>

      </main>

    </div>
  );
}


export default App;