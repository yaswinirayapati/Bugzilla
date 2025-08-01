document.getElementById("logFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("logFile", file);

  try {
    const response = await fetch("http://localhost:5000/api/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    const output = document.getElementById("output");

    if (data.success) {
      let htmlContent = `
        <div class="analysis-header">
          <h3>🔍 Log Analysis Results</h3>
          <div class="summary-stats">
            <span class="stat">📊 Total Test cases: ${data.total_errors}</span>
            <span class="stat">✅ Processed: ${data.processed_errors}</span>
            <span class="stat">🎫 Tickets: ${data.tickets_created.length}</span>
          </div>
        </div>
        
        <div class="summary-section">
          <h4>📋 Executive Summary</h4>
          <pre>${data.summary}</pre>
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

    output.style.display = "block";
  } catch (err) {
    const output = document.getElementById("output");
    output.innerHTML = `
      <div class="error-message">
        <h3>❌ Connection Error</h3>
        <p>Failed to contact backend: ${err.message}</p>
        <p><strong>Troubleshooting:</strong></p>
        <ul>
          <li>Make sure the backend server is running on port 5000</li>
          <li>Check if the backend is accessible at http://localhost:5000</li>
          <li>Verify CORS is properly configured</li>
        </ul>
      </div>
    `;
    output.style.display = "block";
  }
});


