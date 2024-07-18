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

import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

/**
 * The configuration that can be passed to the ConfirmDialog component using the
 * Material dialog's `MAT_DIALOG_DATA` API.
 */
export declare interface ConfirmDialogConfig {
  // The text to show in the dialog.
  content: string;
}

@Component({
  selector: 'app-confirm-dialog',
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss']
})
export class ConfirmDialogComponent {
  readonly content: string;

  constructor(
    @Inject(MAT_DIALOG_DATA) data: ConfirmDialogConfig,
    private readonly dialogRef: MatDialogRef<ConfirmDialogComponent>
  ) {
    this.content = data.content;
  }

  /** Closes the dialog with a confirmation value. */
  confirm() {
    this.dialogRef.close(true);
  }
}
