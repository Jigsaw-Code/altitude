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
export class UploadButtonHarness extends ComponentHarness {
  /** The selector for the host element of a `UploadButtonComponent` instance. */
  static hostSelector = 'app-upload-button';

  private readonly inputLocator = this.locatorFor('input[type="file"]');

  async select(files: File[]) {
    // Build up a DataTransfer object to hold the file data being selected.
    const dataTransfer = new DataTransfer();
    for (const file of files) {
      dataTransfer.items.add(file);
    }

    const input = await this.inputLocator();
    const nativeInput = (input as unknown as { element: HTMLInputElement })
      .element;
    nativeInput.files = dataTransfer.files;
    await input.dispatchEvent('change');
  }
}
