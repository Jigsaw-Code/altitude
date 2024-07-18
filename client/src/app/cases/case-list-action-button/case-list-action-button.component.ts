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

import { Component, Input, OnInit } from '@angular/core';

import { Color } from 'src/prisma/models/color.model';

@Component({
  selector: 'app-case-list-action-button',
  templateUrl: './case-list-action-button.component.html',
  styleUrls: ['./case-list-action-button.component.scss']
})
export class CaseListActionButtonComponent implements OnInit {
  // TODO: Replace with `required: true` once we've upgraded to Angular v16.
  /** The Material icon symbol to use. */
  @Input() icon!: string;

  @Input() color: Color = 'primary';

  ngOnInit() {
    this.assertRequiredProperty('icon');
  }

  private assertRequiredProperty(name: string) {
    const value = (this as any)[name]; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (value === null || value === undefined) {
      throw Error(`Required property not set: \`${name}\``);
    }
  }
}
