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

import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

/** Interval after which auto refresh will be triggered. */
export const AUTO_REFRESH_INTERVAL_MS = 60_000; // 60 seconds.

/** Service to provide auto refresh after particular time interval. */
@Injectable({
  providedIn: 'root'
})
export class AutoRefreshService {
  private interval?: number;

  private refresh = new BehaviorSubject<boolean>(false);
  refresh$ = this.refresh.asObservable();

  /** Set automatic data refresh interval. */
  start(delay: number = AUTO_REFRESH_INTERVAL_MS) {
    if (this.interval) {
      this.stop();
    }
    this.interval = window.setInterval(() => {
      this.refresh.next(true);
    }, delay);
  }

  stop() {
    this.refresh.next(false);
    window.clearInterval(this.interval);
  }
}
