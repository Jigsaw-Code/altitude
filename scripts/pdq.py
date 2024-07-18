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

# Utility script to convert an image file to a PDQ hash.
#
# Example usage:
#
#     python scripts/pdq.py /path/to/image

import pdqhash
from PIL import Image
import numpy
import sys

path = sys.argv[1]
array = numpy.asarray(Image.open(path))
hash_vector, quality = pdqhash.compute(array)
bin_str = "".join([str(x) for x in hash_vector])

# binary to hex using format string
# '%0*' is for padding up to ceil(num_bits/4),
# '%X' create a hex representation from the binary string's integer value
hex_str = "%0*X" % ((len(bin_str) + 3) // 4, int(bin_str, 2))
hex_str = hex_str.lower()

print(hex_str)
