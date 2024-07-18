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

/** Level represents the variations of the priority badge. */
export type Level = 'HIGH' | 'MEDIUM' | 'LOW';

/**
 * This interface represents the priority of a Case.
 * @param confidence the confidence of the Case.
 * @param severity the severityof the Case.
 */
export interface Priority {
  score: number | undefined;
  level: Level | undefined;
  confidence: Level | undefined;
  severity: Level | undefined;
}
