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

import { Component, Input } from '@angular/core';

import { Color } from 'src/prisma/models/color.model';

import { Flag, Source } from '../../models/case.model';

import 'src/prisma/components/prisma_label/prisma-label';

@Component({
  selector: 'app-flagger',
  templateUrl: './flagger.component.html',
  styleUrls: ['./flagger.component.scss']
})
export class FlaggerComponent {
  // TODO: Replace with `required: true` once we've upgraded to Angular v16.
  /** The flag to display. */
  @Input() flag!: Flag;

  get displayName(): string {
    if (this.flag.name == Source.USER_REPORT) {
      return 'User Report';
    }
    return this.flag.name;
  }

  get icon(): string | null {
    switch (this.flag.name) {
      case Source.TCAP:
      case Source.GIFCT:
        return 'verified_user';
      case Source.USER_REPORT:
        return 'person';
      default:
        return null;
    }
  }

  get color(): Color {
    switch (this.flag.name) {
      case Source.TCAP:
        return 'pink';
      case Source.GIFCT:
        return 'teal';
      default:
        return 'primary';
    }
  }
}
