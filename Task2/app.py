from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import time
import re

from dotenv import load_dotenv
import google.generativeai as genai

# =========================================
# ENV + APP SETUP
# =========================================

# Load environment variables from .env in local dev
# (On Render, Render will inject env vars, .env is not used there)
load_dotenv()

app = Flask(__name__)

# Data file (JSON on disk – fine for this assignment)
DATA_FILE = os.environ.get("DATA_FILE", "submissions.json")

# Gemini configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash")

gemini_model = None
AI_ENABLED = False

def init_gemini():
    """
    Configure Gemini using environment variables.
    If anything fails, keep AI_DISABLED and use fallbacks.
    """
    global gemini_model, AI_ENABLED

    if not GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY not found in environment. AI will use fallback responses.")
        AI_ENABLED = False
        return

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        # Optional: tiny test call to ensure it works
        _ = gemini_model.generate_content("Health check for feedback system.")
        AI_ENABLED = True
        print(f"✅ Gemini AI initialized with model '{GEMINI_MODEL_NAME}'")
    except Exception as e:
        AI_ENABLED = False
        gemini_model = None
        print(f"❌ Failed to initialize Gemini AI. Using fallback responses instead.\n   Reason: {e}")

# =========================================
# DATA HANDLING
# =========================================

def init_data_file():
    """Ensure the data file exists and is a valid JSON list."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        return

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("DATA_FILE is not a list – resetting.")
    except Exception:
        # Repair the file if corrupted
        with open(DATA_FILE, "w") as f:
            json.dump([], f)


def get_submissions():
    """Safely load submissions from JSON file."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_submissions(submissions):
    """Safely write submissions to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(submissions, f, indent=2)

# =========================================
# AI HELPERS
# =========================================

def generate_ai_content(prompt: str) -> str | None:
    """
    Call Gemini AI with basic error handling.
    Returns plain text if successful, otherwise None.
    """
    global AI_ENABLED

    if not AI_ENABLED or gemini_model is None:
        return None

    try:
        # Basic retry-on-failure (max 2 attempts)
        for attempt in range(2):
            try:
                response = gemini_model.generate_content(prompt)
                # response.text is the usual property; fall back if absent
                text = getattr(response, "text", None)
                if not text and hasattr(response, "candidates"):
                    # very defensive: extract from first candidate
                    text = response.candidates[0].content.parts[0].text
                return text.strip() if text else None
            except Exception as e:
                print(f"⚠️ Gemini call failed (attempt {attempt+1}): {e}")
                time.sleep(0.8)
        # If we still fail, disable AI for the rest of this run to avoid spamming
        AI_ENABLED = False
        print("❌ Disabling AI for this process due to repeated failures. Using fallback.")
        return None
    except Exception as e:
        # Very last-resort safety
        print(f"❌ Unexpected AI error: {e}")
        AI_ENABLED = False
        return None


def generate_ai_responses(rating: int, review: str) -> dict:
    """
    Generate all AI responses for a review.
    Tries Gemini first; if not available or fails, uses static mock responses.
    """
    # 1) Try Gemini
    if AI_ENABLED:
        prompt = f"""
You are an AI assistant for a restaurant feedback system.

Given this {rating}-star review:

REVIEW: \"\"\"{review}\"\"\"

Generate:

1. A polite, professional response to the customer (1–2 sentences)
2. A brief summary for the restaurant manager (1 sentence)
3. 2–3 actionable suggestions for improvement or follow-up

Format your response EXACTLY as:

