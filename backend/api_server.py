from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from jira import JIRA
from datetime import datetime
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
load_dotenv()

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_URL = os.getenv("JIRA_URL")
PROJECT_KEY = os.getenv("PROJECT_KEY", "OPS")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize OpenRouter AI
try:
    # Test the API key with a simple request
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    test_response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=test_data,
        timeout=10
    )
    
    if test_response.status_code == 200:
        AI_STATUS = "✅ AI Integration Active"
    else:
        AI_STATUS = f"❌ AI Integration Failed: HTTP {test_response.status_code}"
        
except Exception as e:
    AI_STATUS = f"❌ AI Integration Failed: {e}"

# Connect to Jira
try:
    jira = JIRA(
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        options={"server": JIRA_URL}
    )
    # Test connection by getting project info
    project = jira.project(PROJECT_KEY)
    JIRA_STATUS = f"✅ Connected to JIRA successfully. Project: {project.name}"
    print(f"✅ JIRA Connected - Project: {project.name}, Key: {PROJECT_KEY}")
except Exception as e:
    JIRA_STATUS = f"❌ Failed to connect to JIRA: {e}"
    jira = None
    print(f"❌ JIRA Connection Failed: {e}")
    print(f"   JIRA_URL: {JIRA_URL}")
    print(f"   PROJECT_KEY: {PROJECT_KEY}")
    print(f"   JIRA_EMAIL: {JIRA_EMAIL}")
    print(f"   JIRA_API_TOKEN: {'*' * 10 if JIRA_API_TOKEN else 'NOT SET'}")

# Store errors and tickets in memory for demo
ERRORS = []
TICKETS = []

CORS(app)

# Technical team mapping based on error patterns
TEAM_MAPPING = {
    'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'connection', 'timeout', 'deadlock'],
    'frontend': ['javascript', 'react', 'angular', 'vue', 'css', 'html', 'dom', 'browser'],
    'backend': ['python', 'java', 'nodejs', 'php', 'api', 'server', 'endpoint'],
    'devops': ['docker', 'kubernetes', 'aws', 'azure', 'deployment', 'infrastructure'],
    'security': ['authentication', 'authorization', 'ssl', 'encryption', 'firewall'],
    'network': ['connection', 'timeout', 'dns', 'http', 'https', 'proxy']
}

# Developer list for ticket assignment
DEVELOPERS = [
    {"name": "yaswini", "email": "yaswinirayapati@gmail.com", "role": "Frontend developer", "accountId": "712020:a7e81699-32ef-46df-8b47-eaf1ed4c5a5b"},
    {"name": "Harshitha", "email": "harshithabade91@gmail.com", "role": "Backend developer", "accountId": "712020:b4a29ac2-9ab7-42ac-b119-a19725f989da"},
    {"name": "Sneha", "email": "lathach783@gmail.com", "role": "Database developer", "accountId": "712020:4217b8b2-2525-451f-9814-2a63460c1ba9"},
    {"name": "jaswanth", "email": "2100030129cse@gmail.com", "role": "Ai-ML developer", "accountId": "712020:00773563-a85f-4d17-97cd-eca50205520a"},
    {"name": "vena", "email": "veenagona123@gmail.com", "role": "Tester", "accountId": "712020:4f70d574-2497-45fa-8a4f-1909ceca4a08"},
]

# Efficient mapping from error/bug type to developer role
ROLE_KEYWORDS = {
    "Frontend developer": ["frontend", "javascript", "react", "angular", "vue", "css", "html", "dom", "browser", "ui", "client"],
    "Backend developer": ["backend", "python", "java", "nodejs", "php", "api", "server", "endpoint", "controller", "service", "route", "middleware"],
    "Ai-ML developer": ["ai", "ml", "machine learning", "model", "training", "inference", "neural", "deep learning", "artificial intelligence"],
    "Database developer": ["database", "sql", "mysql", "postgresql", "mongodb", "query", "table", "index", "db_", "database_", "deadlock"],
    "Tester": ["test", "qa", "quality", "assertion", "verification", "validation", "tester", "testcase", "test case"]
}

# Map error message to developer role
def map_error_to_role(error_message):
    error_lower = error_message.lower()
    best_role = None
    best_score = 0
    for role, keywords in ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in error_lower)
        if score > best_score:
            best_score = score
            best_role = role
    return best_role if best_score > 0 else None

