#!/usr/bin/env bash
# Build the site and sync it to the DO Space (public-read).
#
#   ./deploy.sh          upload changes
#   ./deploy.sh --dry    show what would change, upload nothing
set -euo pipefail

cd "$(dirname "$0")"

BUCKET="wray-family"
REGION="sfo2"
S3="./.venv/bin/s3cmd -c .s3cfg \
  --host=${REGION}.digitaloceanspaces.com \
  --host-bucket=%(bucket)s.${REGION}.digitaloceanspaces.com"

DRY=""
[[ "${1:-}" == "--dry" ]] && DRY="--dry-run" && echo "DRY RUN — nothing will be uploaded."

python3 build.py

# index.html: short cache so edits show up quickly.
$S3 put site/index.html "s3://${BUCKET}/index.html" \
  --acl-public --mime-type=text/html \
  --add-header="Cache-Control: public, max-age=300" $DRY

# materials/: long cache, they rarely change once uploaded.
if [ -n "$(find materials -type f ! -name '.*' -print -quit)" ]; then
  $S3 sync materials/ "s3://${BUCKET}/" \
    --acl-public --guess-mime-type \
    --add-header="Cache-Control: public, max-age=86400" \
    --exclude '.DS_Store' --exclude 'Thumbs.db' \
    --no-delete-removed $DRY
else
  echo "materials/ is empty — skipping file sync."
fi

echo
echo "Live at: https://${BUCKET}.${REGION}.digitaloceanspaces.com/index.html"
