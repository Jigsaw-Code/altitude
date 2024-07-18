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

import { HTTP_INTERCEPTORS, HttpClient } from '@angular/common/http';
import {
  HttpClientTestingModule,
  HttpTestingController
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ErrorInterceptor } from './error-interceptor';
import { Logger } from '../services/logger.service';

describe('ErrorInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let logger: Logger;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        {
          provide: HTTP_INTERCEPTORS,
          useClass: ErrorInterceptor,
          multi: true
        }
      ]
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    logger = TestBed.inject(Logger);
  });

  it('logs an client error if HTTP request fails', () => {
    const logSpy = spyOn(logger, 'error');
    const errorHandlerSpy = jasmine.createSpy('error handler');
    httpClient.get('/foo/bar').subscribe({ error: errorHandlerSpy });

    httpMock.expectOne('/foo/bar').error(new ProgressEvent('test'));

    expect(logSpy).toHaveBeenCalledOnceWith(
      'Request GET /foo/bar failed: 0 test',
      new Error('test')
    );
  });

  it('logs a server error if HTTP request fails', () => {
    const logSpy = spyOn(logger, 'error');
    const errorHandlerSpy = jasmine.createSpy('error handler');
    httpClient.get('/foo/bar').subscribe({ error: errorHandlerSpy });

    httpMock.expectOne('/foo/bar').flush(
      {
        code: 404,
        name: 'Not Found',
        description: 'Resource not found'
      },
      { status: 404, statusText: 'test' }
    );

    expect(logSpy).toHaveBeenCalledOnceWith(
      'Request GET /foo/bar failed: 404 Not Found',
      new Error('Resource not found')
    );
  });
});
