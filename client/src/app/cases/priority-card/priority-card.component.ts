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

import { Component, Input, OnChanges, SimpleChange } from '@angular/core';

import { Level } from 'src/app/models/priority.model';

import 'src/prisma/components/prisma_progress_bar/prisma-progress-bar';

interface Score {
  type: string;
  description: string;
  data?: Level;
}

/**
 * Card that visualizes priority score breakdown.
 * @Input confidence Optional normalized confidence score between 0 and 1.
 * @Input severity Optional normalized severity score between 0 and 1.
 */
@Component({
  selector: 'app-priority-card',
  templateUrl: './priority-card.component.html',
  styleUrls: ['./priority-card.component.scss']
})
export class PriorityCardComponent implements OnChanges {
  @Input() label = 'N/A';
  @Input() confidence?: Level = undefined;
  @Input() severity?: Level = undefined;

  scores: Score[] = [
    {
      type: 'Confidence',
      description:
        'Likelihood that this content contains TVEC. Calculated from Flagger data.'
    },
    {
      type: 'Severity',
      description:
        'Threat level or severity of content. Calculated from Flagger data.'
    }
  ];

  ngOnChanges(changes: { [propName: string]: SimpleChange }) {
    if (
      changes['confidence'] &&
      changes['confidence'].currentValue !== changes['confidence'].previousValue
    ) {
      this.scores[0].data = changes['confidence'].currentValue;
    }
    if (
      changes['severity'] &&
      changes['severity'].currentValue !== changes['severity'].previousValue
    ) {
      this.scores[1].data = changes['severity'].currentValue;
    }
  }
}
