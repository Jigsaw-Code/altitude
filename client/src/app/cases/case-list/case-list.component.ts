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

import { SelectionModel } from '@angular/cdk/collections';
import {
  AfterViewChecked,
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatPaginator } from '@angular/material/paginator';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort } from '@angular/material/sort';
import { Router } from '@angular/router';
import { MdTabs } from '@material/web/tabs/tabs';
import { Observable, ReplaySubject, of } from 'rxjs';
import {
  catchError,
  filter,
  mergeMap,
  single,
  takeUntil
} from 'rxjs/operators';

import { CaseTableDataSource } from './table-data-source';
import { Case } from '../../models/case.model';
import { ReviewStats } from '../../models/review-stats.model';
import { Route } from '../../routing/routes';
import { AutoRefreshService } from '../../services/auto-refresh.service';
import { CaseListNavigator } from '../../services/case-list-navigator.service';
import { CasesService } from '../../services/cases.service';
import { Logger } from '../../services/logger.service';
import {
  ReviewDecisionType,
  ReviewService
} from '../../services/review.service';
import {
  ConfirmDialogComponent,
  ConfirmDialogConfig
} from '../../shared/components/confirm-dialog/confirm-dialog.component';

import 'src/prisma/components/prisma_badge/prisma-badge';
import 'src/prisma/components/prisma_header/prisma_tabs/prisma-tabs';
import 'src/prisma/components/prisma_header/prisma_toolbar/prisma-toolbar';
import 'src/prisma/components/prisma_header/prisma-header';
import 'src/prisma/components/prisma_text/prisma-text';
import { MSG_CONFIG } from 'src/app/admin/config';

const AUTO_REFRESH_INTERVAL_MS = 60_000; // 60 seconds.

interface Tabs {
  headers: {
    active: string;
    removed: string;
    approved: string;
  };
  currentPanel: HTMLElement | null;
}

