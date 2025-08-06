// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://localhost:5000' 
  : 'https://bugzilla-tggm.onrender.com';

console.log('🔧 API Base URL:', API_BASE_URL);

// Utility function to make API calls
async function makeApiCall(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log('🌐 Making API call to:', url);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('❌ API call failed:', error);
    throw error;
  }
}

// File upload and analysis
document.getElementById("logFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("logFile", file);

  // Show loading state
  const output = document.getElementById("output");
  output.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>🔍 Analyzing log file...</p>
      <p class="loading-details">Processing ${file.name} (${(file.size / 1024).toFixed(1)} KB)</p>
    </div>
  `;
  output.style.display = "block";

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log('📊 Analysis results:', data);

    if (data.success) {
      let htmlContent = `
        <div class="analysis-header">
          <h3>🔍 Log Analysis Results</h3>
          <div class="summary-stats">
            <span class="stat">📊 Total Tests: ${data.total_tests || 0}</span>
            <span class="stat">✅ Passed: ${data.passed_tests || 0}</span>
            <span class="stat">❌ Failed: ${data.failed_tests || 0}</span>
            <span class="stat">🎫 Tickets: ${data.tickets_created ? data.tickets_created.length : 0}</span>
          </div>
        </div>
        
        <div class="summary-section">
          <h4>📋 Executive Summary</h4>
          <pre>${data.summary || 'No summary available'}</pre>
        </div>
      `;

      if (data.detailed_analysis && data.detailed_analysis.length > 0) {
        htmlContent += `<div class="detailed-analysis">`;
        
        data.detailed_analysis.forEach((analysis, index) => {
          htmlContent += `
            <div class="error-card">
              <div class="error-header">
                <h5>🚨 Error ${index + 1}</h5>
                <div class="error-meta">
                  <span class="badge severity-${analysis.severity.toLowerCase()}">${analysis.severity}</span>
                  <span class="badge team-badge">${analysis.team}</span>
                  <span class="badge type-badge">${analysis.type}</span>
                </div>
              </div>
              
              <div class="error-content">
                <strong>Error Message:</strong>
                <pre class="error-message">${analysis.error}</pre>
                
                <div class="ai-analysis">
                  <strong>🤖 AI Analysis & Recommendations:</strong>
                  <div class="ai-content">${analysis.ai_analysis.replace(/\n/g, '<br>')}</div>
                </div>
                
                ${analysis.ticket_url ? `
                  <div class="ticket-link">
                    <strong>🎫 JIRA Ticket:</strong>
                    <a href="${analysis.ticket_url}" target="_blank" class="ticket-btn">
                      View Ticket
                    </a>
                  </div>
                ` : '<p class="ticket-error">❌ Failed to create JIRA ticket</p>'}
              </div>
            </div>
          `;
        });
        
        htmlContent += `</div>`;
      }

      if (data.tickets_created && data.tickets_created.length > 0) {
        htmlContent += `
          <div class="tickets-section">
            <h4>🎫 Created JIRA Tickets</h4>
            <div class="ticket-links">
              ${data.tickets_created.map(url => `
                <a href="${url}" target="_blank" class="ticket-link-btn">View Ticket</a>
              `).join('')}
            </div>
          </div>
        `;
      }

      output.innerHTML = htmlContent;
    } else {
      output.innerHTML = `
        <div class="success-message">
          <h3>✅ ${data.message || 'No errors found!'}</h3>
          <p>${data.suggestion || 'The log file appears to be clean.'}</p>
        </div>
      `;
    }
  } catch (err) {
    console.error('❌ Analysis failed:', err);
    output.innerHTML = `
      <div class="error-message">
        <h3>❌ Connection Error</h3>
        <p>Failed to contact backend: ${err.message}</p>
        <p><strong>Troubleshooting:</strong></p>
        <ul>
          <li>Check if the backend is running at: ${API_BASE_URL}</li>
          <li>Verify CORS is properly configured</li>
          <li>Check network connectivity</li>
          <li>Try refreshing the page</li>
        </ul>
        <div class="debug-info">
          <strong>Debug Info:</strong>
          <p>API URL: ${API_BASE_URL}</p>
          <p>File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)</p>
        </div>
      </div>
    `;
  }
});

// Test API connection on page load
window.addEventListener('load', async () => {
  try {
    const statusData = await makeApiCall('/api/status');
    console.log('✅ Backend status:', statusData);
    
    // Update status indicator if available
    const statusIndicator = document.getElementById('backend-status');
    if (statusIndicator) {
      statusIndicator.innerHTML = `
        <div class="status-success">
          ✅ Backend Connected: ${statusData.server}
        </div>
      `;
    }
  } catch (error) {
    console.warn('⚠️ Backend status check failed:', error);
    
    const statusIndicator = document.getElementById('backend-status');
    if (statusIndicator) {
      statusIndicator.innerHTML = `
        <div class="status-warning">
          ⚠️ Backend Status: ${error.message}
        </div>
      `;
    }
  }
});


