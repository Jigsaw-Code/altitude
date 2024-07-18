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

import {
  HttpClientTestingModule,
  HttpTestingController
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { CasesService } from './cases.service';
import { Case } from '../models/case.model';
import { CASE, IMAGE_CASE } from '../testing/case_models';

describe('CasesService', () => {
  let httpTestingController: HttpTestingController;
  let service: CasesService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CasesService]
    });

    httpTestingController = TestBed.inject(HttpTestingController);
    service = TestBed.inject(CasesService);
  });

  afterEach(() => {
    // After every test, assert that there are no more pending requests.
    httpTestingController.verify();
  });

  it('service should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should retrieve a single case from the API via GET', () => {
    let observedCase: Case = {} as Case;
    service.getCase('abc').subscribe((case1) => {
      observedCase = case1;
    });
    const request = httpTestingController.expectOne('/get_case/abc');
    expect(request.request.method).toBe('GET');

    request.flush(CASE);

    expect(observedCase).toEqual(CASE);
  });

  it('should retrieve multiple cases from the API via GET', () => {
    const mockCases = {
      data: [CASE, IMAGE_CASE],
      nextCursorToken: undefined,
      previousCursorToken: undefined,
      totalCount: 2
    };
    const observedCases: Case[] = [];
    service.getPendingCases(2, undefined, undefined).subscribe((cases) => {
      observedCases.push(...cases['cases']);
    });
    const request = httpTestingController.expectOne(
      '/get_cases?page_size=2&next_cursor_token=&previous_cursor_token='
    );
    expect(request.request.method).toBe('GET');

    request.flush(mockCases);

    expect(observedCases.length).toBe(2);
    expect(observedCases).toEqual(mockCases['data']);
  });

  it('should add note to Case from the API via PATCH', () => {
    service.addNote('abc', 'Hello World').subscribe();
    const request = httpTestingController.expectOne('/add_notes');
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toEqual({
      case_id: 'abc',
      notes: 'Hello World'
    });
    request.flush({});
  });
});
