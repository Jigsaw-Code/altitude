/**
 * Copyright 2024 Google LLC
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

export interface JSONObject {
  [x: string]: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

/** Converts timestamp strings to `Date` objects recursively in a JSON object. */
export function convertDates(obj: JSONObject) {
  if (obj === null) {
    return;
  }
  Object.keys(obj).forEach((key) => {
    const value = obj[key];
    if (Array.isArray(value)) {
      value.forEach((x) => convertDates(x));
    } else if (typeof value === 'string') {
      if (key.toLowerCase().endsWith('time')) {
        try {
          obj[key] = new Date(value);
        } catch (error) {
          console.error(
            `Unable to convert time entry ${value} to Date object.`
          );
        }
      }
    } else if (typeof value === 'object') {
      convertDates(value);
    }
  });
}
