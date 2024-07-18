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

import { TestBed } from '@angular/core/testing';

import { Logger } from './logger.service';

const TEST_MSG = 'TEST';
const TEST_ERROR = new Error('test');

describe('Logger', () => {
  let service: Logger;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [Logger]
    });

    service = TestBed.inject(Logger);
  });

  it('service should be created', () => {
    expect(service).toBeTruthy();
  });

  it('info() should pass on data to `console.log()`', () => {
    const consoleSpy = spyOn(console, 'log');

    service.info(TEST_MSG, TEST_ERROR);

    expect(consoleSpy).toHaveBeenCalledOnceWith(TEST_MSG, TEST_ERROR);
  });

  it('warn() should pass on data to `console.warn()`', () => {
    const consoleSpy = spyOn(console, 'warn');

    service.warn(TEST_MSG, TEST_ERROR);

    expect(consoleSpy).toHaveBeenCalledOnceWith(TEST_MSG, TEST_ERROR);
  });

  it('error() should pass on data to `console.error()`', () => {
    const consoleSpy = spyOn(console, 'error');

    service.error(TEST_MSG, TEST_ERROR);

    expect(consoleSpy).toHaveBeenCalledOnceWith(TEST_MSG, TEST_ERROR);
  });
});