# Find developer by role
def get_developer_by_role(role):
    for dev in DEVELOPERS:
        if dev["role"].lower() == role.lower():
            return dev
    return None

def analyze_error_type(error_message):
    """Analyze error message to determine error type and severity"""
    error_lower = error_message.lower()
    
    # Determine error type
    if any(word in error_lower for word in ['timeout', 'connection refused']):
        error_type = "Connection Error"
        severity = "Medium"
    elif any(word in error_lower for word in ['null pointer', 'undefined', 'index out of range']):
        error_type = "Runtime Error"
        severity = "High"
    elif any(word in error_lower for word in ['authentication', 'unauthorized', 'forbidden']):
        error_type = "Security Error"
        severity = "Critical"
    elif any(word in error_lower for word in ['database', 'sql', 'query']):
        error_type = "Database Error"
        severity = "High"
    else:
        error_type = "General Error"
        severity = "Medium"
    
    return error_type, severity

def assign_team(error_message):
    """Assign developer role based on error content"""
    role = map_error_to_role(error_message)
    if role:
        return role
    return "system"

def get_ai_analysis(error_message, error_type):
    """Get detailed AI analysis and suggestions using OpenRouter API"""
    prompt = f"""
    Analyze this error log entry and provide detailed technical analysis:
    
    Error: {error_message}
    Error Type: {error_type}
    
    Please provide:
    1. Root Cause Analysis (2-3 sentences)
    2. Immediate Fix Steps (numbered list)
    3. Prevention Measures (2-3 points)
    4. Technical Impact Assessment
    5. Recommended Priority Level
    
    Format as a structured technical report.
    """
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "AI analysis failed: Invalid response format"
        else:
            error_detail = response.text if response.text else f"HTTP {response.status_code}"
            return f"AI analysis failed: {error_detail}"
            
    except requests.exceptions.Timeout:
        return "AI analysis failed: Request timeout"
    except requests.exceptions.RequestException as e:
        return f"AI analysis failed: Network error - {str(e)}"
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

def create_detailed_jira_ticket(error_message, error_type, severity, assigned_team, ai_analysis):
    """Create comprehensive JIRA ticket with all details and assign to developer"""
    if not jira:
        print("❌ JIRA not connected, cannot create ticket")
        return None
    try:
        # Map severity to JIRA priority
        priority_mapping = {
            "Critical": "Highest",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low"
        }
        jira_priority = priority_mapping.get(severity, "Medium")
        # Clean up team name for JIRA
        clean_team = assigned_team.replace(' ', '-').replace('_', '-')
        # Find assignee accountId
        assignee_account_id = None
        print(f"🔍 Debug: assigned_team = '{assigned_team}'")
        if assigned_team != "system":
            dev = get_developer_by_role(assigned_team)
            if dev:
                assignee_account_id = dev.get("accountId")
                print(f"🔍 Debug: Found developer {dev['name']} with accountId {assignee_account_id}")
            else:
                print(f"🔍 Debug: No developer found for role '{assigned_team}'")
        else:
            print(f"🔍 Debug: Team is 'system', no assignment needed")
        issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': f"🚨 {error_type}: {error_message[:50]}...",
            'description': f"""
# Auto-Detected Log Error Analysis

## Error Details
- **Error Message**: {error_message}
- **Error Type**: {error_type}
- **Severity**: {severity}
- **Detected At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Assigned Team**: {assigned_team}

## AI Analysis & Recommendations
{ai_analysis}

## Technical Context
- **Source**: Log File Analysis
- **Detection Method**: Automated Error Detection System
- **Priority**: {severity}

---
*This ticket was automatically generated by the Bug Tester AI system.*
            """,
            'issuetype': {'name': 'Bug'},
            'priority': {'name': jira_priority},
            'labels': [error_type.replace(' ', '-'), clean_team, 'auto-generated']
        }
        if assignee_account_id:
            try:
                print(f"🔧 Attempting to assign ticket to accountId: {assignee_account_id}")
                issue_dict['assignee'] = {"id": assignee_account_id}
                print(f"🔧 Set assignee to accountId: {assignee_account_id}")
            except Exception as assign_error:
                print(f"⚠️ Could not assign to {assignee_account_id}: {assign_error}")
                # If assignment fails, create ticket without assignee
                pass
        print(f"🔧 Creating JIRA ticket for {error_type} - Team: {assigned_team} - Assignee: {assignee_account_id or 'system'}")
        new_issue = jira.create_issue(fields=issue_dict)
        ticket_url = f"{JIRA_URL}/browse/{new_issue.key}"
        print(f"✅ JIRA ticket created: {ticket_url}")
        return ticket_url
    except Exception as e:
        print(f"❌ Failed to create JIRA ticket: {e}")
        print(f"   Project Key: {PROJECT_KEY}")
        print(f"   Error Type: {error_type}")
        print(f"   Team: {assigned_team}")
        return None

