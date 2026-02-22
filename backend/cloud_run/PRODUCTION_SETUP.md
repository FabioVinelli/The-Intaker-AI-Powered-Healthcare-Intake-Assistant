# Production Environment Setup Guide

This guide provides comprehensive instructions for setting up "The Intaker" Flask API in a production environment on Google Cloud Run.

## Overview

The production setup includes:
- ✅ **Enhanced Configuration Management**: Environment variables and Google Secret Manager integration
- ✅ **Structured Logging**: JSON-formatted logs for Cloud Logging integration
- ✅ **Optimized Docker Container**: Multi-stage build with security best practices
- ✅ **Automated Deployment**: Production-ready deployment script with IAM setup

## Prerequisites

1. **Google Cloud SDK** installed and authenticated
2. **Docker** installed and running
3. **Python 3.11+** for local development
4. **Google Cloud Project** with billing enabled

## Quick Start

1. **Clone and Navigate to the API Directory**:
   ```bash
   cd backend/cloud_run
   ```

2. **Set Environment Variables**:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export FLASK_ENV="production"
   ```

3. **Deploy to Production**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Detailed Configuration

### 1. Environment Variables

The application uses environment variables for all configuration. See `env.production.example` for a complete list.

#### Core Production Variables
```bash
# Required for production
FLASK_ENV=production
GOOGLE_CLOUD_PROJECT=your-project-id
SECRET_KEY=your-super-secret-key
STORAGE_BUCKET_NAME=your-project-patient-documents

# Logging configuration
LOG_LEVEL=WARNING
LOG_FORMAT=structured

# Security settings
SESSION_COOKIE_SECURE=true
USE_SECRET_MANAGER=true
```

#### Rate Limiting Configuration
```bash
# Memory-based (development)
RATELIMIT_STORAGE_URL=memory://

# Redis-based (production scaling)
RATELIMIT_STORAGE_URL=redis://your-redis-host:6379/0

# Endpoint-specific limits
RATELIMIT_PHI_ACCESS=10 per minute
RATELIMIT_HEALTH=200 per minute
```

### 2. Google Secret Manager Integration

The production configuration automatically integrates with Google Secret Manager for sensitive data:

**Secrets Created Automatically**:
- `intaker-secret-key`: Application secret key
- `google-client-id`: OAuth client ID (manual setup required)
- `google-client-secret`: OAuth client secret (manual setup required)

**Manual Secret Setup** (for OAuth):
```bash
# Create Google OAuth secrets
echo -n "your-google-client-id" | gcloud secrets create google-client-id --data-file=-
echo -n "your-google-client-secret" | gcloud secrets create google-client-secret --data-file=-
```

### 3. Structured Logging

Production logging uses structured JSON format for Cloud Logging integration:

**Log Levels**:
- `DEBUG`: Development debugging
- `INFO`: General information
- `WARNING`: Production default
- `ERROR`: Error conditions only

**Log Format Example**:
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "severity": "WARNING",
  "message": "Rate limit exceeded",
  "service": "intaker-api",
  "url": "/api/v1/patients",
  "method": "POST",
  "remote_addr": "192.168.1.100",
  "user_id": "user123"
}
```

### 4. Docker Optimization

The production Dockerfile uses multi-stage builds for optimization:

**Features**:
- 🔒 **Security**: Non-root user with minimal permissions
- 📦 **Size**: Multi-stage build reduces image size by ~40%
- ⚡ **Performance**: Optimized gunicorn configuration
- 🏥 **Health Checks**: Built-in health check endpoint

**Gunicorn Configuration**:
```bash
# Optimized for Cloud Run (1 vCPU instance)
--workers 1
--threads 8
--worker-connections 1000
--timeout 30
--keep-alive 2
```

## Deployment Process

### Automated Deployment

The `deploy.sh` script handles the complete deployment process:

```bash
./deploy.sh
```

