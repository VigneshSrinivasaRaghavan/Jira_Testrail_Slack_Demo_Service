#!/usr/bin/env bash
# Run from repo root. Makes sequential tests for Jira mock on http://localhost:4001
BASE=http://localhost:4001
AUTH="Authorization: Bearer x"
OUTFILE=./jira_test_output.txt
rm -f "$OUTFILE"
echo "== START: $(date) ==" | tee -a "$OUTFILE"

echo -e "\n-- 1) Health --" | tee -a "$OUTFILE"
curl -s "$BASE/health" | tee -a "$OUTFILE"
echo -e "\n-- end health --\n" | tee -a "$OUTFILE"

echo -e "\n-- 2) GET seeded issue QA-1 --" | tee -a "$OUTFILE"
curl -s -H "$AUTH" -w "\nHTTP_STATUS:%{http_code}\n" "$BASE/rest/api/3/issue/QA-1" | tee -a "$OUTFILE"
echo -e "\n-- end get --\n" | tee -a "$OUTFILE"

echo -e "\n-- 3) SEARCH list --" | tee -a "$OUTFILE"
curl -s -H "$AUTH" -w "\nHTTP_STATUS:%{http_code}\n" "$BASE/rest/api/3/search?startAt=0&maxResults=50" | tee -a "$OUTFILE"
echo -e "\n-- end search --\n" | tee -a "$OUTFILE"

echo -e "\n-- 4) Create via API (JSON) --" | tee -a "$OUTFILE"
API_PAYLOAD='{"fields":{"summary":"Test create from script","description":"from check_jira.sh","issuetype":{"name":"Bug"}}}'
curl -s -X POST "$BASE/rest/api/3/issue" -H "Content-Type: application/json" -H "$AUTH" -d "$API_PAYLOAD" -w "\nHTTP_STATUS:%{http_code}\n" | tee -a "$OUTFILE"
echo -e "\n-- end create api --\n" | tee -a "$OUTFILE"

echo -e "\n-- 5) Create via UI form (server) --" | tee -a "$OUTFILE"
curl -si -X POST "$BASE/ui/create" -F 'summary=FromScript' -F 'description=desc' | tee -a "$OUTFILE"
echo -e "\n-- end create ui --\n" | tee -a "$OUTFILE"

echo -e "\n-- 6) DB inspect (if sqlite3 available locally) --" | tee -a "$OUTFILE"
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 mock-services/jira-mock/jira.db "select id,key,summary from issues order by id;" | tee -a "$OUTFILE"
else
  echo "sqlite3 not found on PATH; skipping DB inspect" | tee -a "$OUTFILE"
fi
echo -e "\n== DONE: $(date) ==" | tee -a "$OUTFILE"
echo "Full output saved to $OUTFILE"