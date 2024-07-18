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

# Utility script to submit all images in a given folder as hashes by sending them into
# the Signal REST API.
#
# Example usage:
#
#     bash scripts/submit_image_signals.sh /path/to/dir/with/images
#
# If you are not running on the default port, remember to override the port here
# as well:
#
#     PORT=1234 bash scripts/submit_image_signals.sh /path/to/dir/with/images

FILES=$(readlink -m "$1/*")

for f in $FILES
do
    if ! pip3 show Pillow &>/dev/null; then
        echo "Installing Pillow package."
        pip3 install --user Pillow --break-system-packages || exit 1
    fi
    if ! pip3 show pdqhash &>/dev/null; then
        echo "Installing pdqhash package."
        pip3 install --user pdqhash --break-system-packages || exit 1
    fi

    echo "Submitting file: $f"
    pdq_digest=$(python3 scripts/pdq.py $f)
    bash scripts/submit_hashpdq_signals.sh $pdq_digest
done

echo "Done."
