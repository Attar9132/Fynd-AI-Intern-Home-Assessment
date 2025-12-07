# Fynd AI Intern – Home Assessment

This repository contains my submission for the **Fynd AI Intern Assessment**, covering both:

- **Task 1:** Prompt engineering and rating prediction  
- **Task 2:** A fully deployed two-dashboard AI feedback system  

---

## 📌 Contents

---

## **Task 1 — Rating Prediction via Prompting**
📁 Folder: `/Task1`

I implemented and evaluated **three different prompting strategies**:

1. **Direct Classification Prompt**  
2. **Few-Shot Example Prompt**  
3. **Rubric-Based Prompt**

Using a sample of **200 Yelp reviews**, I computed:

- Accuracy  
- JSON validity rate  
- Mean Absolute Error (MAE)  
- Reliability & consistency  

Included files:

- `Task_1.ipynb` — complete notebook  
- `task1_results.csv` — predictions  
- `task1_metrics.csv` — evaluation metrics  
- Analysis & comparison  

---

## **Task 2 — Two-Dashboard AI Feedback System**
📁 Folder: `/Task2`

A complete **Flask-based AI application** with two separate dashboards.

---

### **A. User Dashboard (`/`)**
Users can:

- Select a star rating  
- Write a review  
- Submit feedback  

On submission, the system generates:

- 🤖 **AI-created customer response**

---

### **B. Admin Dashboard (`/admin`)**

Admin panel displays:

- ⭐ User rating  
- 📝 User review  
- 🤖 AI-generated summary  
- 💡 AI-suggested next actions  
- 📊 Basic analytics 

Both dashboards share the same data backend.

---

### **Key Features**

- Real-time AI responses using **Google Gemini API**  
- Review summarization  
- Actionable recommendations  
- Secure JSON-based storage  
- Bootstrap UI + Chart.js analytics  
- Deployment on Render with gunicorn  
- **No hardcoded API keys** — environment variables used  

---

## 🚀 Live Deployment

| Dashboard | URL |
|----------|-----|
| 🌐 **User Dashboard** | https://feedback-system-xwew.onrender.com |
| 🔧 **Admin Dashboard** | https://feedback-system-xwew.onrender.com/admin |

---

## 🛠 Technologies Used

### **Task 1**
- Python  
- Pandas  
- Matplotlib  
- Custom Mock LLM simulation  
- Prompt engineering  

### **Task 2**
- Flask  
- Google Gemini API  
- HTML5, Bootstrap 5  
- JavaScript, Chart.js  
- Render.com deployment  
- Environment-variable security  

---

## ✅ Key Achievements

- Created and compared **three prompting strategies**  
- Built a working **AI-powered feedback system**  
- Implemented **secure API key handling**  
- Fully deployed both dashboards  
- Clean UI + useful analytics  
- End-to-end functionality with real AI integration  

---

## 👨‍💻 Author

**Attar Singh Kalsi**  
📧 **attarkalsi@gmail.com**  
Applying for: **Fynd AI Intern — AI/ML Track**

---

