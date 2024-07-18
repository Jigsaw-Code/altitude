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

import { TestBed, fakeAsync, flush } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { Router, TitleStrategy } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { PageTitleStrategy } from './page-title-strategy.service';

class MockComponent {}

describe('PageTitleStrategy', () => {
  let mockTitle: Title;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule.withRoutes([
          { path: 'route-without-title', component: MockComponent },
          { path: 'route-with-title', component: MockComponent, title: 'Test' }
        ])
      ],
      providers: [
        {
          provide: TitleStrategy,
          useClass: PageTitleStrategy
        }
      ]
    });

    mockTitle = TestBed.inject(Title);
    router = TestBed.inject(Router);
    spyOn(mockTitle, 'setTitle');
  });

  it('should default to "Altitude"', fakeAsync(async () => {
    router.navigate(['route-without-title']);
    flush();

    expect(mockTitle.setTitle).toHaveBeenCalledWith('Altitude');
  }));

  it('should add "Altitude" prefix to defined titles', fakeAsync(async () => {
    router.navigate(['route-with-title']);
    flush();

    expect(mockTitle.setTitle).toHaveBeenCalledWith('Altitude - Test');
  }));
});
