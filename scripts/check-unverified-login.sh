#!/usr/bin/env bash
# Checks against a running local Supabase that an unverified email cannot log in.
# Usage: supabase start && scripts/check-unverified-login.sh
set -euo pipefail

eval "$(supabase status -o env)"
email="unverified-$(date +%s)@example.com"
password="Correct-Horse-Battery-9"

curl -fsS -X POST "$API_URL/auth/v1/signup" \
  -H "apikey: $ANON_KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$email\",\"password\":\"$password\"}" >/dev/null

body=$(mktemp)
status=$(curl -s -o "$body" -w "%{http_code}" -X POST \
  "$API_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $ANON_KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$email\",\"password\":\"$password\"}")

if [ "$status" != "400" ] || ! grep -q "email_not_confirmed" "$body"; then
  echo "FAIL: expected 400 email_not_confirmed, got HTTP $status: $(cat "$body")" >&2
  exit 1
fi
echo "OK: unverified email rejected (email_not_confirmed)"
