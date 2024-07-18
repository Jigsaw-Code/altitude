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
import { Observable, map, tap } from 'rxjs';

import { Logger } from './logger.service';
import { JSONObject, Case } from '../models/case.model';

/**
 * This interface contains the cases to display on page and the tokens for page
 * navigation.
 * @param cases The cases for the current page
 * @param nextCursorToken The token used to navigate to the next page
 * @param previousCursorToken The token used to navigate to the previous page
 * @param totalCount Total number of cases in the database
 */
export interface PaginatedCases {
  cases: Case[];
  nextCursorToken: string | undefined;
  previousCursorToken: string | undefined;
  totalCount: number;
}

@Injectable({
  providedIn: 'root'
})
export class CasesService {
  /** Common options to set on HTTP requests. */
  private static readonly OPTIONS = {
    headers: new HttpHeaders().set('Content-Type', 'application/json')
  };

  constructor(
    private readonly http: HttpClient,
    private readonly logger: Logger
  ) {}

  getCase(id: string): Observable<Case> {
    return this.http
      .get<JSONObject>(`/get_case/${id}`, CasesService.OPTIONS)
      .pipe(map(Case.deserialize));
  }

  getPendingCases(
    page_size: number,
    previous_cursor_token?: string,
    next_cursor_token?: string
  ): Observable<PaginatedCases> {
    const endpoint =
      `/get_cases?page_size=${page_size}` +
      `&next_cursor_token=${next_cursor_token ?? ''}` +
      `&previous_cursor_token=${previous_cursor_token ?? ''}`;

    return this.http.get<JSONObject>(endpoint, CasesService.OPTIONS).pipe(
      map((response) => ({
        cases: response['data'].map(Case.deserialize),
        nextCursorToken: response['next_cursor_token'],
        previousCursorToken: response['previous_cursor_token'],
        totalCount: response['total_count']
      }))
    );
  }

  addNote(caseId: string, notes: string): Observable<boolean> {
    return this.http
      .patch<boolean>(
        '/add_notes',
        {
          case_id: caseId,
          notes: notes
        },
        CasesService.OPTIONS
      )
      .pipe(
        tap(() => {
          this.logger.info(`Successfully added notes for: ${caseId}`);
        })
      );
  }
}
