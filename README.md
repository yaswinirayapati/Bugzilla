
# 🤖 BUG TESTING

## 📌 Problem Statement

In many software applications, errors and failures are recorded in **log files**. However, checking these logs manually and creating a **JIRA ticket** every time an error occurs can be time-consuming and repetitive.

This project aims to **automate** this process so that:

- Errors are **automatically detected** from log files.
- A **JIRA ticket is created** when an issue is found.
- A simple **AI agent** tries to understand the error and suggest a possible solution.

---

## 🎯 Objectives

- Read and monitor application logs automatically.
- Identify any error or failure messages.
- Create a JIRA ticket with the error details.
- Use a simple AI model to suggest how to fix the error.

---

## 🛠️ How It Works (Simplified)

The application writes logs during runtime.
A Python script continuously reads the log file and detects error keywords.
When an error is found, it calls the JIRA API to automatically create a ticket.

---

## 🔧 Technologies Used

| Purpose             | Tool / Language             |
|---------------------|-----------------------------|
| Log reading         | Python                      |
| Error detection     | Python (simple keyword check)|
| JIRA integration    | Python + JIRA API            |
| AI suggestions      | ChatGPT API or basic model   |
| Environment setup   | Python, pip                  |

---

Expected Output:
Logs are constantly monitored.
When an error is detected:
A JIRA ticket is created automatically.
The AI agent analyzes and posts a resolution (or takes a corrective action).
Status is tracked until issue is resolved.
Final output includes:
A closed JIRA ticket with proper logs
AI-assisted resolution steps
Improved MTTR metrics
