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

import { Location, LocationStrategy } from '@angular/common';
import { MockLocationStrategy } from '@angular/common/testing';
import { Component, ViewChild } from '@angular/core';
import {
  TestBed,
  discardPeriodicTasks,
  fakeAsync,
  tick
} from '@angular/core/testing';
import { Router, RouterOutlet } from '@angular/router';
import { NEVER, of } from 'rxjs';

import { RoutingModule } from './routing.module';
import { CaseDetailComponent } from '../cases/case-detail/case-detail.component';
import { CaseListComponent } from '../cases/case-list/case-list.component';
import { CasesService, PaginatedCases } from '../services/cases.service';
import { ReviewService } from '../services/review.service';
import { UploadService } from '../services/upload.service';

/** Component used to set up routing tests. */
@Component({
  template: '<router-outlet></router-outlet>'
})
class RoutingTestComponent {
  @ViewChild(RouterOutlet, { static: false }) routerOutlet!: RouterOutlet;
}

describe('RoutingModule', () => {
  let router: Router;
  let location: Location;
  let routerOutlet: RouterOutlet;

  beforeEach(async () => {
    const mockCasesService = jasmine.createSpyObj(
      'CasesService',
      Object.getOwnPropertyNames(CasesService.prototype)
    );
    mockCasesService.getCase.and.returnValue(of({}));
    const paginatedCases: PaginatedCases = {
      cases: [],
      nextCursorToken: undefined,
      previousCursorToken: undefined,
      totalCount: 0
    };
    mockCasesService.getPendingCases.and.returnValue(of(paginatedCases));

    const mockReviewService = jasmine.createSpyObj(
      'ReviewService',
      Object.getOwnPropertyNames(ReviewService.prototype)
    );
    mockReviewService.getReviewStats.and.returnValue(NEVER);
    const mockUploadService = jasmine.createSpyObj(
      'UploadService',
      Object.getOwnPropertyNames(UploadService.prototype)
    );

    await TestBed.configureTestingModule({
      imports: [RoutingModule],
      declarations: [RoutingTestComponent],
      providers: [
        {
          provide: LocationStrategy,
          useClass: MockLocationStrategy
        },
        {
          provide: CasesService,
          useValue: mockCasesService
        },
        {
          provide: ReviewService,
          useValue: mockReviewService
        },
        {
          provide: UploadService,
          useValue: mockUploadService
        }
      ]
    });
    const fixture = TestBed.createComponent(RoutingTestComponent);
    fixture.detectChanges();
    routerOutlet = fixture.componentInstance.routerOutlet;
    router = TestBed.inject(Router) as Router;
    location = TestBed.inject(Location) as Location;
  });

  it('routes `/` to `/cases`', fakeAsync(() => {
    router.navigateByUrl('/');

    tick();

    expect(location.path()).toBe('/cases');
    discardPeriodicTasks();
  }));

  it('routes `/cases` to the cases list', fakeAsync(() => {
    router.navigateByUrl('/cases');

    tick();

    expect(routerOutlet.component).toBeInstanceOf(CaseListComponent);
    discardPeriodicTasks();
  }));

  it('routes `/case/{id}` to a case detail view', fakeAsync(() => {
    router.navigateByUrl('/case/abc');

    tick();

    expect(routerOutlet.component).toBeInstanceOf(CaseDetailComponent);
  }));
});
