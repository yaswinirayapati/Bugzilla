from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from jira import JIRA
from datetime import datetime
from flask_cors import CORS
import requests
import re
from openai import OpenAI
import json

app = Flask(__name__)

# Load environment variables safely
try:
    load_dotenv()
    print("✅ Environment variables loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load .env file: {e}")
    print("Continuing with system environment variables...")

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_URL = os.getenv("JIRA_URL")
PROJECT_KEY = os.getenv("PROJECT_KEY", "OPS")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "")

# Initialize OpenRouter AI client
client = None
if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        # Test the API key with a simple request
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_SITE_NAME,
            },
            extra_body={},
            model="qwen/qwen3-4b:free",
            messages=[
                {"role": "user", "content": "Hello"}
            ]
        )
        if completion and hasattr(completion, "choices") and len(completion.choices) > 0:
            AI_STATUS = "✅ AI Integration Active (Qwen)"
        else:
            AI_STATUS = "❌ AI Integration Failed: No response from Qwen"
    except Exception as e:
        AI_STATUS = f"❌ AI Integration Failed: {e}"
        client = None
else:
    AI_STATUS = "❌ AI Integration Failed: OpenRouter API key not configured"
    client = None

# Connect to Jira
try:
    jira = JIRA(
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        options={"server": JIRA_URL}
    )
    
    # Try to get project info, if it fails, try to create it
    try:
        project = jira.project(PROJECT_KEY)
        JIRA_STATUS = f"✅ Connected to JIRA successfully. Project: {project.name}"
        print(f"✅ JIRA Connected - Project: {project.name}, Key: {PROJECT_KEY}")
    except Exception as project_error:
        if "No project could be found with key" in str(project_error):
            print(f"⚠️ Project '{PROJECT_KEY}' not found. Creating it...")
            try:
                # Try to create the project
                project_data = {
                    'key': PROJECT_KEY,
                    'name': 'Bug Tracker',
                    'projectTypeKey': 'software',
                    'projectTemplateKey': 'com.pyxis.greenhopper.jira:gh-simplified-agility-kanban',
                    'lead': JIRA_EMAIL
                }
                project = jira.create_project(project_data)
                JIRA_STATUS = f"✅ Created and connected to JIRA project: {project.name}"
                print(f"✅ JIRA Project Created - Project: {project.name}, Key: {PROJECT_KEY}")
            except Exception as create_error:
                JIRA_STATUS = f"❌ Failed to create JIRA project: {create_error}"
                jira = None
                print(f"❌ JIRA Project Creation Failed: {create_error}")
        else:
            raise project_error
            
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

# Rate limiting for AI requests
LAST_AI_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 60  # 60 seconds between requests for free tier

# CORS Configuration from environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization,X-Requested-With").split(",")
CORS_EXPOSE_HEADERS = os.getenv("CORS_EXPOSE_HEADERS", "").split(",") if os.getenv("CORS_EXPOSE_HEADERS") else []
CORS_SUPPORTS_CREDENTIALS = os.getenv("CORS_SUPPORTS_CREDENTIALS", "false").lower() == "true"
CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "3600"))

# Initialize CORS with environment-based configuration
CORS(app, 
     origins=CORS_ORIGINS,
     methods=CORS_METHODS,
     allow_headers=CORS_ALLOW_HEADERS,
     expose_headers=CORS_EXPOSE_HEADERS,
     supports_credentials=CORS_SUPPORTS_CREDENTIALS,
     max_age=CORS_MAX_AGE)

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

import time

def get_ai_analysis(error_message, error_type):
    """Get detailed AI analysis and suggestions using Qwen model via OpenRouter API"""
    global LAST_AI_REQUEST_TIME
    
    # Check if enough time has passed since last request
    current_time = time.time()
    time_since_last = current_time - LAST_AI_REQUEST_TIME
    
    if time_since_last < MIN_REQUEST_INTERVAL:
        # Use fallback analysis if rate limited
        return get_fallback_analysis(error_message, error_type)
    
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
        # Update last request time
        LAST_AI_REQUEST_TIME = current_time
        
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_SITE_NAME,
            },
            extra_body={},
            model="qwen/qwen3-4b:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        if completion and hasattr(completion, "choices") and len(completion.choices) > 0:
            return completion.choices[0].message.content.strip()
        else:
            return "AI analysis failed: Invalid response format"
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate limit" in error_str.lower():
            # Provide fallback analysis when rate limited
            return get_fallback_analysis(error_message, error_type)
        else:
            return f"AI analysis failed: {error_str}"

