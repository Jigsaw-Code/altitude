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
import { NgxTippyProps } from 'ngx-tippy-wrapper';

import { Priority } from 'src/app/models/priority.model';
import 'src/prisma/components/prisma_badge/prisma-badge';
import { Color } from 'src/prisma/models/color.model';

interface Config {
  label: string;
  color: Color;
}

@Component({
  selector: 'app-priority-badge',
  templateUrl: './priority-badge.component.html',
  styleUrls: ['./priority-badge.component.scss']
})
export class PriorityBadgeComponent {
  /** The priority scores. */
  @Input() priority?: Priority;

  /** Whether the interaction with the badge should be disabled. */
  // TODO: Use `booleanAttribute` once we've upgraded to Angular v16.
  @Input() disabled: boolean | null = false;

  tippyProps: NgxTippyProps = {
    arrow: false,
    allowHTML: true,
    interactive: true,
    interactiveBorder: 50,
    placement: 'bottom'
  };

  get config(): Config {
    switch (this.priority?.level) {
      case 'HIGH':
        return { label: 'High priority', color: 'error' };
      case 'MEDIUM':
        return { label: 'Medium priority', color: 'orange' };
      case 'LOW':
        return { label: 'Low priority', color: 'ocher' };
      default:
        return { label: 'N/A', color: 'neutral-variant' };
    }
  }

  get label(): string {
    return this.config['label'];
  }

  get color(): Color {
    return this.config['color'];
  }
}
