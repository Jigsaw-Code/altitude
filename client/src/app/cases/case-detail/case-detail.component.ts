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

import { Component, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ActivatedRoute, Data, Router } from '@angular/router';
import { Observable, ReplaySubject, of, map, takeUntil, tap } from 'rxjs';
import { catchError, debounceTime, delay, switchMap } from 'rxjs/operators';

import '@material/web/checkbox/checkbox';

import 'src/prisma/components/prisma_action_button/prisma-action-button';
import 'src/prisma/components/prisma_action_rail/prisma-action-rail';
import 'src/prisma/components/prisma_icon/prisma-icon';
import 'src/prisma/components/prisma_text/prisma-text';
import { Route } from 'src/app/routing/routes';

import { Case } from '../../models/case.model';
import { CaseListNavigator } from '../../services/case-list-navigator.service';
import { CasesService } from '../../services/cases.service';
import {
  ReviewDecisionType,
  ReviewService
} from '../../services/review.service';
import { MSG_CONFIG } from 'src/app/admin/config';

enum FormStatus {
  SAVING = 'Saving...',
  SAVED = 'Saved!',
  IDLE = '',
  ERROR = 'Error Saving'
}

@Component({
  selector: 'app-case-detail',
  templateUrl: './case-detail.component.html',
  styleUrls: ['./case-detail.component.scss']
})
export class CaseDetailComponent implements OnDestroy {
  private static readonly DEBOUNCE_TIME = 1000;
  private static readonly SAVE_TIME = 2000;
  readonly ReviewDecisionType = ReviewDecisionType;

  MSG_CONFIG = MSG_CONFIG;

  caseId = '';
  notesControl = new FormControl();
  formStatus: FormStatus = FormStatus.IDLE;

  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed$ = new ReplaySubject<void>(1);

  readonly case$: Observable<Case> = this.activatedRoute.data.pipe(
    map((data: Data) => {
      const activeCase = data['case'];
      return activeCase;
    }),
    tap((case_: Case) => {
      this.caseId = case_.id;
    })
  );

  constructor(
    private readonly router: Router,
    private readonly activatedRoute: ActivatedRoute,
    private readonly reviewService: ReviewService,
    private readonly casesService: CasesService,
    public navigator: CaseListNavigator
  ) {}

  ngOnInit() {
    this.case$.subscribe((case_) => {
      this.notesControl.setValue(case_.notes);
    });

    this.notesControl.valueChanges
      .pipe(
        takeUntil(this.destroyed$),
        tap(() => {
          this.formStatus = FormStatus.SAVING;
        }),
        // Do not emit an event until the form hasn't changed for 1 consecutive
        // second.
        debounceTime(CaseDetailComponent.DEBOUNCE_TIME),
        switchMap((notesValue) =>
          this.casesService.addNote(this.caseId, notesValue)
        ),
        catchError(() => {
          this.formStatus = FormStatus.ERROR;
          return of();
        }),
        tap(() => {
          this.formStatus = FormStatus.SAVED;
        }),
        delay(CaseDetailComponent.SAVE_TIME)
      )
      .subscribe(() => {
        this.formStatus = FormStatus.IDLE;
      });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  /**
   * Reviews the case.
   * @param decision The decision type to record.
   * @param id The identifier of the case for which to record a decision.
   */
  review(decision: ReviewDecisionType) {
    this.reviewService
      .save([this.caseId], decision)
      .pipe(takeUntil(this.destroyed$))
      .subscribe(() => {
        if (!this.navigator.next(this.caseId)) {
          this.router.navigate([Route.CASE_LIST]);
        } else {
          this.navigateNext();
          this.navigator.remove(this.caseId);
        }
      });
  }

  navigateNext() {
    this.router.navigate(['case', this.navigator.next(this.caseId)]);
  }

  navigatePrev() {
    this.router.navigate(['case', this.navigator.previous(this.caseId)]);
  }
}