@app.route("/api/test-team-assignment", methods=["POST"])
def test_team_assignment():
    """Test team assignment with sample error messages"""
    data = request.get_json()
    test_errors = data.get("errors", [
        "Database connection timeout error",
        "JavaScript undefined variable error", 
        "Python API endpoint failed",
        "Docker container deployment failed",
        "SSL certificate authentication error",
        "Network connection refused"
    ])
    
    results = []
    for error in test_errors:
        error_type, severity = analyze_error_type(error)
        assigned_team = assign_team(error)
        dev = get_developer_by_role(assigned_team) if assigned_team != "system" else None
        results.append({
            "error": error,
            "type": error_type,
            "severity": severity,
            "team": assigned_team,
            "developer": dev["name"] if dev else "system",
            "email": dev["email"] if dev else "system"
        })
    
    return jsonify({
        "success": True,
        "results": results
    })

@app.route("/api/test-developer-mapping", methods=["GET"])
def test_developer_mapping():
    """Test the developer mapping functionality"""
    test_errors = [
        "Database connection timeout error",
        "JavaScript undefined variable error", 
        "Python API endpoint failed",
        "Machine learning model training failed",
        "Test case assertion failed"
    ]
    
    results = []
    for error in test_errors:
        role = map_error_to_role(error)
        dev = get_developer_by_role(role) if role else None
        results.append({
            "error": error,
            "mapped_role": role,
            "developer_name": dev["name"] if dev else "system",
            "developer_email": dev["email"] if dev else "system"
        })
    
    return jsonify({
        "success": True,
        "developers": DEVELOPERS,
        "role_keywords": ROLE_KEYWORDS,
        "test_results": results
    })

@app.route("/api/test-jira", methods=["GET"])
def test_jira():
    """Test JIRA connection and create a simple test ticket"""
    if not jira:
        return jsonify({
            "success": False,
            "error": "JIRA not connected",
            "status": JIRA_STATUS
        }), 500
    
    try:
        # Test basic ticket creation
        test_issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': '🧪 Test Ticket - Bug Tester AI',
            'description': f"""
# Test Ticket

This is a test ticket created by the Bug Tester AI system.

**Test Details:**
- Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Project: {PROJECT_KEY}
- Purpose: Testing JIRA integration

---
*This is a test ticket and can be deleted.*
            """,
            'issuetype': {'name': 'Bug'},
            'priority': {'name': 'Low'},
            'labels': ['test', 'auto-generated']
        }
        
        new_issue = jira.create_issue(fields=test_issue_dict)
        ticket_url = f"{JIRA_URL}/browse/{new_issue.key}"
        
        return jsonify({
            "success": True,
            "message": "Test ticket created successfully",
            "ticket_url": ticket_url,
            "ticket_key": new_issue.key,
            "status": JIRA_STATUS
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": JIRA_STATUS,
            "project_key": PROJECT_KEY
        }), 500

@app.route("/api/status")
def status():
    return jsonify({
        "jira_status": JIRA_STATUS,
        "ai_status": AI_STATUS,
        "server": "✅ Backend API Running",
        "project_key": PROJECT_KEY,
        "jira_connected": jira is not None
    })

@app.route("/api/errors")
def errors():
    # Read last 10 errors from log file
    errors_found = []
    if LOG_FILE_PATH and os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as f:
            for line in f:
                if any(k in line.lower() for k in ["error", "exception", "failed"]):
                    errors_found.append(line.strip())
    return jsonify({"errors": errors_found[-10:]})

@app.route("/api/tickets")
def tickets():
    # For demo, return last 10 tickets
    return jsonify({"tickets": TICKETS[-10:]})

