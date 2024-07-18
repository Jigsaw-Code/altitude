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

import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {
  intercept(
    request: HttpRequest<any>, // eslint-disable-line @typescript-eslint/no-explicit-any
    next: HttpHandler
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): Observable<HttpEvent<any>> {
    // Clone the request and prefix the URL with the appropriate API subpath.
    const redirectRequest = request.clone({
      url: './data' + request.url
    });
    return next.handle(redirectRequest);
  }
}
