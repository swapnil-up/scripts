#!/bin/bash
SECRETS_FILE="$HOME/.config/conky/secrets.env"
if [ ! -f "$SECRETS_FILE" ] || ! file "$SECRETS_FILE" | grep -q text; then
	echo 0
	exit 0
fi
# shellcheck disable=SC1090
source "$SECRETS_FILE"
if [ -z "${GITHUB_USER:-}" ] || [ -z "${GITHUB_TOKEN:-}" ]; then
	echo 0
	exit 0
fi

TODAY=$(date -u +"%Y-%m-%d")
FROM="${TODAY}T00:00:00Z"
TO="${TODAY}T23:59:59Z"

QUERY=$(
	cat <<EOF
{
  "query": "query { user(login: \"$GITHUB_USER\") { contributionsCollection(from: \"$FROM\", to: \"$TO\") { contributionCalendar { totalContributions } } } }"
}
EOF
)

curl -s \
	-H "Authorization: Bearer $GITHUB_TOKEN" \
	-H "Content-Type: application/json" \
	-d "$QUERY" \
	https://api.github.com/graphql |
	jq -r '.data.user.contributionsCollection.contributionCalendar.totalContributions // 0'
