# Deployment Guide

This guide walks you through deploying the Political Party Chatbot to Render.com with GitHub Actions integration.

## 🚀 Quick Deploy to Render

### 1. Prerequisites
- GitHub account with this repository
- Render.com account (free)
- Google Gemini API key

### 2. Deploy Steps

#### Step 1: Fork/Clone Repository
Make sure your code is in a GitHub repository.

#### Step 2: Connect to Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub account and select this repository
4. Render will automatically detect the `render.yaml` configuration

#### Step 3: Set Environment Variables
In your Render dashboard, add these environment variables:
```
GEMINI_API_KEY=your_actual_api_key_here
```
(FLASK_SECRET_KEY will be auto-generated)

#### Step 4: Deploy
Click "Create Web Service" and wait for deployment (~2-3 minutes)

Your app will be available at: `https://your-app-name.onrender.com`

**⚡ Fast Deployment**: Cache is pre-built and included in the repository, so deployments take only ~1-2 minutes!

## 🔧 Configuration Details

### Render Configuration (`render.yaml`)
- **Build Command**: Installs dependencies only (cache pre-built)
- **Start Command**: Runs the Flask app
- **Region**: Frankfurt (closest to Norway)
- **Cache Strategy**: Included in git repository (6MB)
- **Auto-Deploy**: Enabled for main branch

### GitHub Actions (`.github/workflows/ci-cd.yaml`)
- **Triggers**: Push to main/visual_interface, PRs to main
- **Tests**: Code syntax, imports, preprocessing
- **Deployment**: Automatic via Render webhook

## 📊 Monitoring & Management

### Render Dashboard
- **Logs**: View real-time application logs
- **Metrics**: CPU, memory, response times
- **Environment**: Manage environment variables
- **Deployments**: View deployment history

### Scaling Options
- **Free Tier**: 750 hours/month, sleeps after 15min idle
- **Paid Tiers**: Starting $7/month for always-on service

## 🐛 Troubleshooting

### Common Issues

**Build Failed - Missing API Key**
```bash
# In Render dashboard, ensure GEMINI_API_KEY is set
```

**Cache Missing**
```bash
# Cache is included in git, but if missing:
python preprocess_programs.py
git add cache/
git commit -m "Rebuild cache"
```

**App Won't Start**
```bash
# Check if PORT environment variable is set correctly
# Default: 8080 (auto-configured by Render)
```

**Slow Cold Starts**
- Expected on free tier (app sleeps after 15min)
- Upgrade to paid tier for always-on service
- Cache is persistent, so subsequent requests are fast

### Logs Access
```bash
# Via Render dashboard
# Or CLI: render logs -s your-app-name
```

## 🔄 Updates & Maintenance

### Automatic Deployments
1. Push to main branch
2. GitHub Actions runs tests
3. Render automatically deploys if tests pass
4. New version live in ~2-3 minutes

### Manual Cache Rebuild
If you update party programs:
1. Add/update files in `partiprogram/` directory
2. Run `python preprocess_programs.py` locally
3. Commit the updated `cache/` directory
4. Push to repository (deployment uses the committed cache)

### Environment Updates
Update environment variables in Render dashboard:
- Go to your service → Environment
- Add/modify variables
- Click "Save Changes" (triggers redeploy)

## 💰 Cost Estimation

### Free Tier (Recommended for Testing)
- **Cost**: $0/month
- **Limits**: 750 hours, sleeps after 15min idle
- **Perfect for**: Friends/family usage, development

### Starter Tier (Recommended for Production)
- **Cost**: $7/month
- **Benefits**: Always-on, no sleep, faster builds
- **Perfect for**: Regular usage, better UX

## 🔒 Security Notes

- Environment variables are encrypted in Render
- HTTPS automatically enabled
- No sensitive data in repository
- API keys managed through dashboard only

## 📞 Support

### Render Support
- Documentation: [render.com/docs](https://render.com/docs)
- Community: [community.render.com](https://community.render.com)

### Application Issues
- Check GitHub Actions for CI/CD status
- Review Render logs for runtime errors
- Ensure all environment variables are set correctly