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

import { TestBed } from '@angular/core/testing';

import { CaseListNavigator } from './case-list-navigator.service';

describe('CaseNavigator', () => {
  let service: CaseListNavigator;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [CaseListNavigator]
    });

    service = TestBed.inject(CaseListNavigator);
    service.reset();
  });

  it('service should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should propagate to next case on navigator cases list', () => {
    service.add('1');
    service.add('2');
    service.add('3');
    expect(service.next('3')).toBe(null);
    expect(service.next('1')).toBe('2');
    expect(service.next('2')).toBe('3');
  });

  it('should propagate to previous case on navigator cases list', () => {
    service.add('1');
    service.add('2');
    service.add('3');
    expect(service.previous('2')).toBe('1');
    expect(service.previous('3')).toBe('2');
    expect(service.previous('1')).toBe(null);
  });

  it('should remove a case on navigator cases list', () => {
    service.add('1');
    service.add('2');
    service.add('3');
    service.remove('2');
    expect(service.previous('3')).toBe('1');
  });
});
