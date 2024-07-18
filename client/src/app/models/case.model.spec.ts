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

import { ContentType, Case, Source, Likelihood, State } from './case.model';
import { IMAGE_CASE, URL_CASE } from '../testing/case_models';

describe('Case', () => {
  it('should check if ContentType is not url', () => {
    expect(IMAGE_CASE.isTypeUrl()).toBeFalse();
  });

  it('should check if ContentType is url', () => {
    expect(URL_CASE.isTypeUrl()).toBeTrue();
  });

  it('should deserialize correctly', () => {
    const deserialized = Case.deserialize({
      analysis: {
        safeSearchScores: {
          adult: 'POSSIBLE',
          medical: 'POSSIBLE',
          racy: 'POSSIBLE',
          spoof: 'POSSIBLE',
          violence: 'POSSIBLE'
        }
      },
      createTime: '2001-01-25T00:00:00',
      id: 'abc',
      reviewHistory: [],
      signalContent: [
        {
          contentValue: 'https://abc.xyz/',
          contentType: ContentType.URL
        }
      ],
      flags: [
        {
          name: 'TCAP',
          createTime: '2000-12-25T00:00:00',
          tags: ['is_violent_or_graphic']
        },
        {
          name: 'UNKNOWN',
          createTime: '2000-12-27T00:00:00',
          tags: ['is_violent_or_graphic']
        }
      ],
      associatedEntities: [],
      imageBytes: 'image_data_bytes_123',
      state: 'ACTIVE',
      priority: {
        score: 2,
        level: 'LOW',
        confidence: 'MEDIUM',
        severity: undefined
      },
      title: 'Title',
      description: 'Description',
      views: 5,
      uploadTime: '2001-12-25T00:00:00',
      ipAddress: '1.2.3.4',
      ipRegion: 'United States',
      similarCaseIds: [],
      notes: undefined
    });

    expect(deserialized).toBeInstanceOf(Case);
    expect(deserialized.id).toBe('abc');
    expect(deserialized.createTime).toEqual(new Date(2001, 0, 25));
    expect(deserialized.state).toBe(State.ACTIVE);
    expect(deserialized.priority).toEqual({
      score: 2,
      level: 'LOW',
      confidence: 'MEDIUM',
      severity: undefined
    });
    expect(deserialized.reviewHistory).toEqual([]);
    expect(deserialized.signalContent).toEqual([
      {
        contentValue: 'https://abc.xyz/',
        contentType: ContentType.URL
      }
    ]);
    expect(deserialized.flags).toEqual([
      {
        name: Source.TCAP,
        createTime: new Date(2000, 11, 25),
        tags: ['is_violent_or_graphic']
      },
      {
        name: Source.UNKNOWN,
        createTime: new Date(2000, 11, 27),
        tags: ['is_violent_or_graphic']
      }
    ]);
    expect(deserialized.associatedEntities).toEqual([]);
    expect(deserialized.imageBytes).toBe('image_data_bytes_123');
    expect(deserialized.analysis).toEqual({
      safeSearchScores: {
        adult: Likelihood.POSSIBLE,
        medical: Likelihood.POSSIBLE,
        racy: Likelihood.POSSIBLE,
        spoof: Likelihood.POSSIBLE,
        violence: Likelihood.POSSIBLE
      }
    });
    expect(deserialized.title).toBe('Title');
    expect(deserialized.description).toBe('Description');
    expect(deserialized.views).toBe(5);
    expect(deserialized.uploadTime).toEqual(new Date(2001, 11, 25));
    expect(deserialized.ipAddress).toBe('1.2.3.4');
    expect(deserialized.ipRegion).toBe('United States');
    expect(deserialized.similarCaseIds).toEqual([]);
    expect(deserialized.notes).toEqual(undefined);
  });
});
