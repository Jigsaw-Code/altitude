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

import { DataSource } from '@angular/cdk/collections';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';
import {
  BehaviorSubject,
  combineLatest,
  merge,
  Observable,
  Subject,
  Subscription,
  of
} from 'rxjs';
import { map, mergeMap, tap, catchError, finalize } from 'rxjs/operators';

import { Case } from '../../models/case.model';
import { CaseListNavigator } from '../../services/case-list-navigator.service';
import { CasesService, PaginatedCases } from '../../services/cases.service';
import { Logger } from '../../services/logger.service';

const DEFAULT_ERROR_MSG = 'An unknown error occured.';

/**
 * Data source that loads cases using an external API and includes support of
 * sorting (using MatSort), and pagination (using MatPaginator).
 */
export class CaseTableDataSource<
  P extends MatPaginator = MatPaginator
> extends DataSource<Case> {
  /** Stream emitting data array to the table (depends on ordered data changes). */
  readonly data = new BehaviorSubject<Case[]>([]);

  /** Used to react to internal changes of the paginator that are made by the data source itself. */
  private readonly internalPageChanges = new Subject<void>();

  /**
   * Subscription to the changes that should trigger an update to the table's rendered rows, such
   * as sorting, pagination, or base data changes.
   */
  private renderChangesSubscription: Subscription | null = null;

  private readonly loading = new BehaviorSubject<boolean>(false);
  private readonly error = new BehaviorSubject<string | undefined>(undefined);

  readonly loading$ = this.loading.asObservable();
  readonly error$ = this.error.asObservable();

  private totalCount = 0;

  constructor(
    private readonly logging: Logger,
    private readonly casesService: CasesService,
    private readonly navigator: CaseListNavigator
  ) {
    super();
    this.updateChangeSubscription();
  }

  /**
   * Instance of the MatSort directive used by the table to control its sorting. Sort changes
   * emitted by the MatSort will trigger an update to the table's rendered data.
   */
  get sort(): MatSort | null {
    return this.internalSort;
  }

  set sort(sort: MatSort | null) {
    this.internalSort = sort;
    this.updateChangeSubscription();
  }

  private internalSort: MatSort | null = null;

  /**
   * Instance of the paginator component used by the table to control what page of the data is
   * displayed. Page changes emitted by the paginator will trigger an update to the
   * table's rendered data.
   *
   * Note that the data source uses the paginator's properties to calculate which page of data
   * should be displayed. If the paginator receives its properties as template inputs,
   * e.g. `[pageLength]=100` or `[pageIndex]=1`, then be sure that the paginator's view has been
   * initialized before assigning it to this data source.
   */
  get paginator(): P | null {
    return this.internalPaginator;
  }

  set paginator(paginator: P | null) {
    this.internalPaginator = paginator;
    this.updateChangeSubscription();
  }

  private internalPaginator: P | null = null;

  /**
   * Data accessor function that is used for accessing data properties for sorting through
   * the default sortData function.
   * This function assumes that the sort header IDs (which defaults to the column name)
   * matches the data's properties (e.g. column Xyz represents data['Xyz']).
   * @param data Data object that is being accessed.
   * @param sortHeaderId The name of the column that represents the data.
   */
  private sortingDataAccessor(
    data: Case,
    sortHeaderId: string
  ): string | number {
    switch (sortHeaderId) {
      case 'priority': {
        return data.priority.score ? data.priority.score : 0;
      }
      case 'uploadTime': {
        return data.uploadTime.getTime();
      }
      case 'views': {
        return data.views;
      }
      default: {
        return '';
      }
    }
  }

  /**
   * Gets a sorted copy of the data array based on the state of the MatSort. Called
   *  when sort changes are emitted from MatSort.
   * By default, the function retrieves the active sort and its direction and compares data
   * by retrieving data using the sortingDataAccessor.
   * @param data The array of data that should be sorted.
   */
  private sortData(data: Case[]): Case[] {
    // If there is no active sort or direction, return the data without trying to sort.
    if (!this.sort) {
      return data;
    }
    const active = this.sort.active;
    const direction = this.sort.direction;
    if (!active || direction == '') {
      return data;
    }

    return data.sort((a, b) => {
      let valueA = this.sortingDataAccessor(a, active);
      let valueB = this.sortingDataAccessor(b, active);

      // If there are data in the column that can be converted to a number,
      // it must be ensured that the rest of the data
      // is of the same type so as not to order incorrectly.
      const valueAType = typeof valueA;
      const valueBType = typeof valueB;

      if (valueAType !== valueBType) {
        if (valueAType === 'number') {
          valueA += '';
        }
        if (valueBType === 'number') {
          valueB += '';
        }
      }

      // If both valueA and valueB exist (truthy), then compare the two. Otherwise, check if
      // one value exists while the other doesn't. In this case, existing value should come last.
      // This avoids inconsistent results when comparing values to undefined/null.
      // If neither value exists, return 0 (equal).
      let comparatorResult = 0;
      if (valueA != null && valueB != null) {
        // Check if one value is greater than the other; if equal, comparatorResult should remain 0.
        if (valueA > valueB) {
          comparatorResult = 1;
        } else if (valueA < valueB) {
          comparatorResult = -1;
        }
      } else if (valueA != null) {
        comparatorResult = 1;
      } else if (valueB != null) {
        comparatorResult = -1;
      }

      return comparatorResult * (direction == 'asc' ? 1 : -1);
    });
  }

  /**
   * Subscribe to changes that should trigger an update to the table's rendered rows. When the
   * changes occur, process the current state of sort and pagination along with
   * the provided base data and send it to the table for rendering.
   */
  private updateChangeSubscription() {
    // Sorting and/or pagination should be watched if sort and/or paginator are provided.
    // The events should emit whenever the component emits a change or initializes, or if no
    // component is provided, a stream with just a null event should be provided.
    // The `sortChange` and `pageChange` acts as a signal to the combineLatests below so that the
    // pipeline can progress to the next step. Note that the value from these streams are not used,
    // they purely act as a signal to progress in the pipeline.
    const sortChange: Observable<Sort | null | void> = this.internalSort
      ? (merge(
          this.internalSort.sortChange,
          this.internalSort.initialized
        ) as Observable<Sort | void>)
      : of(null);
    const pageChange: Observable<PageEvent | null | void> = this
      .internalPaginator
      ? (merge(
          this.internalPaginator.page,
          this.internalPageChanges,
          this.internalPaginator.initialized
        ) as Observable<PageEvent | void>)
      : of(null);

    // Watch for page changes to provide a paged set of data.
    const paginatedData: Observable<PaginatedCases> = pageChange.pipe(
      mergeMap(() => this.pageData())
    );
    const orderedData = combineLatest([paginatedData, sortChange]).pipe(
      map(([data]) => this.orderData(data))
    );
    // Watched for paged data changes and send the result to the table to render.
    this.renderChangesSubscription?.unsubscribe();
    this.renderChangesSubscription = orderedData.subscribe(
      (cases: PaginatedCases) => {
        this.data.next(cases['cases']);
        this.totalCount = cases['totalCount'];
        this.updateNavigator(
          cases['previousCursorToken'],
          cases['nextCursorToken']
        );
        this.updatePaginator();
      }
    );
  }

  /**
   * Returns a sorted copy of the data if MatSort has a sort applied, otherwise just
   * returns the originally fetched data array.
   */
  private orderData(data: PaginatedCases): PaginatedCases {
    const sortedCases: Case[] = this.sortData(data['cases'].slice());
    data['cases'] = sortedCases;
    return data;
  }

  /**
   * Returns a paged set of data using pagination cursors provided in previous page
   * fetches.
   */
  private pageData(): Observable<PaginatedCases> {
    if (!this.paginator) {
      return this.loadPage();
    }

    if (this.paginator.pageSize != this.navigator.currentPageSize) {
      // Reset page and pagination tokens so that we return to first page when
      // the page size is updated.
      this.navigator.currentPageIndex = 0;
      this.paginator.pageIndex = 0;
      this.navigator.lastTokens.next = undefined;
      this.navigator.lastTokens.previous = undefined;
      this.navigator.currentPageSize = this.paginator?.pageSize;
      return this.loadPage();
    }

    if (this.paginator.pageIndex > this.navigator.currentPageIndex) {
      return this.loadPage(this.navigator.currentTokens.next).pipe(
        tap(() => {
          this.navigator.currentPageIndex = this.paginator?.pageIndex ?? 0;
          this.navigator.lastTokens.next = this.navigator.currentTokens.next;
          this.navigator.lastTokens.previous = undefined;
        })
      );
    }

    if (this.paginator.pageIndex < this.navigator.currentPageIndex) {
      return this.loadPage(
        undefined,
        this.navigator.currentTokens.previous
      ).pipe(
        tap(() => {
          this.navigator.currentPageIndex = this.paginator?.pageIndex ?? 0;
          this.navigator.lastTokens.previous =
            this.navigator.currentTokens.previous;
          this.navigator.lastTokens.next = undefined;
        })
      );
    }

    return this.refresh();
  }

  /**
   * Updates the navigator to reflect the new dataset of cases.
   * @param previousCursorToken The previous cursor token.
   * @param nextCursorToken The next cursor token.
   */
  private updateNavigator(
    previousCursorToken?: string,
    nextCursorToken?: string
  ) {
    this.navigator.reset();
    for (const case_ of this.data.value) {
      this.navigator.add(case_.id);
    }
    this.navigator.currentTokens.previous = previousCursorToken;
    this.navigator.currentTokens.next = nextCursorToken;
  }

  /**
   * Updates the paginator to reflect the length of the totalCount. Values are changed
   * in a resolved promise to guard against making property changes within a round of
   * change detection.
   */
  private updatePaginator() {
    Promise.resolve().then(() => {
      const paginator = this.paginator;
      if (!paginator) {
        return;
      }
      paginator.length = this.totalCount;
    });
  }

  /**
   * Used by the MatTable. Called when it connects to the data source.
   */
  connect() {
    if (!this.renderChangesSubscription) {
      this.updateChangeSubscription();
    }

    return this.data;
  }

  /**
   * Used by the MatTable. Called when it disconnects from the data source.
   */
  disconnect() {
    this.renderChangesSubscription?.unsubscribe();
    this.renderChangesSubscription = null;
    this.loading.complete();
    this.error.complete();
  }

  /**
   * Fetches pending cases from the server based on specified pagination options.
   */
  private loadPage(
    nextCursorToken?: string,
    previousCursorToken?: string
  ): Observable<PaginatedCases> {
    this.logging.info(
      (this.data.value.length ? 'Reloading' : 'Loading') + ' table data...'
    );
    this.loading.next(true);

    return this.casesService
      .getPendingCases(
        this.paginator?.pageSize ?? 0,
        previousCursorToken,
        nextCursorToken
      )
      .pipe(
        catchError((error: Error) => {
          this.logging.error(`getPendingCases() failed with error: `, error);
          this.loading.next(false);
          this.error.next(error.message || DEFAULT_ERROR_MSG);
          return of();
        }),
        finalize(() => this.loading.next(false))
      );
  }

  refresh(): Observable<PaginatedCases> {
    return this.loadPage(
      this.navigator.lastTokens.next,
      this.navigator.lastTokens.previous
    );
  }
}