@Component({
  selector: 'app-case-list',
  templateUrl: './case-list.component.html',
  styleUrls: ['./case-list.component.scss']
})
export class CaseListComponent
  implements OnInit, AfterViewInit, AfterViewChecked, OnDestroy
{
  readonly ReviewDecisionType = ReviewDecisionType;

  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed$ = new ReplaySubject<void>(1);

  readonly reviewStats$: Observable<ReviewStats> = this.reviewService
    .getReviewStats()
    .pipe(
      takeUntil(this.destroyed$),
      single(),
      catchError((error: Error) => {
        this.logging.error(`getReviewStats() failed with error: `, error);
        return of();
      })
    );

  MSG_CONFIG = MSG_CONFIG;

  isLoading = true;
  errorMsg?: string;
  displayedColumns: string[] = [
    'select',
    'content',
    'priority',
    'views',
    'uploadTime',
    'flagger'
  ];

  tabs: Tabs = {
    headers: {
      active: 'Open Cases',
      removed: 'Removed',
      approved: 'Left up'
    },
    currentPanel: null
  };

  /** The data source backing the table. */
  dataSource: CaseTableDataSource;

  /** The selected table items. */
  selection = new SelectionModel<Case>(true, []);

  @ViewChild(MatSort) sort!: MatSort;

  @ViewChild('mdTabs', { read: ElementRef }) mdTabs!: ElementRef;

  @ViewChild(MatPaginator, { static: true }) paginator!: MatPaginator;

  constructor(
    private readonly router: Router,
    private readonly logging: Logger,
    private readonly dialog: MatDialog,
    private readonly snackBar: MatSnackBar,
    private readonly casesService: CasesService,
    private readonly reviewService: ReviewService,
    private readonly autoRefreshService: AutoRefreshService,
    public readonly navigator: CaseListNavigator
  ) {
    this.dataSource = new CaseTableDataSource(
      this.logging,
      this.casesService,
      this.navigator
    );
    this.dataSource.error$
      .pipe(takeUntil(this.destroyed$))
      .subscribe((msg: string | undefined) => {
        if (!msg) {
          return;
        }
        this.snackBar.open(
          'Error loading the cases to review. Please try again later.'
        );
      });

    // Configure the data tables to auto-refresh, as long as the user hasn't selected
    // any rows.
    this.selection.changed.subscribe(() => {
      if (this.selection.selected.length) {
        this.autoRefreshService.stop();
      } else {
        this.autoRefreshService.start(AUTO_REFRESH_INTERVAL_MS);
      }
    });
    this.autoRefreshService.start(AUTO_REFRESH_INTERVAL_MS);
    this.autoRefreshService.refresh$
      .pipe(
        takeUntil(this.destroyed$),
        filter((refresh) => refresh),
        mergeMap(() => this.dataSource.refresh())
      )
      .subscribe();
  }

  ngOnInit() {
    this.reviewStats$.subscribe((reviewStats: ReviewStats) => {
      this.tabs.headers.active += ` (${reviewStats.countActive})`;
      this.tabs.headers.removed += ` (${reviewStats.countRemoved})`;
      this.tabs.headers.approved += ` (${reviewStats.countApproved})`;
    });
  }

  ngAfterViewInit() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  ngAfterViewChecked() {
    if (!this.tabs.currentPanel) {
      // Set the curretly activated panel ID, because md-tabs does not emit a
      // `change` event for the initial auto-activated tab.
      const mdTabsEl = this.mdTabs.nativeElement;
      const currentId = mdTabsEl.activeTab?.getAttribute('aria-controls');
      const root = mdTabsEl.getRootNode() as Document | ShadowRoot;
      this.tabs.currentPanel = root.querySelector<HTMLElement>(`#${currentId}`);
    }
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  updatePanel(event: Event) {
    if (this.tabs.currentPanel) {
      this.tabs.currentPanel.hidden = true;
    }

    const mdTabs = event.target as MdTabs;
    const selectedId = mdTabs.activeTab?.getAttribute('aria-controls');
    const root = mdTabs.getRootNode() as Document | ShadowRoot;
    this.tabs.currentPanel = root.querySelector<HTMLElement>(`#${selectedId}`);

    if (this.tabs.currentPanel) {
      this.tabs.currentPanel.hidden = false;
    }
  }

  /**
   * Returns the sort tooltip message for a specific column header.
   *
   * This depends on the order the header is currently in, i.e. ascending or descending.
   */
  getSortOrderTooltipMsg(column: string): string {
    let ascMsg, descMsg;
    switch (column) {
      case 'uploadTime':
        ascMsg = 'Least recent to most recent';
        descMsg = 'Most recent to least recent';
        break;
      case 'priority':
      case 'views':
      default:
        ascMsg = 'Low to high';
        descMsg = 'High to low';
    }

    if (!this.sort || this.sort.active != column) {
      return descMsg;
    }
    return this.sort.direction == 'asc' ? ascMsg : descMsg;
  }

  /** Whether the number of selected elements matches the total number of rows. */
  isAllSelected(): boolean {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.value.length;
    return numSelected === numRows;
  }

  /** Selects all rows if they are not all selected; otherwise clear selection. */
  toggleAll() {
    this.isAllSelected()
      ? this.selection.clear()
      : this.dataSource.data.value.forEach((row) => this.selection.select(row));
  }

  /**
   * Navigates to a particular case's detail view.
   * NOTE: This is needed because using `routerLink` directly on the row in the
   * template causes tests to fail in unexpected ways.
   */
  navigateTo(row: Case) {
    this.dataSource.loading$.subscribe((loading) => {
      if (loading) {
        return;
      }
      this.router.navigate([Route.CASE_DETAIL, row.id]);
    });
  }

  /**
   * Review the selected cases.
   * @param decision The decision type to record.
   */
  review(decision: ReviewDecisionType) {
    const confirmMsg =
      decision === ReviewDecisionType.BLOCK
        ? `Remove ${this.selection.selected.length} case(s) on platform`
        : `Leave ${this.selection.selected.length} case(s) up on platform`;
    const data: ConfirmDialogConfig = { content: confirmMsg };
    this.dialog
      .open(ConfirmDialogComponent, { data })
      .afterClosed()
      .subscribe((confirm: boolean) => {
        if (!confirm) {
          return;
        }
        this.reviewService
          .save(
            this.selection.selected.map((item: Case) => item.id),
            decision
          )
          .pipe(takeUntil(this.destroyed$))
          .subscribe(() => {
            // TODO: Figure out what to do when reviews has been successfully saved.
            // For now, we refresh the page.
            location.reload();
          });
      });
  }
}
