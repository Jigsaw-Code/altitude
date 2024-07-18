#!/bin/bash
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Utility script to submit all images in a given folder by sending them into the
# the Target REST API.
#
# Example usage:
#
#     bash scripts/submit_image_targets.sh /path/to/dir/with/images my-reference
#
# If you are not running on the default port, remember to override the port here
# as well:
#
#     PORT=1234 bash scripts/submit_image_targets.sh /path/to/dir/with/images my-reference

FILES=$(readlink -m "$1/*")
CONTEXT=$2

for f in $FILES
do
    echo "Submitting $f"
    random_views=$(shuf -i 0-500000 -n 1)
    random_ip=$(printf "%d.%d.%d.%d\n" "$((RANDOM % 256))" "$((RANDOM % 256))" "$((RANDOM % 256))" "$((RANDOM % 256))")
    image_base64=$(base64 -w 0 $f)
    echo 'Submitting {"title": "title", "description": "description", "views": '$random_views', "creator": {"ip_address": "'$random_ip'"}, "client_context": "'$CONTEXT'", "content_type": "IMAGE", "content_bytes": "'${image_base64:0:20}'..."}'

    response=$(echo '{"title": "title", "description": "description", "views": '$random_views', "creator": {"ip_address": "'$random_ip'"}, "client_context": "'$CONTEXT'", "content_type": "IMAGE", "content_bytes": "'$(base64 -w 0 $f)'"}' | \
        curl -s -H "Content-Type: application/json" \
        --data-binary @- "http://localhost:${PORT:-8080}/api/targets/")

    if [[ -z "$response" ]]; then
        echo "No response. Moving on..."
        continue
    fi

    target_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo "Target submitted successfully with ID: $target_id"
done

echo "Done."
