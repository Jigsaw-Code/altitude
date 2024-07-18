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

import { DefaultToPipe } from './default-to.pipe';
import { SharedModule } from '../shared.module';

describe('defaultTo Pipe', () => {
  let pipe: DefaultToPipe;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule]
    });

    pipe = new DefaultToPipe();
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should not change truthy value', () => {
    expect(pipe.transform('foo bar')).toBe('foo bar');
  });

  it('should change undefined', () => {
    expect(pipe.transform(undefined)).toBe('--');
  });

  it('should change null', () => {
    expect(pipe.transform(null)).toBe('--');
  });

  it('should change empty array', () => {
    expect(pipe.transform([])).toBe('--');
  });

  it('should replace falsy values with provided default value', () => {
    expect(pipe.transform(undefined, 'N/A')).toBe('N/A');
  });
});
