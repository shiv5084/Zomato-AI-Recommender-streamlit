## Phase-Wise Architecture

### Phase 1: Data Foundation

**Goal:** Build a reliable restaurant dataset layer.

**Core components:**
- Dataset loader (Hugging Face Zomato dataset)
- Data preprocessing pipeline
- Data quality checks (missing values, invalid ratings/cost)
- Normalized storage (CSV/DB table)

**Input -> Output:**
- Raw dataset -> Clean, structured restaurant records

**Deliverables:**
- Reusable ingestion script
- Cleaned dataset with required schema

### Phase 2: Preference Capture Layer

**Goal:** Collect user needs in a structured format.

**Core components:**
- Input interface (CLI, web form, or API request body)
- Preference validator (location, budget, cuisine, rating)
- Preference schema object (standard internal format)

**Input -> Output:**
- User preferences -> Validated preference object

**Deliverables:**
- Input contract/schema
- Validation rules and error messages

### Phase 3: Candidate Retrieval Layer

**Goal:** Retrieve restaurant candidates that match hard constraints.

**Core components:**
- Rule-based filter engine
- Query module (location, budget range, cuisine, min rating)
- Candidate shortlist builder (Top-N records for LLM context)

**Input -> Output:**
- Validated preferences + cleaned data -> Filtered candidate set

**Deliverables:**
- Deterministic filtering logic
- Candidate shortlist API/function

### Phase 4: LLM Reasoning and Ranking Layer

**Goal:** Convert candidate data into personalized recommendations.

**Core components:**
- Prompt template builder
- LLM orchestration module
- Ranking + explanation generator
- Safety/format constraints (consistent structured output)

**Input -> Output:**
- Candidate set + preferences -> Ranked recommendations with explanations

**Deliverables:**
- Prompt templates (base + optional variants)
- Response parser/formatter
- Ranked recommendation payload

### Phase 5: Presentation and Experience Layer

**Goal:** Deliver understandable and actionable results.

**Core components:**
- Result renderer (UI/API response formatter)
- Recommendation cards/list view
- Optional summary section ("Best overall", "Best budget", etc.)

**Input -> Output:**
- Ranked recommendation payload -> User-friendly display

**Deliverables:**
- Final response format
- Consistent display template

### Phase 6: Evaluation and Feedback Loop

**Goal:** Improve recommendation quality over time.

**Core components:**
- Logging and monitoring (queries, selected recommendations)
- Offline evaluation metrics (precision@k, relevance score)
- User feedback capture (like/dislike, selected option)
- Prompt/filter tuning loop

**Input -> Output:**
- Usage + feedback data -> Improved prompts, filters, and ranking quality

**Deliverables:**
- Evaluation dashboard/report
- Iterative improvement backlog

## End-to-End Data Flow (High Level)

User Preferences  
-> Preference Validation  
-> Candidate Retrieval (rule-based filters)  
-> LLM Ranking and Explanation  
-> Recommendation Display  
-> Feedback Collection and Continuous Improvement
