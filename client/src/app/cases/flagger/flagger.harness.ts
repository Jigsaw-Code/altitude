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

import { ComponentHarness } from '@angular/cdk/testing';

/** Harness for the upload button. */
export class FlaggerHarness extends ComponentHarness {
  /** The selector for the host element of a `FlaggerComponent` instance. */
  static hostSelector = 'app-flagger';

  private readonly nameLocator = this.locatorFor('prisma-text');
  private readonly badgeLocator = this.locatorForOptional('prisma-icon');

  async getDisplayName(): Promise<string> {
    return this.nameLocator().then((h) => h.text());
  }

  async hasVerifiedBadge(): Promise<boolean> {
    return this.badgeLocator()
      .then((h) => h?.text())
      .then((t) => t === 'verified_user');
  }
}
