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

import { Inject, OnDestroy, Pipe, PipeTransform } from '@angular/core';
import * as dayjs from 'dayjs';
import * as relativeTime from 'dayjs/plugin/relativeTime';
import { Observable, ReplaySubject, interval } from 'rxjs';
import {
  distinctUntilChanged,
  map,
  startWith,
  takeUntil
} from 'rxjs/operators';

import { DAYJS } from '../tokens';

dayjs.extend(relativeTime);

/** Pipe for displaying formatted timestamp strings with an auto updating interval. */
@Pipe({ name: 'formatDateAsync', pure: true })
export class FormatDateAsyncPipe implements PipeTransform, OnDestroy {
  private static readonly REFRESH_INTERVAL_MS = 15_000; // 15 seconds.

  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed = new ReplaySubject<void>(1);

  constructor(@Inject(DAYJS) private readonly time: typeof dayjs) {}

  ngOnDestroy() {
    this.destroyed.next();
    this.destroyed.complete();
  }

  transform(date?: Date, format?: 'short' | 'long'): Observable<string | null> {
    return interval(FormatDateAsyncPipe.REFRESH_INTERVAL_MS).pipe(
      startWith(0),
      map(() => {
        return format === 'short'
          ? this.formatShortDate(date)
          : this.formatLongDate(date);
      }),
      distinctUntilChanged(),
      takeUntil(this.destroyed)
    );
  }

  /** Returns a short date, relative from now. */
  private formatShortDate(value?: Date): string | null {
    if (!value) {
      return null;
    }
    const now = this.time(new Date().getTime());
    if (now.diff(value, 'day') > 6) {
      return this.time(value).format('MMM DD, YYYY');
    }
    return this.time(value).fromNow();
  }

  /** Returns a long date. */
  private formatLongDate(value?: Date): string | null {
    if (!value) {
      return null;
    }
    return this.time(value).format('MMM DD, YYYY - h:mmA');
  }
}