**What it does**:
1. ✅ Validates authentication and project setup
2. ✅ Enables required Google Cloud APIs
3. ✅ Creates Secret Manager secrets
4. ✅ Sets up Cloud Storage bucket with HIPAA compliance
5. ✅ Builds and pushes Docker image
6. ✅ Deploys to Cloud Run with production configuration
7. ✅ Sets up IAM permissions
8. ✅ Tests deployment health

### Manual Deployment

For custom deployments, use these gcloud commands:

```bash
# Build and push image
docker build -t gcr.io/your-project/intaker-api .
docker push gcr.io/your-project/intaker-api

# Deploy to Cloud Run
gcloud run deploy intaker-api \
  --image gcr.io/your-project/intaker-api \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=your-project \
  --allow-unauthenticated
```

## Environment-Specific Configurations

### Development Environment
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
export LOG_FORMAT=simple
export SESSION_COOKIE_SECURE=false
```

### Staging Environment
```bash
export FLASK_ENV=production
export LOG_LEVEL=INFO
export LOG_FORMAT=structured
export SESSION_COOKIE_SECURE=true
```

### Production Environment
```bash
export FLASK_ENV=production
export LOG_LEVEL=WARNING
export LOG_FORMAT=structured
export USE_SECRET_MANAGER=true
export SESSION_COOKIE_SECURE=true
```

## Monitoring and Observability

### Cloud Logging Integration
All logs are automatically sent to Cloud Logging with structured format for easy querying:

```bash
# View recent logs
gcloud logs read --service=intaker-api --limit=50

# Filter by severity
gcloud logs read --filter="severity>=WARNING" --service=intaker-api

# Search for specific operations
gcloud logs read --filter="jsonPayload.url:/api/v1/patients" --service=intaker-api
```

### Health Check Endpoints
- **Health Check**: `/health` - Basic service health
- **API Info**: `/` - Service information and endpoints
- **Documentation**: `/docs/swagger` - Interactive API documentation

### Security Headers
Production automatically adds security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Troubleshooting

### Common Issues

1. **Secret Manager Access Denied**:
   ```bash
   # Grant access to service account
   gcloud projects add-iam-policy-binding your-project \
     --member="serviceAccount:your-service-account" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Health Check Failures**:
   ```bash
   # Check logs for startup issues
   gcloud logs read --service=intaker-api --limit=20
   
   # Verify service is running
   gcloud run services describe intaker-api --region=us-central1
   ```

3. **Authentication Issues**:
   ```bash
   # Verify OAuth configuration
   gcloud secrets versions access latest --secret="google-client-id"
   ```

### Performance Optimization

For high-traffic production environments:

1. **Enable Redis for Rate Limiting**:
   ```bash
   gcloud run services update intaker-api \
     --set-env-vars RATELIMIT_STORAGE_URL=redis://your-redis-url
   ```

2. **Increase Resources**:
   ```bash
   gcloud run services update intaker-api \
     --memory 2Gi \
     --cpu 2 \
     --max-instances 50
   ```

3. **Configure Auto-scaling**:
   ```bash
   gcloud run services update intaker-api \
     --min-instances 1 \
     --concurrency 100
   ```

## Security Best Practices

✅ **Secrets Management**: All sensitive data in Secret Manager  
✅ **Non-root Container**: Docker runs as unprivileged user  
✅ **Security Headers**: Comprehensive security header configuration  
✅ **HTTPS Only**: All cookies marked secure in production  
✅ **Rate Limiting**: Endpoint-specific rate limiting enabled  
✅ **Audit Logging**: All API calls logged for HIPAA compliance  

## Next Steps

After successful deployment:

1. **Configure DNS**: Point your domain to the Cloud Run service URL
2. **Set up Monitoring**: Configure Cloud Monitoring alerts
3. **Enable Redis**: For production rate limiting scaling
4. **Configure Backups**: Ensure Firestore backups are running
5. **Security Review**: Run security scans and penetration testing

## Support

For issues or questions:
- Check the application logs: `gcloud logs read --service=intaker-api`
- Review the deployment logs in Cloud Build
- Verify IAM permissions and API enablement
- Consult the API documentation at `/docs/swagger` 