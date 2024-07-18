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

import { HttpClientModule } from '@angular/common/http';
import { CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import {
  MAT_SNACK_BAR_DEFAULT_OPTIONS,
  MatSnackBarModule
} from '@angular/material/snack-bar';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { HTTP_INTERCEPTOR_PROVIDERS } from './http-interceptors';
import { RoutingModule } from './routing/routing.module';
import { SharedModule } from './shared/shared.module';

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    HttpClientModule,
    RoutingModule,
    MatCardModule,
    MatCheckboxModule,
    MatDividerModule,
    MatIconModule,
    MatSnackBarModule,
    SharedModule
  ],
  providers: HTTP_INTERCEPTOR_PROVIDERS.concat([
    {
      provide: MAT_SNACK_BAR_DEFAULT_OPTIONS,
      useValue: {
        horizontalPosition: 'start',
        duration: 5_000 // 5 seconds
      }
    }
  ]),
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  bootstrap: [AppComponent]
})
export class AppModule {}
