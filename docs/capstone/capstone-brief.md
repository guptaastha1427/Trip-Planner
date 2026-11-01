Trip Planner AI Agent Capstone Project
Creating a capstone project that demonstrates real-world AI engineering skills is essential for your portfolio. This project goes beyond simple chatbots to showcase your ability to build production-grade AI applications with external data integration, agentic workflows, and persistent state management.

We’ll guide you through building a complete trip planning application with three core components:

1. Agent Architecture with Tool Calling

Implement OpenAI’s Responses API with function calling
Design and integrate custom tools for POI search and travel guide retrieval
Handle multi-step reasoning and tool orchestration
Debug and trace agent execution paths
2. Real-Time Data Integration

Connect to OpenStreetMap’s Nominatim API for geocoding
Query Overpass API for live Points of Interest
Implement optional Wikivoyage RAG (Retrieval-Augmented Generation)
Handle API rate limiting, retries, and error cases
3. User Experience and Feedback Loops

Build an interactive Streamlit interface with session state management
Create interactive maps with PyDeck for itinerary visualization
Implement user feedback collection to improve future recommendations
Add itinerary persistence and refinement capabilities
Throughout this project, you’ll work with real APIs, handle authentication and rate limiting, validate AI-generated outputs against available data, and create a polished user interface—all skills essential for production AI engineering!

Project Objectives
Build a production-ready AI application using Streamlit
Implement agentic AI workflows with OpenAI’s function calling
Integrate multiple external APIs (OpenStreetMap, Wikivoyage)
Create interactive data visualizations with PyDeck
Design feedback loops to improve model performance
Handle state management and data persistence
Validate and constrain AI outputs for reliability
Prerequisites
Python fundamentals
API integration: REST APIs, authentication, error handling
Data Science libraries: NumPy, Pandas, scikit-learn
AI/ML foundations: Prompt engineering, RAG (Retrieval-Augmented Generation)
OpenAI API: Chat completions, function calling, Responses API
Streamlit: UI components, session state, callbacks
Let’s build an intelligent trip planner that showcases your AI engineering skills! Happy coding!





Set Up Project Structure and API Integration
Set up your development environment with all required dependencies and establish connections to the OpenAI API and OpenStreetMap services. Create a basic Streamlit app skeleton with API key management.

Instructions

Install required packages: streamlit, openai, pydeck, requests, scikit-learn
Create a secure method for users to provide their OpenAI API key (session state storage)
Test connections to Nominatim (geocoding) and Overpass API (POI search)
Implement proper User-Agent headers for OpenStreetMap API compliance
Create data directory structure for storing feedback and app state

Use st.text_input(type="password") for secure API key entry. Store the key in st.session_state but provide an option to clear it after use. Always include proper User-Agent headers when calling external APIs—many services (like Nominatim) require identifying contact information to prevent abuse.





Build POI Search Tool
Implement the search_pois tool that geocodes cities and retrieves relevant Points of Interest from OpenStreetMap based on user interests. This tool will be called by your AI agent.

Instructions

Create a function to geocode city names using Nominatim API
Build Overpass API queries that filter POIs by category (museums, restaurants, parks, etc.)
Map user interests (like “outdoors”, “food”, “history”) to OpenStreetMap tags
Implement caching with @st.cache_data to reduce API calls
Return structured POI data including: poi_id, name, category, lat, lon, url
Add retry logic and error handling for API failures

OpenStreetMap uses a tagging system: tourism=museum, amenity=restaurant, leisure=park, etc. Create a mapping dictionary like:

INTEREST_TO_TAGS = {
 "museums": [("tourism", "museum|gallery")],
 "food": [("amenity", "restaurant|cafe|fast_food")],
 "outdoors": [("leisure", "park|nature_reserve"), ("natural", "peak|beach")]
}
Use regex patterns in Overpass queries to match multiple tag values efficiently.


Implement Wikivoyage RAG
Build a retrieval-augmented generation (RAG) system that fetches travel guides from Wikivoyage and retrieves relevant context to enhance itinerary generation. This is an optional enhancement that demonstrates advanced AI techniques.

Instructions

