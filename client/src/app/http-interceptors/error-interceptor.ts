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

import {
  HttpEvent,
  HttpInterceptor,
  HttpHandler,
  HttpRequest,
  HttpErrorResponse
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { Logger } from '../services/logger.service';

/** Intercepts HTTP requests in order to handle any errors. */
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(private readonly logging: Logger) {}

  intercept(
    request: HttpRequest<any>, // eslint-disable-line @typescript-eslint/no-explicit-any
    next: HttpHandler
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      catchError((errorResponse: HttpErrorResponse) => {
        let error: Error;
        let code: number;
        let name: string;
        if (errorResponse.status === 0) {
          // A client-side or network error occurred.
          code = errorResponse.status;
          name = errorResponse.error.type;
          error = new Error(errorResponse.error.type);
        } else {
          // The backend returned an unsuccessful response code.
          code = errorResponse.error.code;
          name = errorResponse.error.name;
          error = new Error(errorResponse.error.description);
        }
        this.logging.error(
          `Request ${request.method} ${request.url} failed: ${code} ${name}`,
          error
        );
        return throwError(() => error);
      })
    );
  }
}
