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
        results.append({
            "error": error,
            "type": error_type,
            "severity": severity,
            "team": assigned_team
        })
    
    return jsonify({
        "success": True,
        "results": results
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
    # Accept file upload
    if 'logFile' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    file = request.files['logFile']
    content = file.read().decode('utf-8')
    
    # Enhanced error detection with context
    error_lines = []
    for line_num, line in enumerate(content.splitlines(), 1):
        if any(k in line.lower() for k in ["error", "exception", "failed", "timeout", "connection refused"]):
            error_lines.append({
                'line_number': line_num,
                'content': line.strip(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    if not error_lines:
        return jsonify({
            "success": False, 
            "message": "✅ No errors detected in the log file!",
            "errors": [], 
            "suggestion": "The log file appears to be clean with no critical errors.",
            "ticket": None
        })
    
    # Process each error with detailed analysis
    detailed_analysis = []
    tickets_created = []
    
    print(f"🔍 Processing {len(error_lines)} errors...")
    
    for error_data in error_lines[:3]:  # Limit to first 3 errors to avoid spam
        error_message = error_data['content']
        error_type, severity = analyze_error_type(error_message)
        assigned_team = assign_team(error_message)
        ai_analysis = get_ai_analysis(error_message, error_type)
        
        print(f"📋 Error: {error_message[:50]}...")
        print(f"   Type: {error_type}, Severity: {severity}, Team: {assigned_team}")
        
        # Create detailed JIRA ticket
        ticket_url = create_detailed_jira_ticket(
            error_message, error_type, severity, assigned_team, ai_analysis
        )
        
        detailed_analysis.append({
            'error': error_message,
            'type': error_type,
            'severity': severity,
            'team': assigned_team,
            'ai_analysis': ai_analysis,
            'ticket_url': ticket_url
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
- Total Errors Found: {len(error_lines)}
- Errors Processed: {len(detailed_analysis)}
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
        "total_errors": len(error_lines),
        "processed_errors": len(detailed_analysis)
    })





def assign_team(error_message):
    """Assign technical team based on error content"""
    error_lower = error_message.lower()
    
    # Enhanced team mapping with more specific keywords and weights
    team_scores = {
        'database': 0,
        'frontend': 0,
        'backend': 0,
        'devops': 0,
        'security': 0,
        'network': 0
    }
    
    # Database keywords (weight: 2 for exact matches, 1 for partial)
    db_keywords = ['sql', 'mysql', 'postgresql', 'mongodb', 'database', 'connection', 'timeout', 'deadlock', 'query', 'table', 'index', 'db_', 'database_']
    # Frontend keywords
    fe_keywords = ['javascript', 'react', 'angular', 'vue', 'css', 'html', 'dom', 'browser', 'frontend', 'ui', 'component', 'jsx', 'tsx', 'client-side']
    # Backend keywords
    be_keywords = ['python', 'java', 'nodejs', 'php', 'api', 'server', 'endpoint', 'backend', 'controller', 'service', 'route', 'middleware']
    # DevOps keywords
    do_keywords = ['docker', 'kubernetes', 'aws', 'azure', 'deployment', 'infrastructure', 'ci/cd', 'pipeline', 'jenkins', 'gitlab']
    # Security keywords
    sec_keywords = ['authentication', 'authorization', 'ssl', 'encryption', 'firewall', 'security', 'token', 'password', 'jwt', 'oauth']
    # Network keywords
    net_keywords = ['connection', 'timeout', 'dns', 'http', 'https', 'proxy', 'network', 'socket', 'tcp', 'udp']
    
    # Score each team based on keyword matches with weights
    for keyword in db_keywords:
        if keyword in error_lower:
            team_scores['database'] += 2 if keyword in ['sql', 'mysql', 'postgresql', 'mongodb'] else 1
    
    for keyword in fe_keywords:
        if keyword in error_lower:
            team_scores['frontend'] += 2 if keyword in ['javascript', 'react', 'angular', 'vue'] else 1
    
    for keyword in be_keywords:
        if keyword in error_lower:
            team_scores['backend'] += 2 if keyword in ['python', 'java', 'nodejs', 'php'] else 1
    
    for keyword in do_keywords:
        if keyword in error_lower:
            team_scores['devops'] += 2 if keyword in ['docker', 'kubernetes', 'aws', 'azure'] else 1
    
    for keyword in sec_keywords:
        if keyword in error_lower:
            team_scores['security'] += 2 if keyword in ['authentication', 'authorization', 'ssl'] else 1
    
    for keyword in net_keywords:
        if keyword in error_lower:
            team_scores['network'] += 2 if keyword in ['connection', 'timeout', 'dns'] else 1
    
    # Find the team with highest score
    max_score = max(team_scores.values())
    if max_score > 0:
        for team, score in team_scores.items():
            if score == max_score:
                print(f"🎯 Team assigned: {team.title()} (score: {score})")
                return team.title()
    
    print(f"🎯 No specific team match, assigning to General Development")
    return "General Development"



    # Store errors and tickets in memory for demo
ERRORS = []
TICKETS = []


# Technical team mapping based on error patterns
TEAM_MAPPING = {
    'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'connection', 'timeout', 'deadlock'],
    'frontend': ['javascript', 'react', 'angular', 'vue', 'css', 'html', 'dom', 'browser'],
    'backend': ['python', 'java', 'nodejs', 'php', 'api', 'server', 'endpoint'],
    'devops': ['docker', 'kubernetes', 'aws', 'azure', 'deployment', 'infrastructure'],
    'security': ['authentication', 'authorization', 'ssl', 'encryption', 'firewall'],
    'network': ['connection', 'timeout', 'dns', 'http', 'https', 'proxy']
}

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