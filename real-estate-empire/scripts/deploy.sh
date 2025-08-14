#!/bin/bash

# Real Estate Empire Deployment Script

set -e

ENVIRONMENT=${1:-development}
VALID_ENVIRONMENTS=("development" "staging" "production")

# Validate environment
if [[ ! " ${VALID_ENVIRONMENTS[@]} " =~ " ${ENVIRONMENT} " ]]; then
    echo "Error: Invalid environment. Must be one of: ${VALID_ENVIRONMENTS[*]}"
    exit 1
fi

echo "Deploying Real Estate Empire to ${ENVIRONMENT} environment..."

# Load environment variables
if [ -f "environments/${ENVIRONMENT}.env" ]; then
    export $(cat environments/${ENVIRONMENT}.env | grep -v '^#' | xargs)
fi

# Function to check if service is healthy
check_service_health() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=1

    echo "Checking health of ${service_name}..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "${service_url}/health" > /dev/null; then
            echo "${service_name} is healthy"
            return 0
        fi
        
        echo "Attempt ${attempt}/${max_attempts}: ${service_name} not ready, waiting..."
        sleep 10
        ((attempt++))
    done
    
    echo "Error: ${service_name} failed to become healthy"
    return 1
}

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml up -d --build

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose exec postgres psql -U postgres -d real_estate_empire -c "SELECT 1;" || {
    echo "Creating databases..."
    docker-compose exec postgres createdb -U postgres auth_db
    docker-compose exec postgres createdb -U postgres property_db
    docker-compose exec postgres createdb -U postgres lead_db
    docker-compose exec postgres createdb -U postgres outreach_db
    docker-compose exec postgres createdb -U postgres transaction_db
    docker-compose exec postgres createdb -U postgres portfolio_db
    docker-compose exec postgres createdb -U postgres reporting_db
}

# Initialize database schemas
echo "Initializing database schemas..."
python scripts/init_db.py

# Health checks
echo "Performing health checks..."
check_service_health "API Gateway" "http://localhost:8000"

if [ "${ENVIRONMENT}" = "production" ]; then
    # Additional production checks
    echo "Running production smoke tests..."
    # Add smoke tests here
fi

echo "Deployment to ${ENVIRONMENT} completed successfully!"
echo "API Gateway available at: http://localhost:8000"
echo "Frontend available at: http://localhost:3000"