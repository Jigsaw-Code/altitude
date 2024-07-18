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

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Observable, map, mergeMap, tap } from 'rxjs';

import { Logger } from './logger.service';
import { JSONObject } from '../models/case.model';
import { ReviewStats } from '../models/review-stats.model';

/** Denotes the review decisions that can be made. */
export enum ReviewDecisionType {
  BLOCK = 1,
  APPROVE = 2
}

/** Service to create and manage reviews. */
@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  /** Common options to set on HTTP requests. */
  private static readonly OPTIONS = {
    headers: new HttpHeaders().set('Content-Type', 'application/json')
  };

  constructor(
    private readonly http: HttpClient,
    private readonly logger: Logger,
    public snackBar: MatSnackBar
  ) {}

  getReviewStats(): Observable<ReviewStats> {
    return this.http
      .get<JSONObject>('/get_review_stats', ReviewService.OPTIONS)
      .pipe(map(ReviewStats.deserialize));
  }

  private openUndoSnackBar(reviewIds: string[]) {
    const snackBarRef = this.snackBar.open('Review decision saved', 'Undo');

    // Undo button pressed
    snackBarRef
      .onAction()
      .pipe(mergeMap(() => this.delete(reviewIds)))
      .subscribe();
  }

  /**
   * Saves a new Review.
   *
   * Once saved, we present the user with an "UNDO" snackbar popup which would delete
   * the newly created review(s). If not deleted, these draft reviews will be
   * automatically published after 60 seconds by the server.
   *
   * @param caseIds: The IDs of the cases to save the review for.
   * @param decision: The decision made on the provided cases.
   * @returns The IDs of the created reviews.
   */
  save(caseIds: string[], decision: ReviewDecisionType): Observable<string[]> {
    this.logger.info(
      `Saving review decision "${ReviewDecisionType[decision]}" for: ${caseIds}...`
    );

    return this.http
      .post<string[]>(
        '/add_reviews',
        {
          case_ids: caseIds,
          decision: decision
        },
        ReviewService.OPTIONS
      )
      .pipe(
        tap((reviewIds: string[]) => {
          this.logger.info(`Successfully saved reviews for: ${caseIds}`);
          this.openUndoSnackBar(reviewIds);
        })
      );
  }

  /**
   * Deletes a Review.
   *
   * This method is only available for a limited amount of time after the review's
   * creation (~60s) before it is "too late" to delete reviews. After this period of
   * time, these draft reviews are published and the decision will have been delivered
   * to the client platform.
   *
   * @param reviewIds The IDs of the reviews to delete.
   */
  private delete(reviewIds: string[]): Observable<void> {
    this.logger.info(`Deleting review decisions for: ${reviewIds}...`);

    return this.http
      .delete<void>('/remove_reviews', {
        ...ReviewService.OPTIONS,
        body: { review_ids: reviewIds }
      })
      .pipe(
        tap(() => {
          this.logger.info(`Successfully deleted reviews: ${reviewIds}`);
        })
      );
  }
}