def get_fallback_analysis(error_message, error_type):
    """Provide basic analysis when AI is rate limited"""
    error_lower = error_message.lower()
    
    # Basic analysis based on error type
    if "connection" in error_lower or "timeout" in error_lower:
        return f"""
**Root Cause Analysis**: Network connectivity issue or service unavailability causing connection failures.

**Immediate Fix Steps**:
1. Check network connectivity and firewall settings
2. Verify service endpoints are accessible
3. Review timeout configurations
4. Test with different network conditions

**Prevention Measures**:
- Implement connection pooling
- Add retry mechanisms with exponential backoff
- Monitor network health and latency

**Technical Impact**: Service degradation and potential user experience issues.

**Recommended Priority**: Medium
        """
    elif "database" in error_lower or "sql" in error_lower:
        return f"""
**Root Cause Analysis**: Database connection or query execution failure.

**Immediate Fix Steps**:
1. Check database server status and connectivity
2. Review SQL query syntax and performance
3. Verify database credentials and permissions
4. Check for deadlocks or resource contention

**Prevention Measures**:
- Implement proper connection pooling
- Add query timeout and retry logic
- Regular database maintenance and monitoring

**Technical Impact**: Data access issues and potential data loss.

**Recommended Priority**: High
        """
    elif "authentication" in error_lower or "unauthorized" in error_lower:
        return f"""
**Root Cause Analysis**: Authentication or authorization failure.

**Immediate Fix Steps**:
1. Verify user credentials and permissions
2. Check authentication service status
3. Review security token validity
4. Validate access control policies

**Prevention Measures**:
- Implement proper session management
- Add multi-factor authentication
- Regular security audits and monitoring

**Technical Impact**: Security vulnerability and access control issues.

**Recommended Priority**: Critical
        """
    else:
        return f"""
**Root Cause Analysis**: General system error requiring investigation.

**Immediate Fix Steps**:
1. Review error logs for additional context
2. Check system resources and performance
3. Verify application configuration
4. Test in different environments

**Prevention Measures**:
- Implement comprehensive error handling
- Add monitoring and alerting systems
- Regular system health checks

**Technical Impact**: Potential service disruption and user impact.

**Recommended Priority**: Medium
        """

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

