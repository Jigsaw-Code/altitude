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
  ComponentFixture,
  TestBed,
  fakeAsync,
  flush,
  tick
} from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonHarness } from '@angular/material/button/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import {
  ReviewDecisionType,
  ReviewService
} from 'src/app/services/review.service';
import { URL_CASE } from 'src/app/testing/case_models';

import { CaseDetailComponent } from './case-detail.component';
import { CasesService } from '../../services/cases.service';
import { CasesModule } from '../cases.module';

describe('CaseDetailComponent', () => {
  let component: CaseDetailComponent;
  let fixture: ComponentFixture<CaseDetailComponent>;
  let loader: HarnessLoader;

  let mockReviewService: jasmine.SpyObj<ReviewService>;
  let mockCasesService: jasmine.SpyObj<CasesService>;

  beforeEach(async () => {
    mockReviewService = jasmine.createSpyObj(
      'ReviewService',
      Object.getOwnPropertyNames(ReviewService.prototype)
    );
    mockReviewService.save.and.returnValue(of());

    mockCasesService = jasmine.createSpyObj(
      'CasesService',
      Object.getOwnPropertyNames(CasesService.prototype)
    );
    mockCasesService.addNote.and.returnValue(of());

    await TestBed.configureTestingModule({
      imports: [CasesModule, ReactiveFormsModule],
      declarations: [CaseDetailComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { data: of({ case: URL_CASE }) }
        },
        { provide: ReviewService, useValue: mockReviewService },
        { provide: CasesService, useValue: mockCasesService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CaseDetailComponent);
    loader = TestbedHarnessEnvironment.loader(fixture);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display signal data', () => {
    const element: HTMLElement = fixture.nativeElement.querySelector('.url a');
    expect(element.innerText).toContain('https://abc.xyz/');
  });

  it('should display image preview for URLs', () => {
    const element: HTMLElement = fixture.nativeElement;
    expect(element.getElementsByTagName('iframe')[0]).toBeTruthy();
  });

  it('should save a review decision by calling the ReviewService', fakeAsync(async () => {
    mockReviewService.save.and.returnValue(of());

    const blockButton = await loader.getHarness(
      MatButtonHarness.with({ text: 'delete Remove' })
    );

    await blockButton.click();

    expect(mockReviewService.save).toHaveBeenCalledOnceWith(
      ['def'],
      ReviewDecisionType.BLOCK
    );
    flush();
  }));

  it('should addNote when the text area value changes', fakeAsync(() => {
    const textareaEl =
      fixture.nativeElement.getElementsByTagName('textarea')[0];
    textareaEl.value = 'hello world';
    textareaEl.dispatchEvent(new Event('input'));
    // Wait for 1 second.
    tick(1000);
    expect(mockCasesService.addNote).toHaveBeenCalledOnceWith(
      URL_CASE.id,
      'hello world'
    );
  }));
});
