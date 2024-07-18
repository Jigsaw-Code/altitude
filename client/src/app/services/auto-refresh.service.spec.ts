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

import {
  TestBed,
  discardPeriodicTasks,
  fakeAsync,
  tick
} from '@angular/core/testing';

import { AutoRefreshService } from './auto-refresh.service';

describe('AutoRefreshService', () => {
  let service: AutoRefreshService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [AutoRefreshService]
    });

    service = TestBed.inject(AutoRefreshService);
  });

  it('service should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should set refresh to true after specified interval', fakeAsync(() => {
    service.start(2_000);
    tick(2_000);

    service.refresh$.subscribe((refresh) => {
      expect(refresh).toEqual(true);
    });
    discardPeriodicTasks();
  }));

  it('should set refresh to false on stopping the interval', () => {
    service.stop();

    service.refresh$.subscribe((refresh) => {
      expect(refresh).toEqual(false);
    });
  });
});
