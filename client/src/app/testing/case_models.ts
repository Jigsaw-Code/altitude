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

import { Case, ContentType, State, Source } from '../models/case.model';

/** A basic Case. */
export const CASE = new Case(
  'abc',
  new Date(2000, 12, 25),
  State.ACTIVE,
  { score: 5, level: 'MEDIUM', confidence: 'LOW', severity: undefined },
  [],
  [
    {
      contentValue: 'imagehash123abc',
      contentType: ContentType.HASH_PDQ
    }
  ],
  [
    {
      name: Source.TCAP,
      createTime: new Date(2006, 1, 3),
      tags: ['is_violent_or_graphic']
    },
    {
      name: Source.UNKNOWN,
      createTime: new Date(2006, 1, 20),
      tags: []
    }
  ],
  [],
  'imageBytes_123',
  {},
  'Title',
  'Description',
  5,
  new Date(2005, 10, 12),
  '1.2.3.4',
  'United States',
  [],
  'Hello World'
);

/** A basic image Case. */
export const IMAGE_CASE = new Case(
  'abc',
  new Date(2000, 12, 25),
  State.ACTIVE,
  { score: 2, level: 'MEDIUM', confidence: 'LOW', severity: undefined },
  [],
  [
    {
      contentValue: 'imagehash123abc',
      contentType: ContentType.HASH_PDQ
    }
  ],
  [
    {
      name: Source.TCAP,
      createTime: new Date(2006, 1, 3),
      tags: ['is_violent_or_graphic']
    },
    {
      name: Source.UNKNOWN,
      createTime: new Date(2006, 1, 20),
      tags: []
    }
  ],
  [],
  'imageBytes_123',
  {},
  'Image Title',
  'Description',
  5,
  new Date(2005, 10, 12),
  '1.2.3.4',
  'United States',
  [],
  undefined
);

/** A basic URL Case. */
export const URL_CASE = new Case(
  'def',
  new Date(2000, 12, 25),
  State.ACTIVE,
  { score: 5, level: 'HIGH', confidence: 'HIGH', severity: undefined },
  [],
  [
    {
      contentValue: 'https://abc.xyz/',
      contentType: ContentType.URL
    }
  ],
  [
    {
      name: Source.TCAP,
      createTime: new Date(2006, 1, 3),
      tags: ['is_violent_or_graphic']
    },
    {
      name: Source.UNKNOWN,
      createTime: new Date(2006, 1, 20),
      tags: []
    }
  ],
  [],
  'imageBytes_123',
  {},
  'Url Title',
  'Description',
  5,
  new Date(2004, 3, 30),
  '1.2.3.4',
  'United States',
  [],
  undefined
);
