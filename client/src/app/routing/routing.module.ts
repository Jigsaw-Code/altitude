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

import { NgModule } from '@angular/core';
import { RouterModule, Routes, TitleStrategy } from '@angular/router';

import { PageTitleStrategy } from './page-title-strategy.service';
import { caseResolver, caseTitleResolver } from './resolvers';
import { Route } from './routes';
import { AdminModule } from '../admin/admin.module';
import { ImporterConfigComponent } from '../admin/importer-config/importer-config.component';
import { CaseDetailComponent } from '../cases/case-detail/case-detail.component';
import { CaseListComponent } from '../cases/case-list/case-list.component';
import { CasesModule } from '../cases/cases.module';
import { RouteNotFoundComponent } from '../shared/components/route-not-found/route-not-found.component';
import { SharedModule } from '../shared/shared.module';

/** The routes used to configure the router module. */
export const ROUTES: Routes = [
  {
    path: Route.CASE_DETAIL,
    children: [
      {
        path: '',
        redirectTo: `/${Route.CASE_LIST}`,
        pathMatch: 'full'
      },
      {
        path: ':id',
        title: caseTitleResolver,
        component: CaseDetailComponent,
        resolve: { case: caseResolver }
      }
    ]
  },
  {
    path: Route.CASE_LIST,
    component: CaseListComponent
  },
  {
    path: Route.IMPORTERS,
    title: 'Settings',
    component: ImporterConfigComponent
  },
  { path: Route.HOME, redirectTo: Route.CASE_LIST, pathMatch: 'full' },
  { path: '**', component: RouteNotFoundComponent }
];

@NgModule({
  imports: [
    AdminModule,
    CasesModule,
    SharedModule,
    RouterModule.forRoot(ROUTES)
  ],
  exports: [RouterModule],
  providers: [{ provide: TitleStrategy, useClass: PageTitleStrategy }]
})
export class RoutingModule {}
