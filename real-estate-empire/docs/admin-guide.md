# Real Estate Empire - Administrator Guide

## Table of Contents

1. [System Administration](#system-administration)
2. [User Management](#user-management)
3. [Security Configuration](#security-configuration)
4. [Data Management](#data-management)
5. [Integration Management](#integration-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Backup & Recovery](#backup--recovery)
8. [Compliance & Audit](#compliance--audit)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

## System Administration

### Initial System Setup

#### Environment Configuration

1. **Environment Variables**
   ```bash
   # Copy the environment template
   cp .env.example .env
   
   # Configure required variables
   SECRET_KEY=your_secret_key_here
   ENCRYPTION_KEY=your_encryption_key_here
   DATABASE_URL=your_database_connection_string
   ```

2. **Security Configuration**
   - Set strong encryption keys
   - Configure HTTPS certificates
   - Set up trusted host domains
   - Configure CORS origins

3. **Database Setup**
   ```bash
   # Create database tables
   python -c "from app.core.database import create_tables; create_tables()"
   
   # Run migrations if needed
   alembic upgrade head
   ```

#### Application Deployment

1. **Production Deployment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run with production settings
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem
   ```

2. **Docker Deployment**
   ```bash
   # Build container
   docker build -t real-estate-empire .
   
   # Run container
   docker run -d -p 8000:8000 --env-file .env real-estate-empire
   ```

### System Configuration

#### Security Settings

Access security configuration at `/admin/security`:

- **Password Policy**: Set complexity requirements
- **Session Management**: Configure timeout and limits
- **MFA Requirements**: Enable/disable multi-factor authentication
- **Rate Limiting**: Set API request limits
- **Audit Logging**: Configure audit trail settings

#### Application Settings

- **Data Retention**: Set automatic cleanup policies
- **Notification Settings**: Configure system alerts
- **Integration Endpoints**: Manage external service connections
- **Feature Flags**: Enable/disable specific features

## User Management

### User Administration

#### Creating Users

1. **Admin Panel Method**
   - Navigate to **Admin** > **Users**
   - Click **"Create User"**
   - Fill in user details and role
   - Set initial password (user must change on first login)
   - Send welcome email with login instructions

2. **API Method**
   ```bash
   curl -X POST "/auth/register" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "email": "user@company.com",
       "password": "TempPassword123!",
       "role": "agent",
       "full_name": "New User"
     }'
   ```

#### User Roles and Permissions

| Role | Permissions | Description |
|------|-------------|-------------|
| **Admin** | Full system access | System administrators |
| **Manager** | Read/write most data | Team managers |
| **Agent** | Property and lead management | Real estate agents |
| **Investor** | Read-only access to relevant data | External investors |
| **Viewer** | Limited read-only access | Observers and analysts |

#### Managing User Accounts

1. **Account Status Management**
   - **Active**: Normal access
   - **Inactive**: Temporarily disabled
   - **Locked**: Security lockout
   - **Suspended**: Administrative suspension

2. **Password Management**
   - Force password reset
   - Set password expiration
   - View password change history
   - Configure password policies

3. **Session Management**
   - View active sessions
   - Revoke specific sessions
   - Set session timeout policies
   - Monitor concurrent sessions

### Bulk User Operations

#### User Import

1. **CSV Import Format**
   ```csv
   username,email,full_name,role,department
   jdoe,john.doe@company.com,John Doe,agent,sales
   msmith,mary.smith@company.com,Mary Smith,manager,operations
   ```

2. **Import Process**
   - Navigate to **Admin** > **Users** > **Import**
   - Upload CSV file
   - Map columns to user fields
   - Review and confirm import
   - Send welcome emails to new users

#### Bulk Updates

- **Role Changes**: Update multiple user roles
- **Department Assignments**: Bulk department changes
- **Permission Updates**: Apply permission changes
- **Account Status**: Bulk activate/deactivate users

## Security Configuration

### Authentication Settings

#### Password Policies

Configure in **Admin** > **Security** > **Password Policy**:

- **Minimum Length**: 8-20 characters
- **Complexity Requirements**: Upper, lower, numbers, symbols
- **Password History**: Prevent reuse of last N passwords
- **Expiration**: Force password changes every N days
- **Account Lockout**: Lock after N failed attempts

#### Multi-Factor Authentication

1. **System-wide MFA**
   - **Required for Admins**: Always enforce for admin users
   - **Optional for Users**: Allow users to enable voluntarily
   - **Required for All**: Enforce for all user accounts

2. **MFA Methods**
   - **TOTP Apps**: Google Authenticator, Authy, etc.
   - **SMS**: Text message codes (less secure)
   - **Email**: Email-based codes (backup method)
   - **Hardware Tokens**: FIDO2/WebAuthn support

### Access Control

#### IP Restrictions

Configure allowed IP ranges:

```json
{
  "allowed_ips": [
    "192.168.1.0/24",
    "10.0.0.0/8",
    "203.0.113.0/24"
  ],
  "blocked_ips": [
    "192.168.1.100"
  ]
}
```

#### API Security

1. **API Key Management**
   - Generate system API keys
   - Set key expiration dates
   - Monitor key usage
   - Revoke compromised keys

2. **Rate Limiting**
   - Configure per-user limits
   - Set global rate limits
   - Monitor usage patterns
   - Block abusive requests

### Security Monitoring

#### Audit Logging

All security events are logged:

- **Authentication Events**: Logins, logouts, failures
- **Authorization Events**: Permission checks, access denials
- **Data Access**: Sensitive data viewing/modification
- **Administrative Actions**: User management, system changes

#### Security Alerts

Configure alerts for:

- **Failed Login Attempts**: Multiple failures from same IP
- **Unusual Access Patterns**: Off-hours access, new locations
- **Permission Escalation**: Role changes, new permissions
- **Data Export**: Large data downloads
- **System Changes**: Configuration modifications

## Data Management

### Database Administration

#### Database Maintenance

1. **Regular Maintenance Tasks**
   ```sql
   -- Update statistics
   ANALYZE;
   
   -- Vacuum database (PostgreSQL)
   VACUUM ANALYZE;
   
   -- Check database integrity
   SELECT * FROM pg_stat_database;
   ```

2. **Index Management**
   - Monitor query performance
   - Add indexes for slow queries
   - Remove unused indexes
   - Rebuild fragmented indexes

#### Data Backup

1. **Automated Backups**
   ```bash
   # Daily backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump real_estate_empire > backup_$DATE.sql
   
   # Encrypt backup
   gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
       --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
       --output backup_$DATE.sql.gpg backup_$DATE.sql
   
   # Upload to secure storage
   aws s3 cp backup_$DATE.sql.gpg s3://backups/database/
   ```

2. **Backup Verification**
   - Test restore procedures monthly
   - Verify backup integrity
   - Document recovery procedures
   - Maintain backup retention policy

### Data Import/Export

#### Property Data Import

1. **MLS Integration**
   - Configure MLS credentials
   - Set up automated imports
   - Map MLS fields to system fields
   - Handle data conflicts and duplicates

2. **CSV Import**
   - Validate data format
   - Handle missing fields
   - Process large files in batches
   - Generate import reports

#### Data Export

1. **Compliance Exports**
   - GDPR data portability
   - Audit trail exports
   - Financial reporting data
   - Legal discovery requests

2. **Integration Exports**
   - CRM system synchronization
   - Accounting software integration
   - Marketing platform data
   - Third-party analytics

### Data Quality Management

#### Data Validation

1. **Automated Validation Rules**
   - Address format validation
   - Phone number formatting
   - Email address verification
   - Property data consistency

2. **Data Cleansing**
   - Remove duplicate records
   - Standardize data formats
   - Fill missing information
   - Correct data inconsistencies

#### Data Monitoring

- **Data Quality Metrics**: Completeness, accuracy, consistency
- **Data Usage Analytics**: Most accessed data, usage patterns
- **Performance Monitoring**: Query performance, slow operations
- **Storage Monitoring**: Database size, growth trends

## Integration Management

### External Service Integrations

#### MLS Integration

1. **Configuration**
   ```json
   {
     "mls_provider": "RETS",
     "login_url": "https://mls.example.com/login",
     "username": "your_username",
     "password": "your_password",
     "user_agent": "RealEstateEmpire/1.0",
     "sync_frequency": "hourly"
   }
   ```

2. **Data Mapping**
   - Map MLS fields to system fields
   - Handle custom fields
   - Set up data transformations
   - Configure filtering rules

#### Communication Services

1. **Email Service (SendGrid)**
   ```json
   {
     "api_key": "your_sendgrid_api_key",
     "from_email": "noreply@yourdomain.com",
     "from_name": "Real Estate Empire",
     "templates": {
       "welcome": "d-1234567890abcdef",
       "password_reset": "d-abcdef1234567890"
     }
   }
   ```

2. **SMS Service (Twilio)**
   ```json
   {
     "account_sid": "your_twilio_account_sid",
     "auth_token": "your_twilio_auth_token",
     "from_number": "+1234567890",
     "webhook_url": "https://yourdomain.com/webhooks/sms"
   }
   ```

### API Management

#### API Documentation

- **OpenAPI Specification**: Auto-generated API docs
- **Authentication Guide**: API key and OAuth setup
- **Rate Limiting**: Usage limits and best practices
- **Error Handling**: Common errors and solutions

#### Webhook Management

1. **Webhook Configuration**
   ```json
   {
     "url": "https://external-system.com/webhook",
     "events": ["property.created", "lead.updated"],
     "secret": "webhook_secret_key",
     "retry_policy": {
       "max_retries": 3,
       "backoff_factor": 2
     }
   }
   ```

2. **Webhook Monitoring**
   - Delivery success rates
   - Response times
   - Failed deliveries
   - Retry attempts

## Monitoring & Maintenance

### System Monitoring

#### Performance Metrics

1. **Application Metrics**
   - Response times
   - Request rates
   - Error rates
   - Active users

2. **Infrastructure Metrics**
   - CPU usage
   - Memory consumption
   - Disk space
   - Network traffic

#### Health Checks

1. **Automated Health Checks**
   ```bash
   # API health check
   curl -f http://localhost:8000/health || exit 1
   
   # Database connectivity
   python -c "from app.core.database import engine; engine.execute('SELECT 1')"
   
   # External service connectivity
   curl -f https://api.external-service.com/health
   ```

2. **Monitoring Dashboard**
   - Real-time system status
   - Performance graphs
   - Alert notifications
   - Historical trends

### Maintenance Tasks

#### Regular Maintenance

1. **Daily Tasks**
   - Check system health
   - Review error logs
   - Monitor disk space
   - Verify backups

2. **Weekly Tasks**
   - Update system statistics
   - Clean temporary files
   - Review security logs
   - Test backup restores

3. **Monthly Tasks**
   - Update dependencies
   - Review user accounts
   - Analyze performance trends
   - Update documentation

#### System Updates

1. **Application Updates**
   ```bash
   # Backup current version
   cp -r /app /app.backup
   
   # Update code
   git pull origin main
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run migrations
   alembic upgrade head
   
   # Restart services
   systemctl restart real-estate-empire
   ```

2. **Security Updates**
   - Monitor security advisories
   - Apply critical patches immediately
   - Test updates in staging environment
   - Schedule maintenance windows

## Backup & Recovery

### Backup Strategy

#### Backup Types

1. **Full Backups**
   - Complete database dump
   - Application files
   - Configuration files
   - User uploads

2. **Incremental Backups**
   - Changed data only
   - Transaction logs
   - File system changes
   - Configuration updates

#### Backup Schedule

```bash
# Backup schedule (crontab)
# Full backup daily at 2 AM
0 2 * * * /scripts/full_backup.sh

# Incremental backup every 4 hours
0 */4 * * * /scripts/incremental_backup.sh

# Configuration backup weekly
0 3 * * 0 /scripts/config_backup.sh
```

### Disaster Recovery

#### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop application
   systemctl stop real-estate-empire
   
   # Restore database
   psql -d real_estate_empire < backup_20240101_020000.sql
   
   # Verify data integrity
   python -c "from app.core.database import engine; print(engine.execute('SELECT COUNT(*) FROM users').scalar())"
   
   # Start application
   systemctl start real-estate-empire
   ```

2. **Full System Recovery**
   - Restore from system image
   - Recover database from backup
   - Restore application files
   - Update configuration
   - Test system functionality

#### Recovery Testing

- **Monthly Recovery Tests**: Test database restore procedures
- **Quarterly DR Tests**: Full disaster recovery simulation
- **Annual DR Review**: Update recovery procedures and documentation

## Compliance & Audit

### Regulatory Compliance

#### GDPR Compliance

1. **Data Subject Rights**
   - Right to access personal data
   - Right to rectification
   - Right to erasure ("right to be forgotten")
   - Right to data portability
   - Right to restrict processing

2. **Implementation**
   ```python
   # Process GDPR request
   from app.services.data_protection_service import DataProtectionService
   
   service = DataProtectionService(db)
   
   # Data access request
   data = service.export_user_data(user_id)
   
   # Data deletion request
   result = service.delete_user_data(user_id)
   ```

#### CCPA Compliance

1. **Consumer Rights**
   - Right to know about data collection
   - Right to delete personal information
   - Right to opt-out of sale of personal information
   - Right to non-discrimination

2. **Privacy Policy Requirements**
   - Clear data collection disclosure
   - Opt-out mechanisms
   - Contact information for privacy requests
   - Regular policy updates

### Audit Management

#### Audit Trail

All system activities are logged:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "user_id": "user123",
  "action": "property_viewed",
  "resource": "property/456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success"
}
```

#### Compliance Reporting

1. **Automated Reports**
   - Security event summaries
   - Data access reports
   - User activity reports
   - System change logs

2. **Manual Reports**
   - Compliance assessments
   - Risk evaluations
   - Incident reports
   - Audit findings

## Performance Optimization

### Database Optimization

#### Query Optimization

1. **Slow Query Analysis**
   ```sql
   -- Enable slow query logging
   SET log_min_duration_statement = 1000;
   
   -- Analyze slow queries
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. **Index Optimization**
   ```sql
   -- Find missing indexes
   SELECT schemaname, tablename, attname, n_distinct, correlation
   FROM pg_stats
   WHERE schemaname = 'public'
   AND n_distinct > 100
   AND correlation < 0.1;
   
   -- Create composite indexes
   CREATE INDEX idx_properties_location_price 
   ON properties(city, state, price);
   ```

#### Connection Pooling

```python
# Database connection pool configuration
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Application Optimization

#### Caching Strategy

1. **Redis Caching**
   ```python
   import redis
   
   # Cache configuration
   cache = redis.Redis(
       host='localhost',
       port=6379,
       db=0,
       decode_responses=True
   )
   
   # Cache property data
   cache.setex(f"property:{property_id}", 3600, json.dumps(property_data))
   ```

2. **Application-Level Caching**
   - Query result caching
   - Computed value caching
   - Static content caching
   - API response caching

#### Load Balancing

```nginx
# Nginx load balancer configuration
upstream real_estate_empire {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://real_estate_empire;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

#### Authentication Problems

1. **Users Cannot Log In**
   - Check user account status
   - Verify password policy compliance
   - Review failed login attempts
   - Check MFA configuration
   - Validate session settings

2. **API Authentication Failures**
   - Verify API key validity
   - Check key permissions
   - Review rate limiting
   - Validate request format

#### Performance Issues

1. **Slow Response Times**
   - Check database performance
   - Review slow query logs
   - Monitor server resources
   - Analyze network latency
   - Check cache hit rates

2. **High Memory Usage**
   - Review connection pool settings
   - Check for memory leaks
   - Monitor background processes
   - Analyze query complexity

#### Data Issues

1. **Data Import Failures**
   - Validate data format
   - Check field mappings
   - Review error logs
   - Verify data sources
   - Test with sample data

2. **Integration Problems**
   - Check API credentials
   - Verify endpoint URLs
   - Review webhook configurations
   - Test connectivity
   - Monitor error rates

### Diagnostic Tools

#### Log Analysis

```bash
# View application logs
tail -f /var/log/real-estate-empire/app.log

# Search for errors
grep -i error /var/log/real-estate-empire/app.log

# Analyze access patterns
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

#### Database Diagnostics

```sql
-- Check database connections
SELECT * FROM pg_stat_activity;

-- Monitor query performance
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Emergency Procedures

#### System Recovery

1. **Service Restart**
   ```bash
   # Restart application
   systemctl restart real-estate-empire
   
   # Restart database
   systemctl restart postgresql
   
   # Restart web server
   systemctl restart nginx
   ```

2. **Emergency Maintenance Mode**
   ```bash
   # Enable maintenance mode
   touch /app/maintenance.flag
   
   # Disable maintenance mode
   rm /app/maintenance.flag
   ```

#### Security Incidents

1. **Suspected Breach**
   - Immediately change all administrative passwords
   - Revoke all API keys
   - Enable additional logging
   - Contact security team
   - Document incident details

2. **Data Corruption**
   - Stop application immediately
   - Assess corruption extent
   - Restore from latest backup
   - Verify data integrity
   - Investigate root cause

---

## Support and Resources

### Documentation
- **API Documentation**: `/docs` (development only)
- **User Guide**: Available in application help
- **Change Log**: Track system updates and changes

### Support Contacts
- **Technical Support**: admin@realestate-empire.com
- **Security Issues**: security@realestate-empire.com
- **Emergency Contact**: +1-800-RE-EMPIRE

### Training Resources
- **Administrator Training**: Monthly webinars
- **Best Practices Guide**: Security and performance tips
- **Community Forum**: Administrator discussion board

---

*This administrator guide is regularly updated. For the latest version and additional resources, visit the admin portal within the application.*