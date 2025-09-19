# Quickstart Guide: Scraper SEM Parallèle

**Date**: 2025-09-16  
**Feature**: Scraper SEM Parallèle  
**Purpose**: End-to-end validation of the scraping system

## Prerequisites

### System Requirements
- Python 3.x
- Playwright browser automation
- SQLite database
- VPS environment (Ubuntu recommended)
- MyToolsPlan API access

### Environment Setup
```bash
# Install Python dependencies
pip install playwright fastapi uvicorn sqlite3 asyncio

# Install Playwright browsers
playwright install chromium

# Set up VPS environment
# Ensure proper file permissions and network access

# Database setup
# Production database: /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db (existing)
# Test database: /home/ubuntu/trendtrack-scraper-final/data/trendtrack_test.db (existing)
# Ensure both databases have proper schema and permissions
```

## Quickstart Test Scenarios

### Scenario 1: Basic Website Scraping

**Objective**: Validate end-to-end scraping of a single website

**Steps**:
1. **Add Website**
   ```bash
   curl -X POST http://localhost:8000/websites \
     -H "Content-Type: application/json" \
     -d '{
       "shop_name": "Test Website",
       "shop_url": "https://example.com",
       "project_source": "test"
     }'
   ```

2. **Start Scraping Session**
   ```bash
   curl -X POST http://localhost:8000/scraping/sessions \
     -H "Content-Type: application/json" \
     -d '{
       "session_name": "Quickstart Test",
       "target_status": "pending",
       "worker_count": 1,
       "websites_per_worker": 1
     }'
   ```

3. **Monitor Session Progress**
   ```bash
   # Get session ID from previous response
   curl http://localhost:8000/scraping/sessions/{session_id}/status
   ```

4. **Verify Results**
   ```bash
   # Get website metrics
   curl http://localhost:8000/websites/{website_id}/metrics
   
   # Verify website status updated
   curl http://localhost:8000/websites/{website_id}
   ```

**Expected Results**:
- Website status changes from `pending` to `completed` or `partial`
- Metrics are collected and stored
- Session completes successfully
- All API endpoints return valid responses

### Scenario 2: Parallel Worker Processing

**Objective**: Validate parallel processing of multiple websites

**Steps**:
1. **Add Multiple Websites**
   ```bash
   # Add 5 test websites
   for i in {1..5}; do
     curl -X POST http://localhost:8000/websites \
       -H "Content-Type: application/json" \
       -d "{
         \"shop_name\": \"Test Website $i\",
         \"shop_url\": \"https://example$i.com\",
         \"project_source\": \"test\"
       }"
   done
   ```

2. **Start Parallel Session**
   ```bash
   curl -X POST http://localhost:8000/scraping/sessions \
     -H "Content-Type: application/json" \
     -d '{
       "session_name": "Parallel Test",
       "target_status": "pending",
       "worker_count": 2,
       "websites_per_worker": 3
     }'
   ```

3. **Monitor Parallel Progress**
   ```bash
   # Check session status every 30 seconds
   while true; do
     curl http://localhost:8000/scraping/sessions/{session_id}/status
     sleep 30
   done
   ```

**Expected Results**:
- Multiple workers process websites simultaneously
- Session progress updates in real-time
- All websites are processed within reasonable time
- Worker status shows proper load distribution

### Scenario 3: Error Handling and Recovery

**Objective**: Validate error handling and graceful degradation

**Steps**:
1. **Add Website with Invalid URL**
   ```bash
   curl -X POST http://localhost:8000/websites \
     -H "Content-Type: application/json" \
     -d '{
       "shop_name": "Invalid Website",
       "shop_url": "https://invalid-domain-that-does-not-exist.com",
       "project_source": "test"
     }'
   ```

2. **Start Session with Mixed Websites**
   ```bash
   curl -X POST http://localhost:8000/scraping/sessions \
     -H "Content-Type: application/json" \
     -d '{
       "session_name": "Error Handling Test",
       "target_status": "pending",
       "worker_count": 1,
       "websites_per_worker": 5
     }'
   ```

3. **Verify Error Handling**
   ```bash
   # Check that invalid website gets 'failed' status
   curl http://localhost:8000/websites/{invalid_website_id}
   
   # Check that valid websites still get processed
   curl http://localhost:8000/websites/{valid_website_id}
   ```

**Expected Results**:
- Invalid websites get `failed` status
- Valid websites continue to be processed
- Session completes with partial success
- Error messages are logged appropriately

### Scenario 4: Metric Validation

**Objective**: Validate metric collection and validation logic

