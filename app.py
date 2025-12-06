from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import google.generativeai as genai
import time

app = Flask(__name__)

# ========== CONFIGURATION ==========
GEMINI_API_KEY = "AIzaSyC58rpy2LnyzM8y43L8CghTQZcyA9evHH8"  # ← REPLACE WITH YOUR KEY
DATA_FILE = 'submissions.json'

# Initialize Gemini AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    AI_ENABLED = True
    print("✅ Gemini AI initialized successfully")
except:
    AI_ENABLED = False
    print("⚠️ Gemini AI not available, using fallback")

# ========== DATA HANDLING ==========
def init_data_file():
    """Initialize or repair the data file"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Not a list")
        except:
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)

def get_submissions():
    """Safely get submissions from file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_submissions(submissions):
    """Safely save submissions to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)

# ========== AI FUNCTIONS ==========
def generate_ai_content(prompt):
    """Generate content using Gemini AI with fallback"""
    if not AI_ENABLED:
        return None
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def generate_ai_responses(rating, review):
    """Generate all AI responses for a review"""
    
    # Try Gemini AI first
    if AI_ENABLED:
        prompt = f"""
        As a restaurant feedback system, generate responses for this {rating}-star review:
        
        REVIEW: "{review}"
        
        Generate:
        1. A polite, professional response to the customer (1-2 sentences)
        2. A brief summary for the restaurant manager (1 sentence)
        3. 2-3 actionable suggestions for improvement
        
        Format your response as:
        RESPONSE TO CUSTOMER: [your response here]
        SUMMARY: [your summary here]
        SUGGESTIONS: [suggestion 1], [suggestion 2], [suggestion 3]
        """
        
        ai_output = generate_ai_content(prompt)
        
        if ai_output:
            # Parse the response
            lines = ai_output.split('\n')
            customer_response = ""
            summary = ""
            suggestions = []
            
            for line in lines:
                if line.startswith("RESPONSE TO CUSTOMER:"):
                    customer_response = line.replace("RESPONSE TO CUSTOMER:", "").strip()
                elif line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()
                elif line.startswith("SUGGESTIONS:"):
                    suggestions_text = line.replace("SUGGESTIONS:", "").strip()
                    suggestions = [s.strip() for s in suggestions_text.split(',')]
            
            if customer_response and summary and suggestions:
                return {
                    'customer_response': customer_response,
                    'summary': summary,
                    'suggestions': suggestions
                }
    
    # Fallback responses
    responses = {
        1: {
            'customer_response': "We sincerely apologize for your disappointing experience. We take your feedback seriously and will address these issues immediately.",
            'summary': "Critical 1-star review requiring urgent attention.",
            'suggestions': ["Immediate customer follow-up", "Staff retraining", "Quality control review"]
        },
        2: {
            'customer_response': "Thank you for your honest feedback. We're sorry we fell short of your expectations and will work to improve.",
            'summary': "Dissatisfied customer with specific complaints.",
            'suggestions': ["Review service protocols", "Check product quality", "Consider compensation"]
        },
        3: {
            'customer_response': "Thank you for your feedback. We appreciate you taking the time to share your experience with us.",
            'summary': "Average experience with room for improvement.",
            'suggestions': ["Identify improvement areas", "Monitor similar feedback", "Standard check"]
        },
        4: {
            'customer_response': "Thank you for your positive review! We're delighted you enjoyed your experience and hope to see you again soon!",
            'summary': "Positive review with high satisfaction.",
            'suggestions': ["Share with team for motivation", "Reinforce positive practices", "Thank the staff involved"]
        },
        5: {
            'customer_response': "Wow! Thank you for the amazing review! We're thrilled you loved everything and can't wait to welcome you back!",
            'summary': "Excellent review with high praise.",
            'suggestions': ["Feature as testimonial", "Reward exceptional staff", "Share on social media"]
        }
    }
    
    return responses.get(rating, responses[3])

# ========== ROUTES ==========
init_data_file()

@app.route('/')
def user_dashboard():
    return render_template('user.html')

@app.route('/admin')
def admin_dashboard():
    submissions = get_submissions()
    
    # Calculate statistics
    total = len(submissions)
    avg_rating = 0
    rating_counts = {1:0, 2:0, 3:0, 4:0, 5:0}
    
    if total > 0:
        for sub in submissions:
            rating_counts[sub['rating']] += 1
        avg_rating = sum(s['rating'] for s in submissions) / total
    
    return render_template('admin.html', 
                         submissions=submissions,
                         total=total,
                         avg_rating=round(avg_rating, 2),
                         rating_counts=rating_counts)

@app.route('/submit', methods=['POST'])
def submit_review():
    try:
        data = request.json
        rating = int(data.get('rating', 3))
        review = data.get('review', '').strip()
        
        if not review:
            return jsonify({'error': 'Please write a review'}), 400
        
        if len(review) > 1000:
            return jsonify({'error': 'Review too long (max 1000 characters)'}), 400
        
        # Generate AI responses
        ai_data = generate_ai_responses(rating, review)
        
        # Create submission
        submission = {
            'id': datetime.now().strftime("%Y%m%d%H%M%S"),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rating': rating,
            'review': review,
            'ai_response': ai_data['customer_response'],
            'ai_summary': ai_data['summary'],
            'ai_actions': ai_data['suggestions']
        }
        
        # Save to file
        submissions = get_submissions()
        submissions.append(submission)
        save_submissions(submissions)
        
        print(f"📝 New {rating}-star review submitted")
        if AI_ENABLED:
            print(f"🤖 AI Response: {ai_data['summary'][:50]}...")
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully!',
            'ai_response': ai_data['customer_response']
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export')
def export_data():
    """Export all submissions as JSON"""
    submissions = get_submissions()
    return jsonify(submissions)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ENHANCED AI FEEDBACK SYSTEM")
    print("=" * 60)
    print(f"🤖 AI Status: {'ENABLED' if AI_ENABLED else 'DISABLED (using fallback)'}")
    print("👉 User Dashboard: http://localhost:5000")
    print("👨‍💼 Admin Dashboard: http://localhost:5000/admin")
    print("📊 Export Data: http://localhost:5000/export")
    print("=" * 60)
    app.run(debug=True, port=5000)