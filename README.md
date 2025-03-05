# Tenant Screening Match Evaluator

A Flask-based API for evaluating potential matches in tenant screening processes. This service analyzes tenant information against screening results to determine the relevance and risk level of potential matches.

## Overview

The Tenant Screening Match Evaluator is designed to help property managers and screening services evaluate potential tenant matches against various databases. It uses a sophisticated algorithm to calculate relevance scores based on multiple factors including name similarity, date of birth, location, nationality, and gender.

## Features

- Evaluates tenant information against screening results
- Calculates relevance scores using weighted factors
- Categorizes matches into different relevance levels
- Provides detailed match and mismatch reasons
- RESTful API for easy integration

## Installation

### Prerequisites
Ensure you have **Python 3.7+** installed on your system. You can check your Python version by running:

```bash
python --version
```

### Step 1: Clone the Repository
Clone this repository to your local machine:

```bash
git clone https://github.com/your-username/your-flask-app.git
cd your-flask-app
```

### Step 2: Create a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

#### **Windows** (Command Prompt or PowerShell):
```bash
python -m venv venv
venv\Scripts\activate
```

#### **Mac/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
Install required Python packages:

```bash
pip install -r requirements.txt
```

## Running the Application

After installing dependencies, you can start the Flask application with:

```bash
flask run
```

By default, the application runs on `http://127.0.0.1:5000/`. You can change the port using:

```bash
flask run --host=0.0.0.0 --port=8080
```

## Running Unit Tests

To run the unit tests, use the following command:

```bash
python -m pytest --cov=challenge tests/
```

Or use the provided shell script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Environment Variables
You may need to set environment variables before running the application:


```bash
export FLASK_APP=app.py
export FLASK_ENV=development  # Enables debug mode
```

On Windows (Command Prompt):
```bash
set FLASK_APP=challenge/app.py
set FLASK_ENV=development
```


## USAGE

The API will be available at `http://localhost:5000`.

### API Endpoints

- `POST /evaluate`: Evaluate a tenant against pipeline data
  - Request body: JSON object containing `tenant` and `pipeline_data`
  - Response: Evaluation results

### Example Usage

```python
import requests

url = "http://localhost:5000/evaluate"
data = {
    "tenant": {
        "first_name": "Juan Carlos",
        "last_name": "Perez Gonzalez",
        "dob": "1990-05-15",
        "gender": "male",
        "nationality": "Mexican",
        "location": "Bogota, Colombia"
    },
    "pipeline_data": {
        "pipeline": [
            {
                "type": "refinitiv-blacklist",
                "results": [
                    {
                        "id": 1,
                        "first_name": "Juan Carlos",
                        "last_name": "Perez Gonzalez",
                        "dob": "1990-05-15",
                        "gender": "male",
                        "nationality": "Mexican",
                        "location": "Bogota, Colombia",
                        "risk_type": "Low"
                    }
                ]
            }
        ]
    }
}

response = requests.post(url, json=data)
print(response.json())