Query Wikivoyage API to find and fetch article content for destinations
Clean HTML content and extract plain text
Chunk text into manageable segments (800-1000 characters)
Build TF-IDF vectorizer and document embeddings using scikit-learn
Implement semantic search to retrieve top-k relevant chunks
Return chunk metadata including chunk_id, source, text, score
Cache vectorized indices to avoid reprocessing on every query

Wikivoyage can return 403 errors if User-Agent headers aren’t properly set. Use a header like: "User-Agent": "trip-planner-capstone/1.0 (contact@example.com)". When chunking text, preserve paragraph boundaries and avoid splitting mid-sentence. Use cosine_similarity from scikit-learn to rank chunks by relevance to the query.


Design Agent System with Function Calling
Create the AI agent that orchestrates tool calls to generate personalized itineraries. Implement OpenAI’s Responses API with strict function schemas and proper error handling.

Instructions

Define function schemas for search_pois and retrieve_guides with strict mode enabled
Implement the agent loop: call model → execute tools → return results → repeat
Parse tool call arguments and route to appropriate Python functions
Track tool state across calls (POIs discovered, chunks retrieved, city metadata)
Implement max step limits to prevent infinite loops
Add execution tracing to visualize agent decision-making
Validate that the final itinerary only references POIs actually returned by tools

Use OpenAI’s strict: True parameter in function definitions to enforce exact schema compliance. This prevents the model from hallucinating parameters. Keep a tool_state dictionary to accumulate all POIs and chunks across multiple tool calls—the model needs access to this data when generating the final itinerary.

Example validation:

def validate_itinerary_poi_ids(itin, allowed_pois):
 valid_ids = set(allowed_pois.keys())
 for day in itin["days"]:
 for block in ["morning", "afternoon", "evening"]:
 for item in day[block]:
 if item["poi_id"] not in valid_ids:
 raise ValueError(f"Invalid poi_id: {item['poi_id']}")


Create Streamlit UI with Itinerary Display
Build an intuitive user interface for trip planning with input controls, itinerary generation, and beautiful output formatting. Make the experience feel polished and professional.

Instructions

Create input fields for: destination, trip length, pace, interests, constraints
Add a “Generate Itinerary” button that triggers the agent workflow
Display a status indicator showing agent progress and tool calls
Render the generated itinerary with clear day/block structure
Format POI information: name, category, explanation (“why” this place)
Include source citations if RAG was used
Add a download button for itinerary JSON export
Implement session state persistence so itineraries survive page refreshes
Use Streamlit columns for clean layouts:

col1, col2 = st.columns(2)
with col1:
 st.subheader("Morning")
 for item in morning_activities:
 st.markdown(f"**{item['name']}**")
 st.caption(item["why"])
Persist the itinerary to data/app_state.json so users don’t lose their work if they refresh the page or return later.



Add Interactive Map Visualization
Visualize the itinerary on an interactive map using PyDeck, showing POI locations and day-by-day routes. This helps users understand the spatial layout of their trip.

Instructions

Extract latitude/longitude coordinates from selected POIs
Create a PyDeck ScatterplotLayer for POI markers
Add a PathLayer connecting POIs in temporal order
Implement a day filter dropdown to show individual days or entire trip
Calculate appropriate zoom level based on POI spread
Add tooltips showing POI name, category, and day/block
Support both light and dark map styles
Handle the edge case where changing filters doesn’t clear the itinerary
Use radius in meters for ScatterplotLayer so dots scale naturally with zoom:

pdk.Layer(
 "ScatterplotLayer",
 data=points,
 get_position="[lon, lat]",
 get_radius=35, # meters
 radius_min_pixels=3,
 radius_max_pixels=10,
)
Important: Render the itinerary outside button callbacks to prevent the UI from blanking when users interact with the map controls.


Implement Itinerary Refinement
Allow users to refine their itinerary through natural language requests. Implement both full-itinerary refinement and single-day regeneration while maintaining consistency.

Instructions

Add a text input for refinement requests (e.g., “make it more outdoorsy”)
Pass the existing itinerary JSON to the agent along with refinement instructions
Validate that refined itineraries still only use valid POI IDs
For single-day regeneration, verify that other days remain unchanged
Update session state and persist changes to disk
Allow multiple rounds of refinement without losing previous work
Show before/after comparisons when helpful
When regenerating a single day, explicitly instruct the model to leave other days unchanged:

