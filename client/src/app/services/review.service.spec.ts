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

import { HarnessLoader } from '@angular/cdk/testing';
import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
import {
  HttpClientTestingModule,
  HttpTestingController,
  TestRequest
} from '@angular/common/http/testing';
import { Component } from '@angular/core';
import { TestBed, fakeAsync } from '@angular/core/testing';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSnackBarHarness } from '@angular/material/snack-bar/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { ReviewDecisionType, ReviewService } from './review.service';

@Component({ template: `` })
class TestComponent {}

describe('ReviewService', () => {
  let httpTestingController: HttpTestingController;
  let service: ReviewService;
  let loader: HarnessLoader;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        MatSnackBarModule,
        BrowserAnimationsModule
      ],
      declarations: [TestComponent],
      providers: [ReviewService]
    });

    httpTestingController = TestBed.inject(HttpTestingController);
    service = TestBed.inject(ReviewService);
    const fixture = TestBed.createComponent(TestComponent);
    loader = TestbedHarnessEnvironment.documentRootLoader(fixture);
  });

  afterEach(() => {
    // After every test, assert that there are no more pending requests.
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should send a request to get review stats to the API', () => {
    service.getReviewStats().subscribe();

    const request = httpTestingController.expectOne('/get_review_stats');
    expect(request.request.method).toBe('GET');
    request.flush({});
  });

  describe('when a review is made', () => {
    let request: TestRequest;
    let snackBar: MatSnackBarHarness;

    beforeEach(fakeAsync(async () => {
      service.save(['abc'], ReviewDecisionType.BLOCK).subscribe();
      request = httpTestingController.expectOne('/add_reviews');
      request.flush(['review1']);

      snackBar = await loader.getHarness(MatSnackBarHarness);
    }));

    it('should send a request to create the review to the API', () => {
      expect(request.request.method).toBe('POST');
      expect(request.request.body).toEqual({
        case_ids: ['abc'],
        decision: 1
      });
    });

    it('should open "UNDO" snack bar', fakeAsync(async () => {
      expect(snackBar).toBeTruthy();
      expect(await snackBar.getActionDescription()).toBe('Undo');
    }));

    it('should delete a review decision on "UNDO"', fakeAsync(async () => {
      await snackBar.dismissWithAction();

      const deleteRequest = httpTestingController.expectOne('/remove_reviews');
      expect(deleteRequest.request.method).toBe('DELETE');
      expect(deleteRequest.request.body).toEqual({
        review_ids: ['review1']
      });
      deleteRequest.flush(null);
    }));
  });
});
