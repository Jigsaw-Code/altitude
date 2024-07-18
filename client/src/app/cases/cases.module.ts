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

import { CommonModule } from '@angular/common';
import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatRippleModule } from '@angular/material/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { NgxTippyModule } from 'ngx-tippy-wrapper';

import { CaseDetailComponent } from './case-detail/case-detail.component';
import { CaseListComponent } from './case-list/case-list.component';
import { CaseListActionButtonComponent } from './case-list-action-button/case-list-action-button.component';
import { FlaggerComponent } from './flagger/flagger.component';
import { PriorityBadgeComponent } from './priority-badge/priority-badge.component';
import { PriorityCardComponent } from './priority-card/priority-card.component';
import { UploadButtonComponent } from './upload-button/upload-button.component';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [
    CaseDetailComponent,
    CaseListActionButtonComponent,
    CaseListComponent,
    FlaggerComponent,
    PriorityCardComponent,
    PriorityBadgeComponent,
    UploadButtonComponent
  ],
  imports: [
    BrowserAnimationsModule,
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatDialogModule,
    MatDividerModule,
    MatIconModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatRippleModule,
    MatSnackBarModule,
    MatSortModule,
    MatTableModule,
    MatTooltipModule,
    NgxTippyModule,
    ReactiveFormsModule,
    RouterModule,
    SharedModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  exports: [CaseDetailComponent, CaseListComponent]
})
export class CasesModule {}
