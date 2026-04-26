## Problem Statement

Build an AI-powered restaurant recommendation system inspired by Zomato.  
The application should combine structured restaurant data with a Large Language Model (LLM) to deliver personalized and easy-to-understand recommendations based on user preferences.

## Objective

Design and implement an application that:

- Accepts user preferences such as location, budget, cuisine, and minimum rating.
- Uses a real restaurant dataset as the source of recommendations.
- Leverages an LLM to produce personalized, human-like suggestions.
- Presents results in a clear, useful, and user-friendly format.

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  [https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract key fields such as:
  - Restaurant name
  - Location
  - Cuisine
  - Estimated cost
  - Rating

### 2. User Input

Collect user preferences, including:

- Location (for example, Delhi or Bangalore)
- Budget range (low, medium, high)
- Preferred cuisine (for example, Italian or Chinese)
- Minimum acceptable rating
- Additional preferences (for example, family-friendly, quick service)

### 3. Integration Layer

- Filter restaurant records based on user input.
- Prepare structured candidate data for the LLM.
- Build a prompt that helps the LLM reason about, compare, and rank options.

### 4. Recommendation Engine

Use the LLM to:

- Rank the best matching restaurants.
- Explain why each recommendation fits the user’s preferences.
- Optionally provide a short summary of the top choices.

### 5. Output Display

Present top recommendations in a clean format with:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation