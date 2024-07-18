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

/**
 * Service that serves as a central logger service to collect and broadcast log
 * messages. This provides a unified experience for developers and a consistent way of
 * showing messages to end users (e.g. log versus toast).
 */
@Injectable({
  providedIn: 'root'
})
export class Logger {
  info(msg: string, exception?: Error) {
    console.log(msg, exception);
  }

  warn(msg: string, exception?: Error) {
    console.warn(msg, exception);
  }

  error(msg: string, exception?: Error) {
    console.error(msg, exception);
  }
}
