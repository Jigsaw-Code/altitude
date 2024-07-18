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

import { JSONObject, convertDates } from './date-utils';

describe('DateUtils', () => {
  it('converts date strings to Date objects recursively', () => {
    const data: JSONObject = {
      createTime: '2022-12-01T06:30:58',
      notATimeStamp: 'foobar',
      subPath: {
        someOtherTime: '2022-03-25T12:03:44'
      }
    };

    convertDates(data);

    expect(data['createTime']).toEqual(new Date(2022, 11, 1, 6, 30, 58));
    expect(data['notATimeStamp']).toEqual('foobar');
    expect(data['subPath']['someOtherTime']).toEqual(
      new Date(2022, 2, 25, 12, 3, 44)
    );
  });
});
