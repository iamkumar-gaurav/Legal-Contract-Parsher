# 🧠 Legal Document Parser using LLMs

An experimental project to explore how Large Language Models (LLMs) can be used to reduce manual effort in contract review by extracting and structuring actionable insights.

---

## 🚀 Problem Statement

Legal teams spend significant time manually reviewing contracts to identify:

- Key obligations  
- Risks and clauses  
- Actionable items  

This process is:
- Time-consuming  
- Repetitive  
- Hard to scale  

---

## 💡 Solution

This project builds a prototype system that:

👉 Parses unstructured legal documents  
👉 Extracts actionable items using LLMs  
👉 Structures them into an Excel format  
👉 Assigns priority to each item  

---

## ⚙️ How It Works

### 1. Input
- Legal contracts (PDF / text documents)

### 2. Processing
- LLM analyzes document
- Identifies:
  - Obligations
  - Deadlines
  - Key clauses
- Applies basic prioritization logic

### 3. Output
- Structured Excel file containing:
  - Actionable item
  - Description
  - Priority (High / Medium / Low)
  - Relevant clause/context

---

## 📊 Example Output

| Action Item | Description | Priority | Clause |
|------------|------------|----------|--------|
| Payment Obligation | Vendor must pay within 30 days | High | Section 4.2 |
| Data Protection | Must comply with GDPR | High | Section 7.1 |

---

## 🎯 Objectives

- Reduce manual contract review effort  
- Improve turnaround time  
- Bring structure to unstructured legal data  
- Enable better tracking and decision-making  

---

## 🔍 Key Insight

> The value of LLMs is not just in generating text —  
> it’s in integrating them into workflows that save time.

---

## 🛠️ Tech Stack

- Python  
- LLM API (OpenAI / Claude / etc.)  
- Pandas (for structuring data)  
- Excel export  

---

## ⚠️ Current Limitations

- Prototype-level accuracy  
- Depends on prompt quality  
- Limited handling of very large documents  
- Basic prioritization logic  

---

## 🔮 Future Improvements

- Improved prompt engineering  
- Better prioritization using rules + ML  
- Integration with legal workflows/tools  
- UI for uploading and reviewing documents  
- Support for multiple contract types  

---

## 📽️ Demo

Check the LinkedIn post/video for a walkthrough of the prototype.

---

## 🤝 Contribution

This is an experimental project — feedback and ideas are welcome!

---

## 📌 Author

Kumar Gaurav  
🔗 LinkedIn: https://www.linkedin.com/in/iamkumar-gaurav/  
🔗 GitHub: https://github.com/iamkumar-gaurav  

---

## ⭐ If you found this useful

Give it a star ⭐ and share your thoughts!
