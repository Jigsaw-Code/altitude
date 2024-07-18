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

import { MatButtonHarness } from '@angular/material/button/testing';
import { MatDialogHarness } from '@angular/material/dialog/testing';

/** Harness for the confirm dialog. */
export class ConfirmDialogHarness extends MatDialogHarness {
  /** The selector for the host element of a `ConfirmDialogComponent` instance. */
  static override hostSelector = 'app-confirm-dialog';

  /** Returns true if there is a `ConfirmDialogComponent` open. */
  static isOpen(): boolean {
    return !!document.querySelector(ConfirmDialogHarness.hostSelector);
  }

  private readonly dialogContentLocator = this.locatorFor('mat-dialog-content');
  private readonly cancelButtonLocator = this.locatorFor(
    MatButtonHarness.with({ text: 'Cancel' })
  );

  private readonly confirmButtonLocator = this.locatorFor(
    MatButtonHarness.with({ text: 'Confirm' })
  );

  async dialogContent(): Promise<string> {
    return this.dialogContentLocator().then((h) => h.text());
  }

  async clickCancel(): Promise<void> {
    return (await this.cancelButtonLocator()).click();
  }

  async clickConfirm(): Promise<void> {
    return (await this.confirmButtonLocator()).click();
  }
}
