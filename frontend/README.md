# Bug Tester AI - Frontend

A modern web interface for the Bug Tester AI system that analyzes log files and creates JIRA tickets automatically.

## 🚀 Quick Deploy to Vercel

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Add frontend with Vercel configuration"
   git push origin main
   ```

2. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import your GitHub repository
   - Set the **Root Directory** to `frontend`
   - Click "Deploy"

### Method 2: Deploy from Local Directory

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Follow the prompts:**
   - Link to existing project or create new
   - Set project name (e.g., `bug-tester-ai-frontend`)
   - Confirm deployment

## 🔧 Configuration

### Environment Variables (Optional)

You can set these in Vercel dashboard if needed:

```bash
# Backend API URL (auto-detected)
API_BASE_URL=https://bugzilla-tggm.onrender.com
```

### CORS Configuration

The frontend automatically detects the environment:
- **Development**: Uses `http://localhost:5000`
- **Production**: Uses `https://bugzilla-tggm.onrender.com`

## 📁 Project Structure

```
frontend/
├── index.html          # Main HTML file
├── script.js           # JavaScript logic
├── style.css           # Styling
├── package.json        # Node.js configuration
├── vercel.json         # Vercel deployment config
└── README.md           # This file
```

## 🛠️ Local Development

### Prerequisites
- Node.js (v14 or higher)
- Backend server running on `http://localhost:5000`

### Setup
1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   - Navigate to `http://localhost:3000`
   - The app will automatically connect to your local backend

## 🌐 Features

### ✅ What's Working
- **File Upload**: Drag & drop or click to upload log files
- **Real-time Analysis**: Instant log analysis with AI insights
- **JIRA Integration**: Automatic ticket creation with team assignment
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Comprehensive error messages and debugging
- **Loading States**: Visual feedback during processing
- **Backend Status**: Real-time connection status

### 🔧 Technical Features
- **Environment Detection**: Auto-switches between local and production APIs
- **CORS Handling**: Proper cross-origin request handling
- **Error Recovery**: Graceful fallbacks and retry mechanisms
- **Debug Information**: Detailed error reporting for troubleshooting

## 🚀 Deployment Commands

### Vercel CLI Commands

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from frontend directory
cd frontend
vercel

# Deploy to production
vercel --prod

# List deployments
vercel ls

# View deployment details
vercel inspect [deployment-url]
```

### Git Commands for Deployment

```bash
# Commit changes
git add .
git commit -m "Update frontend for Vercel deployment"

# Push to GitHub
git push origin main

# Vercel will auto-deploy from GitHub
```

## 🔍 Testing

### Local Testing
1. Start your backend server: `python api_server.py`
2. Open frontend: `http://localhost:3000`
3. Upload a log file and test analysis

### Production Testing
1. Deploy to Vercel
2. Test with your deployed backend
3. Verify CORS is working correctly

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check backend CORS configuration
   - Verify API URL is correct
   - Ensure backend is running

2. **File Upload Issues**
   - Check file size limits
   - Verify file format (.log, .txt)
   - Check browser console for errors

3. **Backend Connection Issues**
   - Verify backend URL in script.js
   - Check if backend is deployed and running
   - Test API endpoints directly

### Debug Information

The frontend provides detailed debug information:
- API URL being used
- File details (name, size)
- Error messages and stack traces
- Backend connection status

## 📊 Performance

- **Lightweight**: No heavy frameworks, fast loading
- **Responsive**: Works on all device sizes
- **Cached**: Static assets are cached by Vercel CDN
- **Optimized**: Minified CSS and JS for production

## 🔒 Security

- **CORS**: Properly configured for production
- **No Secrets**: No sensitive data in frontend code
- **HTTPS**: Automatic SSL certificate from Vercel
- **Headers**: Security headers configured in vercel.json

## 📈 Monitoring

- **Vercel Analytics**: Built-in performance monitoring
- **Error Tracking**: Console errors logged
- **Uptime**: Vercel provides 99.9% uptime SLA

## 🎯 Next Steps

After deployment:
1. **Test the application** with various log files
2. **Configure CORS** in your backend for the Vercel domain
3. **Set up monitoring** and alerts
4. **Customize styling** if needed
5. **Add more features** like user authentication

## 📞 Support

If you encounter issues:
1. Check the browser console for errors
2. Verify backend is running and accessible
3. Test API endpoints directly
4. Check Vercel deployment logs
5. Review CORS configuration

---

**Happy Deploying! 🚀** 