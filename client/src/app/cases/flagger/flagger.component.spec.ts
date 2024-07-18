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

import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
import { ComponentFixture, TestBed, fakeAsync } from '@angular/core/testing';

import { FlaggerComponent } from './flagger.component';
import { FlaggerHarness } from './flagger.harness';
import { Source } from '../../models/case.model';

describe('FlaggerComponent', () => {
  let component: FlaggerComponent;
  let fixture: ComponentFixture<FlaggerComponent>;
  let harness: FlaggerHarness;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [FlaggerComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(FlaggerComponent);
    component = fixture.componentInstance;
    component.flag = {
      name: Source.TCAP,
      createTime: new Date(),
      tags: []
    };
    fixture.detectChanges();
    harness = await TestbedHarnessEnvironment.harnessForFixture(
      fixture,
      FlaggerHarness
    );
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should specify a display name for user reports', fakeAsync(async () => {
    component.flag.name = Source.USER_REPORT;
    fixture.detectChanges();

    expect(await harness.getDisplayName()).toEqual('User Report');
  }));

  it('should show a verified badge on TCAP', fakeAsync(async () => {
    component.flag.name = Source.TCAP;
    fixture.detectChanges();

    expect(await harness.hasVerifiedBadge()).toBeTrue();
  }));

  it('should not show a verified badge on user reports', fakeAsync(async () => {
    component.flag.name = Source.USER_REPORT;
    fixture.detectChanges();

    expect(await harness.hasVerifiedBadge()).toBeFalse();
  }));
});
