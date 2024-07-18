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

import { ReviewStats } from './review-stats.model';

describe('ReviewStats', () => {
  it('should check deserialize', () => {
    const deserialized = ReviewStats.deserialize({
      count_removed: 1,
      count_approved: 3,
      count_active: 5
    });
    expect(deserialized).toEqual(new ReviewStats(1, 3, 5));
  });
});