@app.route("/")
def home():
    return "Welcome to the Bugzilla-F API! Try /api/status for health check."

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
        "jira_connected": jira is not None,
        "cors_config": {
            "origins": CORS_ORIGINS,
            "methods": CORS_METHODS,
            "allow_headers": CORS_ALLOW_HEADERS,
            "expose_headers": CORS_EXPOSE_HEADERS,
            "supports_credentials": CORS_SUPPORTS_CREDENTIALS,
            "max_age": CORS_MAX_AGE
        }
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
        # Process only failed test cases for detailed analysis
        detailed_analysis = []
        tickets_created = []
        max_tickets_to_create = 5  # Configurable limit to prevent spam
        tickets_to_process = min(len(failed_tests), max_tickets_to_create)
        
        print(f"🔍 Processing {total_tests} test cases ({total_passed} passed, {total_failed} failed)...")
        print(f"📋 Creating tickets for first {tickets_to_process} failed tests (limit: {max_tickets_to_create})")
        
        # Process ONLY failed test cases for detailed analysis
        failed_count = 0  # Track how many failed tests we've processed for tickets
        
        for test_data in failed_tests:
            error_message = test_data['content']
            
            # Analyze failed tests and create tickets
            error_type, severity = analyze_error_type(error_message)
            assigned_team = assign_team(error_message)
            ai_analysis = get_ai_analysis(error_message, error_type)
            print(f"📋 Failed Test: {error_message[:50]}...")
            print(f"   Type: {error_type}, Severity: {severity}, Team: {assigned_team}")
            
            # Only create tickets for the first few failed tests (to prevent spam)
            ticket_url = None
            if failed_count < tickets_to_process:
                print(f"🔧 Attempting to create JIRA ticket for failed test #{failed_count + 1}")
                print(f"   JIRA Status: {JIRA_STATUS}")
                print(f"   Project Key: {PROJECT_KEY}")
                
                ticket_url = create_detailed_jira_ticket(
                    error_message, error_type, severity, assigned_team, ai_analysis
                )
                if ticket_url:
                    tickets_created.append(ticket_url)
                    TICKETS.append({"url": ticket_url, "summary": error_message})
                    print(f"✅ Ticket created successfully: {ticket_url}")
                else:
                    print(f"❌ Failed to create ticket - JIRA connection issue")
                failed_count += 1
            else:
                print(f"⏭️ Skipping ticket creation (limit reached)")
            
            detailed_analysis.append({
                'error': error_message,
                'type': error_type,
                'severity': severity,
                'team': assigned_team,
                'ai_analysis': ai_analysis,
                'ticket_url': ticket_url,
                'test_status': 'FAILED'
            })
        # Generate comprehensive summary
        summary = f"""
🔍 **Log Analysis Complete**

📊 **Summary:**
- Total Test Cases: {total_tests}
- Passed Tests: {total_passed}
- Failed Tests: {total_failed}
- JIRA Tickets Created: {len(tickets_created)} (max {max_tickets_to_create} allowed)
- Remaining Failed Tests: {total_failed - len(tickets_created)}

📋 **Failed Test Cases Analyzed:**
- Showing {len(detailed_analysis)} failed test cases with detailed analysis
- JIRA tickets created for first {len(tickets_created)} failed tests (limited to prevent spam)
- Passed tests are not shown in detailed analysis

🎯 **Key Issues:**
{chr(10).join([f"- {analysis['type']} (Severity: {analysis['severity']}) - Assigned to {analysis['team']}" for analysis in detailed_analysis])}

⚠️ **Immediate Actions Required:**
- Review all created JIRA tickets
- Assign team members based on error types
- Implement suggested fixes from AI analysis
- Consider creating additional tickets for remaining {total_failed - len(tickets_created)} failed tests if needed
    """
        return jsonify({
            "success": True,
            "summary": summary,
            "detailed_analysis": detailed_analysis,
            "tickets_created": tickets_created,
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "processed_errors": len(detailed_analysis),
            "remaining_failed_tests": total_failed - len(tickets_created),
            "max_tickets_limit": max_tickets_to_create
        })
    except Exception as e:
        import traceback
        print("Exception in /api/analyze:", e)
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route("/api/analyze_qwen", methods=["POST"])
def analyze_qwen():
    """
    Analyze uploaded log file, generate AI-powered bug report, and create a Jira ticket using Qwen model.
    """
    if 'logFile' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    file = request.files['logFile']
    content = file.read().decode('utf-8')

    prompt = f""" 
    Analyze the following log file content and generate a comprehensive bug report.

    Log Content:
    {content}

    Please return the output strictly in this *valid JSON format*, with correct syntax (double-quoted keys and strings, arrays where appropriate). Do NOT include explanations, comments, or markdown formatting.

    Example:
    {{
      "root_cause_analysis": "Describe root cause in one sentence.",
      "immediate_fix_steps": [
        "First step.",
        "Second step."
      ],
      "prevention_measures": [
        "First prevention.",
        "Second prevention."
      ],
      "technical_impact_assessment": "Explain technical impact.",
      "recommended_priority_level": "High | Medium | Low",
      "suggested_team_for_resolution": "Team Name"
    }}

    Return only JSON following the format above.
    """
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen/qwen3-4b:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
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
                ai_response = result["choices"][0]["message"]["content"].strip()
                # Save AI response for debugging
                with open("ai_response.txt", "w", encoding="utf-8") as file:
                    file.write(ai_response)
                
                # Parse AI response as JSON
                try:
                    print(ai_response)
                    ai_response_json = json.loads(ai_response)
                    bug_report = ai_response_json.get("bug_report", ai_response_json)
                except json.JSONDecodeError:
                    return jsonify({"success": False, "error": "Invalid JSON format in AI response"}), 400
                
                # Extract fields from AI response
                root_cause = bug_report.get("root_cause_analysis", "Unknown")
                priority = bug_report.get("recommended_priority_level", "Medium")
                team = bug_report.get("suggested_team_for_resolution", "Development Team")
                technical_impact = bug_report.get("technical_impact_assessment", "Unknown")
                immediate_fix_steps = bug_report.get("immediate_fix_steps", [])
                prevention_measures = bug_report.get("prevention_measures", [])
                
                # Format AI analysis for Jira ticket
                ai_analysis = f"""
**Root Cause Analysis**: {root_cause}
**Immediate Fix Steps**:
{chr(10).join([f'- {step}' for step in immediate_fix_steps])}
**Prevention Measures**:
{chr(10).join([f'- {measure}' for measure in prevention_measures])}
**Technical Impact**: {technical_impact}
                """
                
                # Create Jira ticket using existing function
                ticket_url = create_detailed_jira_ticket(
                    error_message=root_cause,
                    error_type="Task Execution Failure",
                    severity=priority,
                    assigned_team=team,
                    ai_analysis=ai_analysis
                )
                
                # Return response with ticket URL
                response_data = {
                    "success": True,
                    "report": ai_response,
                    "ticket_url": ticket_url if ticket_url else "Failed to create Jira ticket"
                }
                return jsonify(response_data)
            else:
                return jsonify({"success": False, "error": "Invalid response format from AI"}), 500
        else:
            error_detail = response.text if response.text else f"HTTP {response.status_code}"
            return jsonify({"success": False, "error": f"AI analysis failed: {error_detail}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "AI analysis failed: Request timeout"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"AI analysis failed: Network error - {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"AI analysis failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)