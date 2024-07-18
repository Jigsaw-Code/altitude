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
import { MatSnackBar } from '@angular/material/snack-bar';
import {
  NavigationCancel,
  NavigationEnd,
  NavigationError,
  NavigationStart,
  Router,
  RouterEvent
} from '@angular/router';
import { ReplaySubject, takeUntil } from 'rxjs';

import 'src/prisma/components/prisma_icon/prisma-icon';

import { Route } from './routing/routes';
import { Logger } from './services/logger.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnDestroy {
  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed$ = new ReplaySubject<void>(1);

  private static readonly DEFAULT_LOADING_MSG = 'Loading...';

  loading = true;
  loadingMsg: string = AppComponent.DEFAULT_LOADING_MSG;

  constructor(
    private readonly router: Router,
    private readonly logging: Logger,
    private readonly snackBar: MatSnackBar
  ) {
    this.router.events.pipe(takeUntil(this.destroyed$)).subscribe((event) => {
      this.navigationInterceptor(event as RouterEvent);
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  private navigationInterceptor(event: RouterEvent) {
    if (event instanceof NavigationStart) {
      this.loadingMsg = event.url.startsWith(`/${Route.CASE_DETAIL}/`)
        ? 'Loading case...'
        : AppComponent.DEFAULT_LOADING_MSG;
      this.loading = true;
    }

    if (event instanceof NavigationEnd || event instanceof NavigationCancel) {
      this.loading = false;
    }

    if (event instanceof NavigationError) {
      this.loading = false;
      this.snackBar.open('Page not found. Redirecting home.');
      this.router.navigate([Route.HOME]);
    }
  }
}
