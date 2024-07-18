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
import { ComponentFixture, TestBed, fakeAsync } from '@angular/core/testing';
import { MatCheckboxHarness } from '@angular/material/checkbox/testing';
import { MatSortHarness } from '@angular/material/sort/testing';
import { MatTableHarness } from '@angular/material/table/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { of } from 'rxjs';

import { ReviewStats } from 'src/app/models/review-stats.model';
import {
  CaseListNavigator,
  DEFAULT_PAGE_SIZE
} from 'src/app/services/case-list-navigator.service';
import { CasesService, PaginatedCases } from 'src/app/services/cases.service';
import {
  ReviewDecisionType,
  ReviewService
} from 'src/app/services/review.service';
import { ConfirmDialogHarness } from 'src/app/shared/components/confirm-dialog/confirm-dialog.harness';
import { IMAGE_CASE, URL_CASE } from 'src/app/testing/case_models';

import { CaseListComponent } from './case-list.component';
import { CaseListHarness } from './case-list.harness';
import { UploadService } from '../../services/upload.service';
import { CaseListActionButtonHarness } from '../case-list-action-button/case-list-action-button.harness';
import { CasesModule } from '../cases.module';

const CASES = [IMAGE_CASE, URL_CASE];

const REVIEW_STATS: ReviewStats = {
  countRemoved: 1,
  countActive: 2,
  countApproved: 3
};

