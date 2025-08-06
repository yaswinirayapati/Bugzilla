# Bug Testing AI Agent

An intelligent log analysis tool that automatically detects errors, analyzes them using AI, and creates JIRA tickets.

## Issues Fixed

### ✅ Backend Issues:
- Removed hardcoded API key (security risk)
- Fixed environment variable configuration
- Improved error handling

### ✅ UI Interface Issues:
- Created complete frontend HTML file
- Added proper styling matching the design
- Implemented file upload functionality
- Added real-time status updates

## Setup Instructions

### 1. Install Dependencies
```bash
pip install flask flask-cors python-dotenv jira requests
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# JIRA Configuration
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_URL=https://your-domain.atlassian.net
PROJECT_KEY=BUG

# OpenRouter AI Configuration
OPENROUTER_API_KEY=your-openrouter-api-key

# Log File Path (optional)
LOG_FILE_PATH=/path/to/your/log/file.log
```

### 3. Start the Backend Server
```bash
cd backend
python api_server.py
```

### 4. Open the Frontend
Open `frontend/index.html` in your browser or serve it with a local server.

## Troubleshooting

### Common Issues:

1. **"Cannot connect to backend API"**
   - Make sure the backend server is running on port 5000
   - Check if there are any firewall issues

2. **"JIRA Connection Failed"**
   - Verify your JIRA credentials in the `.env` file
   - Ensure the JIRA URL is correct
   - Check if your API token has proper permissions

3. **"AI Integration Failed"**
   - Verify your OpenRouter API key
   - Check your internet connection
   - Ensure the API key has sufficient credits

4. **File upload not working**
   - Make sure you're selecting a valid log file (.log or .txt)
   - Check browser console for JavaScript errors

### Testing the System:

1. **Test Backend Status:**
   ```
   GET http://localhost:5000/api/status
   ```

2. **Test JIRA Connection:**
   ```
   GET http://localhost:5000/api/test-jira
   ```

3. **Test Team Assignment:**
   ```
   POST http://localhost:5000/api/test-team-assignment
   ```

## Features

- 🔍 **Automatic Error Detection**: Scans log files for errors, exceptions, and failures
- 🤖 **AI-Powered Analysis**: Uses OpenRouter AI to provide detailed error analysis
- 🎯 **Smart Team Assignment**: Automatically assigns errors to appropriate technical teams
- 📋 **JIRA Integration**: Creates detailed tickets with AI analysis and recommendations
- 🎨 **Modern UI**: Clean, responsive interface with real-time feedback

## File Structure

```
bug-tester-ai/
├── backend/
│   ├── api_server.py      # Main Flask API server
│   └── main.py           # Alternative server implementation
├── frontend/
│   └── index.html        # Complete UI interface
└── README.md             # This file
```

## API Endpoints

- `POST /api/analyze` - Analyze uploaded log file
- `GET /api/status` - Check system status
- `GET /api/test-jira` - Test JIRA connection
- `POST /api/test-team-assignment` - Test team assignment logic
- `GET /api/errors` - Get recent errors
- `GET /api/tickets` - Get recent tickets
