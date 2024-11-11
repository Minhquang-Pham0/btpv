#!/bin/bash

# Base URL for the API
BASE_URL="http://localhost:8000/api/v1"

# Function to check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        echo "jq is required but not installed. Please install jq first."
        exit 1
    fi
}

# Function to make API calls and handle errors
api_call() {
    local response=$(curl -s "$@")
    if [ $? -ne 0 ]; then
        echo "Error making API call"
        exit 1
    fi
    echo "$response"
}

# Main testing sequence
main() {
    check_jq

    echo "Testing Password Vault API"
    echo "-------------------------"

    # 1. Register user
    echo "1. Registering new user..."
    api_call -X POST "${BASE_URL}/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!"
        }' | jq '.'

    # 2. Login
    echo "2. Logging in..."
    LOGIN_RESPONSE=$(api_call -X POST "${BASE_URL}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=testuser&password=Test123!")
    TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
    
    if [ -z "$TOKEN" ]; then
        echo "Failed to get authentication token"
        exit 1
    fi

    AUTH_HEADER="Authorization: Bearer $TOKEN"

    # 3. Create group
    echo "3. Creating group..."
    GROUP_RESPONSE=$(api_call -X POST "${BASE_URL}/groups" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d '{
            "name": "Personal Passwords",
            "description": "My personal password collection"
        }')
    GROUP_ID=$(echo $GROUP_RESPONSE | jq -r '.id')

    # 4. List groups
    echo "4. Listing groups..."
    api_call -X GET "${BASE_URL}/groups" \
        -H "$AUTH_HEADER" | jq '.'

    # 5. Create password
    echo "5. Creating password entry..."
    api_call -X POST "${BASE_URL}/passwords" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "{
            \"title\": \"GitHub Account\",
            \"username\": \"gituser\",
            \"password\": \"MyGitPass123!\",
            \"url\": \"https://github.com\",
            \"notes\": \"Main GitHub account\",
            \"group_id\": $GROUP_ID
        }" | jq '.'

    # 6. List passwords
    echo "6. Listing passwords..."
    api_call -X GET "${BASE_URL}/passwords/group/${GROUP_ID}" \
        -H "$AUTH_HEADER" | jq '.'

    # 7. Generate password
    echo "7. Generating random password..."
    api_call -X POST "${BASE_URL}/passwords/generate" \
        -H "$AUTH_HEADER" \
        -d "length=16" | jq '.'

    echo "8. Get Logs"
    api_call -X GET "${BASE_URL}/logs" \
        -H "$AUTH_HEADER" | jq '.'

    echo "8. Get Logs by group id"
    api_call -X GET "${BASE_URL}/logs/group/${GROUP_ID}" \
        -H "$AUTH_HEADER" | jq '.'
}

main