prompt = f"""
Goal: ONLY modify day {target_day}. All other days must remain EXACTLY unchanged.
Compare JSON structures to verify compliance.

Existing itinerary: {json.dumps(itin)}
Request: {user_request}
"""
After generation, verify compliance programmatically before accepting the new itinerary.




Build Feedback Loop System
Collect user feedback on individual POIs and use it to improve future recommendations. This demonstrates how AI systems can learn from user interactions over time.

Instructions

Create a feedback UI with upvote/downvote buttons for each POI in the itinerary
Store feedback events in a JSONL file with timestamps
Calculate boost scores per POI based on accumulated feedback (+0.25 per upvote, -0.35 per downvote)
Apply boosts when ranking POIs in search_pois tool
Scope feedback to specific cities (same POI in different cities tracked separately)
Display feedback statistics or trends (optional)
Store feedback with enough context to be useful:

feedback_event = {
 "ts": time.time(),
 "city_key": "santa fe, nm",
 "poi_id": "osm_way_12345",
 "vote": "up" # or "down"
}
When searching POIs, compute boosts and apply them during ranking:

boost = feedback_boost_map(city_key)
for poi in pois:
 poi["_score"] = poi["_base_score"] + boost.get(poi["poi_id"], 0.0)
pois.sort(key=lambda p: p["_score"], reverse=True)



Add Error Handling and Edge Cases
Make your application robust by handling API failures, invalid inputs, and edge cases gracefully. Production applications must fail gracefully and provide helpful error messages.

Instructions

Handle cases where geocoding returns no results
Manage API rate limits with exponential backoff retries
Validate all user inputs before passing to agent
Handle cases where no POIs match user criteria
Catch and display JSON parsing errors with helpful messages
Add timeout handling for long-running agent calls
Test with cities that have limited POI data
Ensure the app doesn’t crash on malformed API responses
Use try-except blocks strategically and provide context:

try:
 itin = extract_json(raw_output)
except ValueError as e:
 st.error(f"Could not parse itinerary: {e}")
 with st.expander("Raw model output"):
 st.code(raw_output)
 st.stop()
For external APIs, implement retry logic:

for attempt in range(3):
 try:
 response = requests.get(url, timeout=20)
 if response.status_code == 429: # rate limit
 time.sleep(2 ** attempt)
 continue
 response.raise_for_status()
 return response.json()
 except Exception as e:
 if attempt == 2:
 raise



Optimize Performance and User Experience
Fine-tune your application for speed and usability. Implement caching, optimize API calls, and create a smooth user experience that feels responsive and professional.

Instructions

Add execution trace viewer showing agent steps and timings
Implement “Fast Mode” that limits tool calls for quicker results
Use @st.cache_data for geocoding and RAG indices
Add loading spinners and status indicators during long operations
Optimize map rendering (appropriate dot sizes, smooth zoom)
Provide clear instructions and helpful tooltips
Add configuration options in sidebar (model selection, max steps, etc.)
Test with various trip lengths and destinations to ensure consistent performance
Fast mode can dramatically improve UX:

if fast_mode:
 instructions = "Call search_pois ONCE with broad criteria (limit=40)"
 max_steps = 5
else:
 instructions = "Call search_pois 2-3 times with different queries (limit=30)"
 max_steps = 10
Cache expensive operations:

@st.cache_data(ttl=3600) # cache for 1 hour
def geocode_city(city, user_agent):
 # expensive API call
 return result




Polish and Deploy
Add final touches to make your project portfolio-ready and optionally deploy it for public access. A deployed project has significantly more impact on your portfolio than local-only demos.

Instructions

Write comprehensive README with setup instructions, features, and screenshots
Add example outputs and use cases to your documentation
Include architecture diagram showing data flow
Document API requirements and rate limits
Test with multiple users/sessions simultaneously
Deploy to Streamlit Cloud, Hugging Face Spaces, or similar platform
Add usage analytics (optional)
Create a video showcasing key features
For deployment, ensure:

API keys are managed via environment variables or user input (never hardcoded)
External API rate limits are handled gracefully for multiple users
Session state is isolated between users
Large cache data doesn’t exceed platform limits
Great README sections to include:

Project overview with screenshot
Key features and capabilities
Architecture diagram
Setup instructions
API requirements and costs
Known limitations
Future enhancements
Credits and resources



