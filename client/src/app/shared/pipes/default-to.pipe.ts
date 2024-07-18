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

import { Pipe, PipeTransform } from '@angular/core';

/** Converts falsy values to given default value or "--". */
@Pipe({ name: 'defaultTo' })
export class DefaultToPipe implements PipeTransform {
  private static readonly DEFAULT_VALUE = '--';

  transform<T>(
    value: T | null | undefined,
    defaultValue: string = DefaultToPipe.DEFAULT_VALUE
  ): NonNullable<T> | string {
    // Empty array should use default value.
    if (Array.isArray(value) && !value.length) {
      return defaultValue;
    }

    return value || defaultValue;
  }
}
