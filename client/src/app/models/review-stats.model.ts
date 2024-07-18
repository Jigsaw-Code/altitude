/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { JSONObject } from './case.model';

/**
 * This represents statistics about the Reviews a User has done.
 */
export class ReviewStats {
  countRemoved: number;
  countApproved: number;
  countActive: number;

  constructor(
    countRemoved: number,
    countApproved: number,
    countActive: number
  ) {
    this.countRemoved = countRemoved;
    this.countApproved = countApproved;
    this.countActive = countActive;
  }

  static deserialize(input: JSONObject): ReviewStats {
    return new ReviewStats(
      input['count_removed'],
      input['count_approved'],
      input['count_active']
    );
  }
}