@app.route("/api/create_ticket", methods=["POST"])
def create_ticket():
    # This endpoint can be called from frontend to create a ticket
    import flask
    data = flask.request.get_json()
    error_message = data.get("error_message", "Unknown error")
    issue_dict = {
        'project': {'key': PROJECT_KEY},
        'summary': f"⚠️ Auto-Detected Log Error: {error_message[:60]}",
        'description': f"Error detected in logs at {datetime.now()}:\n\n{error_message}",
        'issuetype': {'name': 'Bug'},
    }
    try:
        new_issue = jira.create_issue(fields=issue_dict)
        ticket_url = f"{JIRA_URL}/browse/{new_issue.key}"
        TICKETS.append({"url": ticket_url, "summary": error_message})
        return jsonify({"success": True, "url": ticket_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        # Accept file upload
        if 'logFile' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        file = request.files['logFile']
        content = file.read().decode('utf-8')
        # Enhanced test case detection with context
        test_cases = []
        passed_tests = []
        failed_tests = []
        for line_num, line in enumerate(content.splitlines(), 1):
            line_lower = line.lower()
            # Detect passed test cases
            if any(k in line_lower for k in ["passed", "success", "completed successfully", "test passed", "✓", "✅"]):
                passed_tests.append({
                    'line_number': line_num,
                    'content': line.strip(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'PASSED'
                })
                test_cases.append({
                    'line_number': line_num,
                    'content': line.strip(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'PASSED'
                })
            # Detect failed test cases and errors
            elif any(k in line_lower for k in ["error", "exception", "failed", "timeout", "connection refused", "test failed", "✗", "❌", "fail"]):
                failed_tests.append({
                    'line_number': line_num,
                    'content': line.strip(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'FAILED'
                })
                test_cases.append({
                    'line_number': line_num,
                    'content': line.strip(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'FAILED'
                })
        total_tests = len(test_cases)
        total_passed = len(passed_tests)
        total_failed = len(failed_tests)
        if total_tests == 0:
            return jsonify({
                "success": False, 
                "message": "✅ No test cases detected in the log file!",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "suggestion": "The log file doesn't contain recognizable test case results.",
                "ticket": None
            })
        # Process failed test cases with detailed analysis
        detailed_analysis = []
        tickets_created = []
        print(f"🔍 Processing {total_tests} test cases ({total_passed} passed, {total_failed} failed)...")
        # Only process failed tests for detailed analysis and JIRA tickets
        for test_data in failed_tests[:3]:  # Limit to first 3 failed tests to avoid spam
            error_message = test_data['content']
            error_type, severity = analyze_error_type(error_message)
            assigned_team = assign_team(error_message)
            ai_analysis = get_ai_analysis(error_message, error_type)
            print(f"📋 Failed Test: {error_message[:50]}...")
            print(f"   Type: {error_type}, Severity: {severity}, Team: {assigned_team}")
            # Create detailed JIRA ticket for failed tests
            ticket_url = create_detailed_jira_ticket(
                error_message, error_type, severity, assigned_team, ai_analysis
            )
            detailed_analysis.append({
                'error': error_message,
                'type': error_type,
                'severity': severity,
                'team': assigned_team,
                'ai_analysis': ai_analysis,
                'ticket_url': ticket_url,
                'test_status': 'FAILED'
            })
            if ticket_url:
                tickets_created.append(ticket_url)
                TICKETS.append({"url": ticket_url, "summary": error_message})
                print(f"✅ Ticket created successfully")
            else:
                print(f"❌ Failed to create ticket")
        # Generate comprehensive summary
        summary = f"""
🔍 **Log Analysis Complete**

📊 **Summary:**
- Total Test Cases: {total_tests}
- Passed Tests: {total_passed}
- Failed Tests: {total_failed}
- JIRA Tickets Created: {len(tickets_created)}

🎯 **Key Issues:**
{chr(10).join([f"- {analysis['type']} (Severity: {analysis['severity']}) - Assigned to {analysis['team']}" for analysis in detailed_analysis])}

⚠️ **Immediate Actions Required:**
- Review all created JIRA tickets
- Assign team members based on error types
- Implement suggested fixes from AI analysis
    """
        return jsonify({
            "success": True,
            "summary": summary,
            "detailed_analysis": detailed_analysis,
            "tickets_created": tickets_created,
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "processed_errors": len(detailed_analysis)
        })
    except Exception as e:
        import traceback
        print("Exception in /api/analyze:", e)
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
