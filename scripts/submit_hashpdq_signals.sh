# Copyright 2024 Google LLC
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

# Utility script to submit all provided PDQ hashes by sending them into the
# Signal REST API.
#
# Example usage:
#
#     bash scripts/submit_hashpdq_signals.sh hash1 hash2 hash3
#
# If you are not running on the default port, remember to override the port here
# as well:
#
#     PORT=1234 bash scripts/submit_hashpdq_signals.sh hash1 hash2 hash3

for pdq_digest in "$@"
do
    echo "Submitting hash: $pdq_digest"
    response=$(echo '{"content": {"value": "'$pdq_digest'", "type": "HASH_PDQ"}, "source": {"name": "GIFCT", "author": "JigsawTest Hash Sharing", "create_time": "'$(date -u +"%Y-%m-%dT%H:%M:%S")'"}}' | \
        curl -s -H "Content-Type: application/json" \
        --data-binary @- "http://localhost:${PORT:-8080}/api/signals/")

    if [[ -z "$response" ]]; then
        echo "No response. Moving on..."
        continue
    fi

    signal_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    if [[ -z "$signal_id" ]]; then
        echo "Something went wrong."
        echo $response
        continue
    fi

    echo "Signal submitted successfully with ID: $signal_id"
done

echo "Done."
