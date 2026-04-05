#!/usr/bin/env bash
# Graceful failure test: send bad inputs and verify correct error responses

BASE_URL="${BASE_URL:-http://64.23.146.45:8080}"
PASS=0
FAIL=0

check() {
  local desc="$1"
  local expected="$2"
  local status="$3"
  local body="$4"
  if [ "$status" -eq "$expected" ]; then
    echo "  PASS [$status] $desc"
    echo "         body: $body"
    ((PASS++))
  else
    echo "  FAIL [$status != $expected] $desc"
    echo "         body: $body"
    ((FAIL++))
  fi
}

run() {
  local args=("$@")
  local tmp
  tmp=$(curl -s -w "\n%{http_code}" "${args[@]}")
  local body status
  status=$(echo "$tmp" | tail -n 1)
  body=$(echo "$tmp" | sed '$d')
  echo "$status|$body"
}

# Fire N parallel bad requests to spike WARNING count for alert demo
spam_errors() {
  local n="${1:-20}"
  echo "  [spam] Firing $n parallel bad requests..."
  for i in $(seq 1 $n); do
    curl -s -o /dev/null -X POST "$BASE_URL/users/" \
      -H "Content-Type: application/json" -d '{}' &
    curl -s -o /dev/null "$BASE_URL/users/999999" &
    curl -s -o /dev/null "$BASE_URL/urls/999999" &
  done
  wait
  echo "  [spam] Done"
}

echo "=== Users ==="

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{}')
check "POST /users/ missing username+email → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"username": 123, "email": "a@b.com"}')
check "POST /users/ username is int → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"username": true, "email": "a@b.com"}')
check "POST /users/ username is bool → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"username": null, "email": "a@b.com"}')
check "POST /users/ username is null → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"username": [], "email": "a@b.com"}')
check "POST /users/ username is array → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"email": "a@b.com"}')
check "POST /users/ missing username → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"username": "foo"}')
check "POST /users/ missing email → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run "$BASE_URL/users/999999")
check "GET /users/999999 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run "$BASE_URL/users/0")
check "GET /users/0 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run "$BASE_URL/users/abc")
check "GET /users/abc → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run -X PUT "$BASE_URL/users/999999" -H "Content-Type: application/json" -d '{"username": "ghost"}')
check "PUT /users/999999 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run -X PUT "$BASE_URL/users/999998" -H "Content-Type: application/json" -d '{"username": "ghost"}')
check "PUT /users/999998 → 404" 404 "${result%%|*}" "${result#*|}"

tmp_id=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"username":"__badtest__","email":"__badtest__@x.com"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

if [ -n "$tmp_id" ]; then
  result=$(run -X PUT "$BASE_URL/users/$tmp_id" -H "Content-Type: application/json" -d '{"username": 42}')
  check "PUT /users/:id username is int → 422" 422 "${result%%|*}" "${result#*|}"

  result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" \
    -d "{\"username\":\"__badtest__\",\"email\":\"other@x.com\"}")
  check "POST /users/ duplicate username → 409" 409 "${result%%|*}" "${result#*|}"

  result=$(run -X POST "$BASE_URL/users/" -H "Content-Type: application/json" \
    -d "{\"username\":\"other\",\"email\":\"__badtest__@x.com\"}")
  check "POST /users/ duplicate email → 409" 409 "${result%%|*}" "${result#*|}"

  curl -s -o /dev/null -X DELETE "$BASE_URL/users/$tmp_id"
fi

echo ""
echo "=== URLs ==="

result=$(run -X POST "$BASE_URL/urls/" -H "Content-Type: application/json" -d '{"user_id": 1}')
check "POST /urls/ missing original_url → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/urls/" -H "Content-Type: application/json" -d '{"original_url": "https://example.com"}')
check "POST /urls/ missing user_id → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/urls/" -H "Content-Type: application/json" -d '{}')
check "POST /urls/ empty body → 422" 422 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/urls/" -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com", "user_id": 999999}')
check "POST /urls/ user not found → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/urls/" -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com", "user_id": 999998}')
check "POST /urls/ user 999998 not found → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run "$BASE_URL/urls/999999")
check "GET /urls/999999 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run "$BASE_URL/urls/0")
check "GET /urls/0 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run -X PUT "$BASE_URL/urls/999999" -H "Content-Type: application/json" -d '{"title": "ghost"}')
check "PUT /urls/999999 → 404" 404 "${result%%|*}" "${result#*|}"

result=$(run -X PUT "$BASE_URL/urls/999998" -H "Content-Type: application/json" -d '{"title": "ghost"}')
check "PUT /urls/999998 → 404" 404 "${result%%|*}" "${result#*|}"

echo ""
echo "=== Bulk import ==="

result=$(run -X POST "$BASE_URL/users/bulk")
check "POST /users/bulk no file → 400" 400 "${result%%|*}" "${result#*|}"

result=$(run -X POST "$BASE_URL/users/bulk" -F "file=@/dev/stdin;filename=empty.csv" <<< "username,email")
check "POST /users/bulk empty CSV → 200" 200 "${result%%|*}" "${result#*|}"

echo ""
echo "=== Spam phase (triggering High Error Rate alert) ==="
spam_errors 20

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