RESPONSE TO CUSTOMER: <text>
SUMMARY: <text>
SUGGESTIONS: <suggestion 1>, <suggestion 2>, <suggestion 3>
"""
        ai_output = generate_ai_content(prompt)

        if ai_output:
            customer_response = ""
            summary = ""
            suggestions: list[str] = []

            for line in ai_output.splitlines():
                line = line.strip()
                if line.startswith("RESPONSE TO CUSTOMER:"):
                    customer_response = line.replace("RESPONSE TO CUSTOMER:", "").strip()
                elif line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()
                elif line.startswith("SUGGESTIONS:"):
                    suggestions_text = line.replace("SUGGESTIONS:", "").strip()
                    # Split on commas but ignore empty segments
                    suggestions = [s.strip() for s in re.split(r",|\u2022|-", suggestions_text) if s.strip()]

            if customer_response and summary and suggestions:
                return {
                    "customer_response": customer_response,
                    "summary": summary,
                    "suggestions": suggestions,
                }

            print("⚠️ AI output could not be fully parsed, falling back to static responses.")

    # 2) Fallback – deterministic mock responses based on rating
    fallback_responses = {
        1: {
            "customer_response": "We sincerely apologize for your disappointing experience and will urgently review what went wrong.",
            "summary": "Critical 1-star review requiring immediate attention.",
            "suggestions": [
                "Reach out to the customer personally",
                "Review staff performance on this shift",
                "Check food and service quality controls",
            ],
        },
        2: {
            "customer_response": "Thank you for your honest feedback. We’re sorry we fell short and will work to address these issues.",
            "summary": "Mostly negative experience with clear improvement areas.",
            "suggestions": [
                "Investigate specific complaints",
                "Provide coaching or retraining where needed",
                "Offer a goodwill gesture if appropriate",
            ],
        },
        3: {
            "customer_response": "Thank you for sharing your experience. We’ll use your feedback to make improvements.",
            "summary": "Neutral or mixed review with room for improvement.",
            "suggestions": [
                "Identify key pain points mentioned",
                "Review processes related to the feedback",
                "Monitor similar feedback trends",
            ],
        },
        4: {
            "customer_response": "Thank you for the positive review! We’re glad you enjoyed your visit and hope to see you again soon.",
            "summary": "Generally positive review with minor issues.",
            "suggestions": [
                "Share praise with staff",
                "Address any small issues mentioned",
                "Encourage customer to return / leave public review",
            ],
        },
        5: {
            "customer_response": "Thank you for the amazing review! We’re thrilled you had a great experience.",
            "summary": "Excellent review with high satisfaction.",
            "suggestions": [
                "Celebrate with the team",
                "Consider featuring this as a testimonial",
                "Maintain the standards praised by the customer",
            ],
        },
    }

    return fallback_responses.get(rating, fallback_responses[3])

# =========================================
# ROUTES
# =========================================

# Initialize on import
init_data_file()
init_gemini()

@app.route("/")
def user_dashboard():
    return render_template("user.html")


@app.route("/admin")
def admin_dashboard():
    submissions = get_submissions()
    total = len(submissions)
    avg_rating = 0
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    if total > 0:
        for sub in submissions:
            rating_counts[sub["rating"]] += 1
        avg_rating = sum(s["rating"] for s in submissions) / total

    return render_template(
        "admin.html",
        submissions=submissions,
        total=total,
        avg_rating=round(avg_rating, 2) if total > 0 else 0,
        rating_counts=rating_counts,
        ai_enabled=AI_ENABLED,
    )


@app.route("/submit", methods=["POST"])
def submit_review():
    try:
        data = request.json or {}
        rating = int(data.get("rating", 3))
        review = (data.get("review") or "").strip()

        if not review:
            return jsonify({"error": "Please write a review."}), 400

        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5."}), 400

        if len(review) > 1000:
            return jsonify({"error": "Review too long (max 1000 characters)."}), 400

        ai_data = generate_ai_responses(rating, review)

        submission = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rating": rating,
            "review": review,
            "ai_response": ai_data["customer_response"],
            "ai_summary": ai_data["summary"],
            "ai_actions": ai_data["suggestions"],
        }

        submissions = get_submissions()
        submissions.append(submission)
        save_submissions(submissions)

        print(f"📝 New {rating}-star review submitted. AI_ENABLED={AI_ENABLED}")

        return jsonify(
            {
                "success": True,
                "message": "Review submitted successfully!",
                "ai_response": ai_data["customer_response"],
            }
        )

    except Exception as e:
        print(f"❌ Error in /submit: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/export")
def export_data():
    """Export all submissions as JSON."""
    submissions = get_submissions()
    return jsonify(submissions)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI FEEDBACK SYSTEM – DEVELOPMENT MODE")
    print("=" * 60)
    print(f"🤖 AI Status: {'ENABLED' if AI_ENABLED else 'DISABLED (fallback only)'}")
    print("👉 User Dashboard:   http://localhost:5000")
    print("👨‍💼 Admin Dashboard: http://localhost:5000/admin")
    print("📊 Export Data:      http://localhost:5000/export")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
