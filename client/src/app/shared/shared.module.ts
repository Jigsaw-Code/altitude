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
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';
import * as dayjs from 'dayjs';

import { ConfirmDialogComponent } from './components/confirm-dialog/confirm-dialog.component';
import { ContentDisplayComponent } from './components/content-display/content-display.component';
import { LearnMoreComponent } from './components/learn-more/learn-more.component';
import { LoadingDialogComponent } from './components/loading-dialog/loading-dialog.component';
import { RouteNotFoundComponent } from './components/route-not-found/route-not-found.component';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { AbsoluteLinkPipe } from './pipes/absolute-link.pipe';
import { DefaultToPipe } from './pipes/default-to.pipe';
import { FormatDateAsyncPipe } from './pipes/format-date-async.pipe';
import { DAYJS } from './tokens';

const SHARED_COMPONENTS = [
  AbsoluteLinkPipe,
  ConfirmDialogComponent,
  ContentDisplayComponent,
  DefaultToPipe,
  FormatDateAsyncPipe,
  LearnMoreComponent,
  LoadingDialogComponent,
  RouteNotFoundComponent,
  SidebarComponent
];

@NgModule({
  imports: [
    CommonModule,
    MatButtonModule,
    MatDialogModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    RouterModule
  ],
  declarations: SHARED_COMPONENTS,
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  exports: SHARED_COMPONENTS,
  providers: [{ provide: DAYJS, useFactory: () => dayjs }]
})
export class SharedModule {}
