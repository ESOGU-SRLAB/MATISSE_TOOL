# MATISSE Tool: Intelligent Test Scenario and Test Case Generation Platform

MATISSE Tool is a modern test automation platform designed to optimize software testing processes while offering a user-friendly experience. It has been developed with advanced technologies to generate test scenarios and detailed test cases from various documents.

## Features

- **Functional and Non-Functional Tests:** Identifies appropriate test categories based on document content and creates contextually accurate test scenarios.
- **Test Case Generation:** Derives specific and detailed test cases from test scenarios.
- **User-Friendly Interface:** Provides an intuitive Streamlit-based interface for easy document upload, test category selection, and scenario customization.
- **LLM Integration:** Utilizes modern large language models such as Llama, Mistral, and Codellama to generate test scenarios.
- **Flexible Data Management:** Manages session data, user inputs, and test results using MongoDB.

## Technologies Used

- **LLM (Large Language Model):** Generates context-aware test scenarios using natural language processing technologies.
- **Ollama:** A platform that simplifies the integration and execution of LLM models.
- **Streamlit:** Offers a user interface and real-time processing support.
- **MongoDB:** Provides flexible and scalable data management.

# Installation Guide

This document provides detailed instructions on how to install and set up the Smart Test Generation Tool.

## Step 1: Clone the Repository

First, clone the repository to your local machine:

```bash
git clone <repository_url>
cd <repository_name>
```

## Step 2: Set Up a Virtual Environment (Optional but Recommended)

Create and activate a virtual environment to isolate the dependencies:

For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

Use the following command to install all the necessary Python libraries listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Key Libraries Installed

- **Streamlit**: A framework for building interactive web applications in Python.
- **Pydantic**: A library for data validation and parsing using Python type annotations.
- **Llama Index**: Provides integrations for managing and querying large language models.
- **Requests**: Enables making HTTP requests to interact with APIs.
- **JSON**: Used for handling JSON data processing.
- **UUID**: Generates universally unique identifiers.
- **Datetime**: Handles timestamping for logs and operations.

## Step 4: Run the Application

Once everything is set up, you can run the application using the following command:

```bash
streamlit run app.py
```

This will launch the Smart Test Generation Tool in your default web browser.

---

You're now ready to use the Smart Test Generation Tool!
