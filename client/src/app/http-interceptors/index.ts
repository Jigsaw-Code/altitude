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

import { HTTP_INTERCEPTORS } from '@angular/common/http';
import type { EnvironmentProviders, Provider } from '@angular/core';

import { ApiInterceptor } from './api-interceptor';
import { ErrorInterceptor } from './error-interceptor';

/** Array of HTTP interceptor providers in outside-in order. */
export const HTTP_INTERCEPTOR_PROVIDERS: Array<
  Provider | EnvironmentProviders
> = [
  { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
  { provide: HTTP_INTERCEPTORS, useClass: ApiInterceptor, multi: true }
];
