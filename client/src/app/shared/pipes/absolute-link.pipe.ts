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

/**
 * Converts a link to an absolute link.
 *
 * This is needed to force links to open in a new tab.
 */
@Pipe({ name: 'absoluteLink' })
export class AbsoluteLinkPipe implements PipeTransform {
  transform(value: string): string {
    // Force the link to be treated as an absolute path instead of a relative
    // path if it's not already formatted.
    if (!value.startsWith('http')) {
      return '//' + value;
    }
    return value;
  }
}