**Steps**:
1. **Process Website with Complete Data**
   ```bash
   # Use a known website with good data availability
   curl -X POST http://localhost:8000/websites \
     -H "Content-Type: application/json" \
     -d '{
       "shop_name": "Complete Data Test",
       "shop_url": "https://shopbala.com",
       "project_source": "test"
     }'
   ```

2. **Start Scraping Session**
   ```bash
   curl -X POST http://localhost:8000/scraping/sessions \
     -H "Content-Type: application/json" \
     -d '{
       "session_name": "Metric Validation Test",
       "target_status": "pending",
       "worker_count": 1,
       "websites_per_worker": 1
     }'
   ```

3. **Validate Collected Metrics**
   ```bash
   # Get metrics and verify all 8 metrics are present
   curl http://localhost:8000/websites/{website_id}/metrics
   ```

4. **Verify Status Logic**
   ```bash
   # Check that website status is 'completed' if all metrics present
   curl http://localhost:8000/websites/{website_id}
   ```

**Expected Results**:
- All 8 metrics are collected: organic_traffic, paid_search_traffic, visits, bounce_rate, avg_visit_duration, branded_traffic, conversion_rate, percent_branded_traffic
- Website status is `completed` if all metrics valid
- Website status is `partial` if some metrics missing
- Calculated metrics (percent_branded_traffic) are computed correctly

### Scenario 5: API Contract Validation

**Objective**: Validate all API endpoints work correctly

**Steps**:
1. **Test Website CRUD Operations**
   ```bash
   # Create
   curl -X POST http://localhost:8000/websites -H "Content-Type: application/json" -d '{"shop_name": "CRUD Test", "shop_url": "https://crud-test.com"}'
   
   # Read
   curl http://localhost:8000/websites/{website_id}
   
   # Update
   curl -X PUT http://localhost:8000/websites/{website_id} -H "Content-Type: application/json" -d '{"shop_name": "Updated Name"}'
   
   # Delete
   curl -X DELETE http://localhost:8000/websites/{website_id}
   ```

2. **Test Session Management**
   ```bash
   # List sessions
   curl http://localhost:8000/scraping/sessions
   
   # Get session details
   curl http://localhost:8000/scraping/sessions/{session_id}
   
   # Cancel session
   curl -X DELETE http://localhost:8000/scraping/sessions/{session_id}
   ```

3. **Test Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

**Expected Results**:
- All CRUD operations work correctly
- Proper HTTP status codes returned
- Error responses follow API contract
- Health check returns healthy status

## Performance Validation

### Response Time Requirements
- API endpoints: < 200ms for simple operations
- Website scraping: 1-2 minutes per website
- Session status updates: < 100ms

### Throughput Requirements
- Parallel workers: 2-3 workers processing simultaneously
- API requests: 100+ requests per minute
- Database operations: 1000+ operations per minute

### Reliability Requirements
- API availability: 99%+ uptime
- Scraping success rate: 90%+ for valid websites
- Error recovery: Graceful handling of failures

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check MyToolsPlan credentials
   - Verify cookie synchronization
   - Check network connectivity

2. **Database Errors**
   - Verify SQLite file permissions
   - Check database schema
   - Validate foreign key constraints

3. **Worker Failures**
   - Check browser installation
   - Verify Playwright setup
   - Monitor system resources

4. **API Errors**
   - Check FastAPI server status
   - Verify endpoint contracts
   - Validate request/response formats

### Debug Commands
```bash
# Check system health
curl http://localhost:8000/health

# View recent logs
tail -f logs/scraper.log

# Check production database status
sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db "SELECT COUNT(*) FROM shops;"

# Check test database status
sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack_test.db "SELECT COUNT(*) FROM shops;"

# Compare database schemas
sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db ".schema" > prod_schema.sql
sqlite3 /home/ubuntu/trendtrack-scraper-final/data/trendtrack_test.db ".schema" > test_schema.sql
diff prod_schema.sql test_schema.sql

# Monitor worker processes
ps aux | grep python
```

## Success Criteria

### Functional Validation
- ✅ All 5 test scenarios pass
- ✅ API contracts validated
- ✅ Metric collection works correctly
- ✅ Error handling functions properly

### Performance Validation
- ✅ Response times meet requirements
- ✅ Throughput meets requirements
- ✅ Reliability meets requirements

### Integration Validation
- ✅ MyToolsPlan APIs integrate correctly
- ✅ Database operations work correctly
- ✅ Parallel processing functions correctly
- ✅ User interface responds correctly

---
*Quickstart guide completed: 2025-09-16*
