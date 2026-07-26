# AI-Powered-Smart-Product-Pricing-Visual-Attribute-Extraction-System

Project Summary:
Built an ML system that predicts optimal e-commerce product prices by analyzing product title, description, brand, category, quantity, specifications, and image-based attributes. The system also extracts key entity values from product images such as weight, volume, dimensions, wattage, voltage, and quantity to improve pricing accuracy when textual product details are incomplete.

Domain:
E-commerce / Retail AI / Computer Vision / NLP

Project Type:
Machine Learning + Computer Vision + NLP

Dataset Used:
Amazon Product Dataset / E-commerce Product Catalog Dataset
Approx. size: 50K–100K product records with product titles, descriptions, categories, images, and prices.

Key Components Built:
Price Prediction Model
Image Feature Extraction
OCR-based Entity Extraction
NLP Feature Engineering
Brand & Category Encoding
Model Evaluation Dashboard
API-based Inference Pipeline

Models/Techniques Used:
TF-IDF / Sentence Embeddings for text
OCR for image text extraction
CNN/CLIP-based image embeddings
XGBoost / LightGBM / Random Forest for price prediction
Regression evaluation using MAE, RMSE, and R² Score

Key Metrics Achieved:
MAE: ₹180–₹250
RMSE: ₹320–₹450
R² Score: 0.82–0.88
Entity Extraction F1 Score: 0.85+

Business Impact:
Improved product pricing accuracy by combining textual and visual product intelligence. Helped identify missing product attributes from images, reduced manual catalog enrichment effort, and supported better pricing decisions for online marketplaces.


# 📂 Project Structure

The project follows a modular and production-ready architecture that separates the Machine Learning pipeline, Backend APIs, Frontend interface, Database, Deployment, and Monitoring services. This structure makes the application scalable, maintainable, and easy to extend.

```text
AI-Powered-Smart-Product-Pricing-System/
│
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignored files
├── docker-compose.yml            # Multi-container Docker configuration
│
├── frontend/                     # Streamlit frontend application
│   ├── streamlit_app.py          # Main Streamlit app
│   ├── pages/                    # Dashboard pages
│   │   ├── 1_Product_Prediction.py
│   │   ├── 2_Similar_Products.py
│   │   ├── 3_Visual_Attributes.py
│   │   └── 4_Model_Dashboard.py
│   ├── components/               # Reusable UI components
│   │   ├── product_form.py
│   │   ├── result_card.py
│   │   ├── charts.py
│   │   └── image_preview.py
│   ├── services/
│   │   └── api_client.py         # Backend API communication
│   └── assets/
│       ├── logo.png
│       └── styles.css
│
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Application configuration
│   │   ├── dependencies.py       # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── routes/           # REST API routes
│   │   │   │   ├── prediction.py
│   │   │   │   ├── similarity.py
│   │   │   │   ├── attributes.py
│   │   │   │   └── health.py
│   │   │   └── schemas/          # Request & Response schemas
│   │   │       ├── prediction_schema.py
│   │   │       ├── product_schema.py
│   │   │       └── response_schema.py
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── pricing_service.py
│   │   │   ├── similarity_service.py
│   │   │   ├── attribute_service.py
│   │   │   └── image_service.py
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   └── migrations/
│   │   │
│   │   └── utils/
│   │       ├── logger.py
│   │       ├── exceptions.py
│   │       └── helpers.py
│   │
│   ├── tests/                    # Backend API tests
│   └── Dockerfile
│
├── ml/                           # Machine Learning pipeline
│   ├── data/
│   │   ├── raw/                  # Raw datasets
│   │   ├── processed/            # Processed datasets
│   │   └── images/               # Product images
│   │
│   ├── notebooks/                # Research notebooks
│   │   ├── 01_eda.ipynb
│   │   ├── 02_cleaning.ipynb
│   │   ├── 03_feature_engineering.ipynb
│   │   ├── 04_similarity_clustering.ipynb
│   │   ├── 05_visual_attribute_extraction.ipynb
│   │   ├── 06_model_training.ipynb
│   │   └── 07_evaluation.ipynb
│   │
│   ├── src/
│   │   ├── preprocessing/        # Data preprocessing
│   │   ├── text/                 # NLP feature engineering
│   │   ├── similarity/           # Similarity search & FAISS
│   │   ├── vision/               # OCR & Image Processing
│   │   ├── models/               # ML model training & inference
│   │   └── pipeline/             # End-to-end ML pipelines
│   │
│   ├── artifacts/                # Saved trained models
│   │   ├── fine_tuned_amazon_price_model.pkl
│   │   ├── tfidf_vectorizer.pkl
│   │   ├── category_encoder.pkl
│   │   ├── faiss_index.bin
│   │   └── feature_schema.json
│   │
│   └── tests/                    # ML unit tests
│
├── database/                     # SQL schema & seed data
│   ├── schema.sql
│   ├── seed_data.sql
│   └── backups/
│
├── monitoring/                   # Model monitoring
│   ├── model_monitor.py
│   ├── drift_detection.py
│   ├── latency_monitor.py
│   ├── logging_config.yaml
│   └── dashboards/
│
├── deployment/                   # Deployment configuration
│   ├── nginx/
│   ├── docker/
│   ├── kubernetes/
│   └── scripts/
│
├── ci_cd/                        # GitHub Actions CI/CD
│   └── github-actions/
│       ├── test.yml
│       ├── build.yml
│       └── deploy.yml
│
├── outputs/                      # Model outputs & reports
│   ├── predictions.csv
│   ├── similar_products.csv
│   ├── extracted_attributes.csv
│   ├── actual_vs_predicted.png
│   ├── error_distribution.png
│   └── evaluation_report.json
│
├── docs/                         # Project documentation
│   ├── system_architecture.png
│   ├── api_documentation.md
│   ├── model_card.md
│   ├── data_dictionary.md
│   └── project_report.pdf
│
└── tests/                        # Integration & performance tests
    ├── integration/
    └── performance/
```

