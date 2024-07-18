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

import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { LoadingDialogComponent } from './loading-dialog.component';
import { LoadingDialogHarness } from './loading-dialog.harness';
import { SharedModule } from '../../shared.module';

@Component({ template: `` })
class TestComponent {
  constructor(private readonly dialog: MatDialog) {}

  openDialog(): MatDialogRef<LoadingDialogComponent> {
    return this.dialog.open(LoadingDialogComponent);
  }
}

describe('LoadingDialogComponent', () => {
  let dialogHost: TestComponent;
  let fixture: ComponentFixture<TestComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SharedModule, MatDialogModule, NoopAnimationsModule],
      declarations: [TestComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    dialogHost = fixture.componentInstance;
    dialogHost.openDialog();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(dialogHost).toBeTruthy();
    expect(LoadingDialogHarness.isOpen()).toBeTrue();
  });
});
