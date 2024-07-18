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
  BaseHarnessFilters,
  ComponentHarness,
  HarnessPredicate
} from '@angular/cdk/testing';
import { MatButtonHarness } from '@angular/material/button/testing';

/**
 * A set of criteria that can be used to filter a list of case list action
 * harness instances.
 */
export interface CaseListActionButtonHarnessFilters extends BaseHarnessFilters {
  /** Only find instances whose icon matches the given value. */
  icon?: string | RegExp;
}

/** Harness for the confirm dialog. */
export class CaseListActionButtonHarness extends ComponentHarness {
  /** The selector for the host element of a `CaseListActionButton` instance. */
  static hostSelector = 'app-case-list-action-button';

  private readonly buttonLocator = this.locatorFor(MatButtonHarness);

  /**
   * Gets a `HarnessPredicate` that can be used to search for a
   * `CaseListActionButtonHarness` that meets certain criteria.
   * @param options Options for filtering which survey question instances are
   *     considered a match.
   * @return a `HarnessPredicate` configured with the given options.
   */
  static with(
    options: CaseListActionButtonHarnessFilters = {}
  ): HarnessPredicate<CaseListActionButtonHarness> {
    return new HarnessPredicate(CaseListActionButtonHarness, options).addOption(
      'icon',
      options.icon,
      (harness, icon) => HarnessPredicate.stringMatches(harness.getIcon(), icon)
    );
  }

  /** Gets a promise for the button's label text. */
  async getIcon(): Promise<string | null> {
    return (await this.host()).getAttribute('icon');
  }

  async click(): Promise<void> {
    return (await this.buttonLocator()).click();
  }
}