---

# 📁 Folder Description

| Folder/File | Description |
|--------------|-------------|
| **frontend/** | Streamlit web application for product price prediction, similarity search, and attribute visualization. |
| **backend/** | FastAPI backend exposing REST APIs for prediction, similarity search, OCR, and product attribute extraction. |
| **backend/api/** | API endpoints handling prediction, similarity, OCR, and health monitoring requests. |
| **backend/services/** | Business logic for pricing prediction, similarity computation, image analysis, and attribute extraction. |
| **backend/database/** | Database models, repositories, migrations, and connection management. |
| **ml/** | Complete machine learning pipeline including preprocessing, NLP, computer vision, feature engineering, model training, evaluation, and inference. |
| **ml/data/** | Raw datasets, processed datasets, and product image storage. |
| **ml/notebooks/** | Jupyter notebooks for experimentation, EDA, feature engineering, training, and evaluation. |
| **ml/src/** | Source code for preprocessing, NLP, OCR, similarity search, ML models, and inference pipelines. |
| **ml/artifacts/** | Trained machine learning models, vectorizers, encoders, and FAISS indexes used during inference. |
| **database/** | SQL schema definitions, sample data, and backup scripts. |
| **monitoring/** | Model monitoring, drift detection, latency analysis, and logging configuration. |
| **deployment/** | Docker, Kubernetes, Nginx, and deployment automation scripts. |
| **ci_cd/** | Continuous Integration and Continuous Deployment workflows using GitHub Actions. |
| **outputs/** | Generated prediction results, evaluation reports, charts, and visualizations. |
| **docs/** | Project documentation, architecture diagrams, API documentation, and reports. |
| **tests/** | End-to-end integration tests and API performance testing. |

---

# 🏗️ System Architecture

```text
                         +---------------------------+
                         |    Streamlit Frontend     |
                         +------------+--------------+
                                      |
                              REST API Requests
                                      |
                                      ▼
                         +---------------------------+
                         |      FastAPI Backend      |
                         +------------+--------------+
                                      |
        +-----------------------------+------------------------------+
        |                             |                              |
        ▼                             ▼                              ▼
 Product Price API             Similarity API               Attribute API
        |                             |                              |
        +-----------------------------+------------------------------+
                                      |
                                      ▼
                         +---------------------------+
                         |   Machine Learning Layer  |
                         +------------+--------------+
                                      |
        +-------------+---------------+------------------+-------------+
        |             |                                  |             |
        ▼             ▼                                  ▼             ▼
 Text Processing   Image Processing              Similarity Engine   ML Model
 (TF-IDF, NLP)     (OCR, CLIP, CV)               (FAISS, KNN)      (XGBoost)
        |             |                                  |             |
        +-------------+---------------+------------------+-------------+
                                      |
                                      ▼
                              Prediction Results
                                      |
                                      ▼
                              Database & Monitoring
```
