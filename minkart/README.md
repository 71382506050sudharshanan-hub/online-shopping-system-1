# MINKART - Online Shopping System

**Tagline:** *Shop Smart. Live Better.*

Minkart is a modern, full-stack, responsive e-commerce web application featuring a production-ready architecture, seed catalog with 65+ realistic products across 11 categories, server-side cart & transaction management, stock deduction, mock payments, automated Pytest suite, Docker containerization, and a 4-stage GitHub Actions CI/CD pipeline.

---

## 🚀 Key Features

1. **Rich Product Catalog:** Browse 65+ realistic sample products across 11 major categories (*Electronics, Fashion, Home & Kitchen, Beauty & Personal Care, Grocery, Sports & Fitness, Books & Education, Toys & Games, Automotive, Pet Supplies, Other*).
2. **Advanced Search & Filtering:** Filter catalog items by live search query, category, brand, price range slider/inputs, star rating threshold, and sort order.
3. **Product Details:** Detailed view page with stock indicator, discount badges, review ratings, SKU, and quantity limit selector.
4. **Server-Side Session Cart:** Cart management with real-time stock ceiling checks, free shipping threshold calculation, and automatic subtotals.
5. **Transactional Checkout:** Atomic SQLite order creation, customer input validation, mock payment gateway choices, stock decrementing, and automatic rollback on errors.
6. **Order Confirmation:** Order success view with complete itemized breakdown, receipt printing, and order ID generation.
7. **Production DevOps & CI/CD:** Integrated Gunicorn server, Docker Compose orchestration, Pytest automated testing, and GitHub Actions workflow.

---

## 🛠️ Technology Stack

* **Frontend:** HTML5, CSS3 (Vanilla CSS System with Glassmorphism & Micro-animations), JavaScript (ES6+ AJAX & Toast Notifications)
* **Backend:** Python Flask
* **Database:** SQLite (Auto-initialized with seed dataset on launch)
* **Server:** Gunicorn
* **Testing:** Pytest
* **Containerization:** Docker & Docker Compose
* **CI/CD:** GitHub Actions

---

## 📁 Project Architecture

```text
Developer (Git Commit & Push)
   ↓
GitHub Repository
   ↓
GitHub Actions Pipeline
   ├── Stage 1: Pytest Automated Suite
   ├── Stage 2: Docker Image Build
   ├── Stage 3: Push to Docker Hub (<DOCKERHUB_USERNAME>/minkart:latest)
   └── Stage 4: MVP Simulated Deployment Verification
   ↓
Minkart Application (Gunicorn + SQLite on Port 5000)
```

---

## 💻 Local Setup Instructions

### Prerequisites

* Python 3.10+
* Git

### Step-by-Step Execution

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd minkart
   ```

2. **Create and activate virtual environment:**

   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install project dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Flask application:**

   ```bash
   python app.py
   ```

   Open your browser at `http://localhost:5000`.

---

## 🧪 Running Automated Tests

Run the Pytest suite to verify application routes, catalog filtering, cart logic, checkout validation, and database transaction integrity:

```bash
pytest -v
```

---

## 🐳 Running with Docker & Docker Compose

### Start Containerized Application

```bash
docker compose up --build -d
```

Access the application at `http://localhost:5000`.

### View Logs

```bash
docker compose logs -f
```

### Stop Containers

```bash
docker compose down
```

---

## 🔄 GitHub Actions CI/CD Pipeline

The `.github/workflows/cicd.yml` pipeline runs automatically on every push or pull request to `main`/`master` and includes four automated stages:

1. **Stage 1 — Test:** Sets up Python 3.10, installs dependencies, and runs `pytest -v`.
2. **Stage 2 — Build:** Sets up Docker Buildx and builds the production Docker image.
3. **Stage 3 — Push:** Authenticates with Docker Hub using repository secrets and pushes tagged images (`latest` and `${{ github.sha }}`).
4. **Stage 4 — Deploy Verification:** Pulls the built image, starts a test container instance, performs HTTP verification against `http://localhost:5000/`, and outputs deployment logs.

### 🔑 Configuring GitHub Secrets

To enable Docker Hub push and verification in GitHub Actions, configure the following repository secrets:

1. Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add:
   * `DOCKERHUB_USERNAME`: Your Docker Hub account username.
   * `DOCKERHUB_TOKEN`: Your Docker Hub Personal Access Token (PAT).

---

## 📄 License

Educational & DevOps MVP Showcase Project — **Minkart**.