Enhance and Extend (Optional)
Take your AI Trip Planner to the next level by adding advanced features and improvements. Here are some ideas to get you started:

Implement user authentication to save trip plans
Add a database to store historical searches
Incorporate image generation for destination previews
Implement a comparison feature that shows multiple trip options side-by-side.
Integrate real-time weather forecasts
Add budget tracking
Create shareable trip itineraries that users can export as PDFs
Start with one enhancement at a time and test thoroughly before adding more:

User Authentication: Consider using Streamlit’s session state or integrating services like Auth0
Database Functionality: SQLite is a good starting point for local storage, while Supabase or Firebase work well for cloud-based solutions
New AI Features: Think about API costs and response times—you may want to add caching to avoid redundant calls
UI/UX Design: Update your interface to accommodate new features without overwhelming users using Streamlit’s layout options





Going off-platform:
For this particular project, you will be using Streamlit to build an interactive web application. If you need help with your setup, follow these steps to get started off-platform:

Installation Steps:

Install Python 3.8+: Ensure you have Python 3.8 or higher installed on your system

Python Installation Guide for Mac and Windows
Python Installation Guide for Chromebooks
Set up a virtual environment (recommended):

 python -m venv trip-planner-env
 source trip-planner-env/bin/activate # On Windows: trip-planner-env\Scripts\activate

Install required packages:
 pip install streamlit openai pydeck requests scikit-learn numpy pandas

Create your project structure:
 trip-planner/
 ├── app.py
 ├── data/
 │ ├── app_state.json
 │ └── feedback.jsonl
 └── README.md

Run your Streamlit app:
 streamlit run app.py

Additional Resources:

Getting Started with Streamlit
Streamlit Tutorial
API Keys and Access:
This project requires access to external APIs. Here’s what you’ll need and how to obtain them:

1. OpenAI API Key (Required)
Purpose: Powers the AI agent that generates itineraries using function calling

How to obtain:

Sign up at platform.openai.com
Navigate to API Keys
Click “Create new secret key”
Copy and save your key securely (starts with sk-)
Cost considerations:

OpenAI charges per token used
This project uses GPT-4.1-mini by default (~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
A typical itinerary generation costs $0.01-0.05
Set up usage limits in your OpenAI account to control costs
Security note: Never hardcode your API key in your code. This project uses session state storage where users enter their own keys, or you can use environment variables for personal development.

2. OpenStreetMap APIs (Free, No Key Required)
Purpose: Geocoding cities and retrieving Points of Interest

Services used:

Nominatim (geocoding): Free, no API key needed
Overpass API (POI data): Free, no API key needed
Usage requirements:

Provide a valid User-Agent header with contact information
Respect rate limits (1 request per second for Nominatim)
This project includes automatic rate limiting and retry logic
Setup:

# In your code, use a descriptive User-Agent
user_agent = "trip-planner-capstone/1.0 (your-email@example.com)"
headers = {"User-Agent": user_agent}

3. Wikivoyage API (Optional, Free, No Key Required)
Purpose: Retrieval-Augmented Generation (RAG) for travel context

Setup:

Part of the Wikimedia API
No API key required
Must include proper User-Agent header
Can be disabled if you encounter 403 errors
Best practices:

Always include contact information in your User-Agent
Cache API responses to minimize requests
Handle errors gracefully (some regions may block certain IPs)
Managing API Keys in Your Project:
Option 1: User input (recommended for deployment)

# In your Streamlit sidebar
api_key = st.text_input("OpenAI API key", type="password", key="user_openai_key")
st.checkbox("Remember for this session", value=True)

Option 2: Environment variables (for local development)

import os
from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

Set the environment variable:

# Mac/Linux
export OPENAI_API_KEY="sk-your-key-here"

# Windows
set OPENAI_API_KEY=sk-your-key-here

Option 3: Secrets file (for Streamlit Cloud deployment)

#.streamlit/secrets.toml (DO NOT commit to git)
OPENAI_API_KEY = "sk-your-key-here"

# In your code
api_key = st.secrets["OPENAI_API_KEY"]

Security checklist:

Never commit API keys to version control
Add.streamlit/secrets.toml to.gitignore
Use environment variables or user input for keys
Implement usage limits and monitoring
Rotate keys if accidentally exposed