describe('CaseListComponent', () => {
  let component: CaseListComponent;
  let fixture: ComponentFixture<CaseListComponent>;
  let loader: HarnessLoader;
  let rootLoader: HarnessLoader;
  let mockCasesService: jasmine.SpyObj<CasesService>;
  let mockReviewService: jasmine.SpyObj<ReviewService>;
  let mockUploadService: jasmine.SpyObj<UploadService>;
  let navigator: CaseListNavigator;
  let paginatedCases: PaginatedCases;

  beforeEach(async () => {
    mockCasesService = jasmine.createSpyObj(
      'CasesService',
      Object.getOwnPropertyNames(CasesService.prototype)
    );
    paginatedCases = {
      cases: CASES,
      nextCursorToken: undefined,
      previousCursorToken: undefined,
      totalCount: 2
    };
    mockCasesService.getPendingCases.and.returnValue(of(paginatedCases));
    mockReviewService = jasmine.createSpyObj(
      'ReviewService',
      Object.getOwnPropertyNames(ReviewService.prototype)
    );
    mockReviewService.save.and.returnValue(of());
    mockReviewService.getReviewStats.and.returnValue(of(REVIEW_STATS));
    mockUploadService = jasmine.createSpyObj(
      'ReviewService',
      Object.getOwnPropertyNames(UploadService.prototype)
    );

    await TestBed.configureTestingModule({
      imports: [CasesModule, NoopAnimationsModule],
      providers: [
        {
          provide: CasesService,
          useValue: mockCasesService
        },
        { provide: ReviewService, useValue: mockReviewService },
        { provide: UploadService, useValue: mockUploadService }
      ],
      declarations: [CaseListComponent]
    }).compileComponents();
    navigator = TestBed.inject(CaseListNavigator);
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CaseListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    loader = TestbedHarnessEnvironment.loader(fixture);
    // Dialogs exist outside the host component, so we need a root loader to get
    // harnesses for dialogs.
    rootLoader = TestbedHarnessEnvironment.documentRootLoader(fixture);
  });

  it('should create', fakeAsync(async () => {
    expect(component).toBeTruthy();
    const tableHarness = await loader.getHarness(MatTableHarness);
    expect(await tableHarness.getRows()).toHaveSize(2);
  }));

  it('should display the title', fakeAsync(async () => {
    const tableHarness = await loader.getHarness(MatTableHarness);
    const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
    expect(cellTextByColumnName['content'].text[0]).toContain('Image Title');
  }));

  it('should display the report time in human-readable format', fakeAsync(async () => {
    const tableHarness = await loader.getHarness(MatTableHarness);
    const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
    expect(
      cellTextByColumnName['uploadTime'].text[0].replace(/\s\s+/g, ' ')
    ).toContain('Reported: Feb 03, 2006');
  }));

  it('should display the upload time in human-readable format', fakeAsync(async () => {
    const tableHarness = await loader.getHarness(MatTableHarness);
    const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
    expect(
      cellTextByColumnName['uploadTime'].text[1].replace(/\s\s+/g, ' ')
    ).toContain('Uploaded: Apr 30, 2004');
  }));

  it('should init the navigator with the correct case data', fakeAsync(async () => {
    expect(navigator.previous('abc')).toBeNull();
    expect(navigator.next('abc')).toBe('def');
    expect(navigator.previous('def')).toBe('abc');
    expect(navigator.next('def')).toBeNull();
  }));

  it('should navigate to the detail view when clicking on a row', fakeAsync(async () => {
    const router: Router = TestBed.inject(Router);
    const routerSpy = spyOn(router, 'navigate');
    const tableHarness = await loader.getHarness(MatTableHarness);
    const rows = await tableHarness.getRows();

    await (await rows[1].host()).click();

    expect(routerSpy).toHaveBeenCalledWith(['case', 'def']);
  }));

  describe('when sorting by timestamp', () => {
    let tableHarness: MatTableHarness;

    beforeEach(fakeAsync(async () => {
      tableHarness = await loader.getHarness(MatTableHarness);
      // Verify ordering before we sort.
      const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
      expect(cellTextByColumnName['content'].text[0]).toContain('Image Title');
      expect(cellTextByColumnName['content'].text[1]).toContain('Url Title');

      // Sort by clicking the timestamp header.
      const sortHarness = await loader.getHarness(MatSortHarness);
      const headers = await sortHarness.getSortHeaders({ label: 'Timestamp' });
      await headers[0].click();
    }));

    it('should update the table row order', fakeAsync(async () => {
      const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
      expect(cellTextByColumnName['content'].text[0]).toContain('Url Title');
      expect(cellTextByColumnName['content'].text[1]).toContain('Image Title');
    }));

    it('should update the navigator', fakeAsync(async () => {
      expect(navigator.previous('def')).toBeNull();
      expect(navigator.next('def')).toBe('abc');
      expect(navigator.previous('abc')).toBe('def');
      expect(navigator.next('abc')).toBeNull();
    }));
  });

  it('can sort by complex property `priority.level`', fakeAsync(async () => {
    const tableHarness = await loader.getHarness(MatTableHarness);

    // Verify ordering before we sort.
    const cellTextByColumnName = await tableHarness.getCellTextByColumnName();
    expect(cellTextByColumnName['content'].text[0]).toContain('Image Title');
    expect(cellTextByColumnName['content'].text[1]).toContain('Url Title');

    // Sort in ascending order by clicking the priority header.
    const sortHarness = await loader.getHarness(MatSortHarness);
    const headers = await sortHarness.getSortHeaders({
      label: /Flagger Priority/
    });
    await headers[0].click();

    const updatedCellTextByColumnName =
      await tableHarness.getCellTextByColumnName();
    expect(updatedCellTextByColumnName['content'].text[0]).toContain(
      'Image Title'
    );
    expect(updatedCellTextByColumnName['content'].text[1]).toContain(
      'Url Title'
    );
  }));

  it('should open dialog to confirm bulk action', fakeAsync(async () => {
    const rows = await loader.getAllChildLoaders('table tr[mat-row]');
    const checkbox = await rows[1].getHarness(MatCheckboxHarness);
    await checkbox.toggle();

    const deleteButton = await loader.getHarness(
      CaseListActionButtonHarness.with({ icon: 'delete' })
    );
    await deleteButton.click();

    expect(ConfirmDialogHarness.isOpen()).toBeTrue();
  }));

  it('should send reviews on confirming bulk action', fakeAsync(async () => {
    const rows = await loader.getAllChildLoaders('table tr[mat-row]');
    const checkbox = await rows[1].getHarness(MatCheckboxHarness);
    await checkbox.toggle();

    const deleteButton = await loader.getHarness(
      CaseListActionButtonHarness.with({ icon: 'delete' })
    );
    await deleteButton.click();
    const dialog = await rootLoader.getHarness(ConfirmDialogHarness);
    await dialog.clickConfirm();

    expect(mockReviewService.save).toHaveBeenCalledOnceWith(
      ['def'],
      ReviewDecisionType.BLOCK
    );
  }));

  it(
    'should send reviews for all rows when using the "select all" checkbox ' +
      'with bulk action',
    fakeAsync(async () => {
      const headerRow = await loader.getChildLoader('table tr[mat-header-row]');
      const checkbox = await headerRow.getHarness(MatCheckboxHarness);
      await checkbox.toggle();

      const leaveUpButton = await loader.getHarness(
        CaseListActionButtonHarness.with({ icon: 'select_check_box' })
      );
      await leaveUpButton.click();
      const dialog = await rootLoader.getHarness(ConfirmDialogHarness);
      await dialog.clickConfirm();

      expect(mockReviewService.save).toHaveBeenCalledOnceWith(
        ['abc', 'def'],
        ReviewDecisionType.APPROVE
      );
    })
  );

  it('should not send reviews on canceling bulk action', fakeAsync(async () => {
    const rows = await loader.getAllChildLoaders('table tr[mat-row]');
    const checkbox = await rows[1].getHarness(MatCheckboxHarness);
    await checkbox.toggle();

    const deleteButton = await loader.getHarness(
      CaseListActionButtonHarness.with({ icon: 'delete' })
    );
    await deleteButton.click();
    const dialog = await rootLoader.getHarness(ConfirmDialogHarness);
    await dialog.clickCancel();

    expect(mockReviewService.save).not.toHaveBeenCalled();
  }));

  it('should reload the data table on successful file upload', fakeAsync(async () => {
    const harness = await TestbedHarnessEnvironment.harnessForFixture(
      fixture,
      CaseListHarness
    );
    mockCasesService.getPendingCases.calls.reset();

    await harness.emitUploadEvent();

    expect(mockCasesService.getPendingCases).toHaveBeenCalledOnceWith(
      DEFAULT_PAGE_SIZE,
      undefined,
      undefined
    );
  }));
});
