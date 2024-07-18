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

import { HarnessLoader } from '@angular/cdk/testing';
import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync } from '@angular/core/testing';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { ConfirmDialogComponent } from './confirm-dialog.component';
import { ConfirmDialogHarness } from './confirm-dialog.harness';
import { SharedModule } from '../../shared.module';

@Component({ template: `` })
class TestComponent {
  constructor(private readonly dialog: MatDialog) {}

  openDialog(content: string): MatDialogRef<ConfirmDialogComponent> {
    return this.dialog.open(ConfirmDialogComponent, { data: { content } });
  }
}

describe('ConfirmDialogComponent', () => {
  let dialogHost: TestComponent;
  let dialogRef: MatDialogRef<ConfirmDialogComponent>;
  let fixture: ComponentFixture<TestComponent>;
  let loader: HarnessLoader;
  let harness: ConfirmDialogHarness;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SharedModule, MatDialogModule, NoopAnimationsModule],
      declarations: [TestComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    loader = TestbedHarnessEnvironment.documentRootLoader(fixture);
    dialogHost = fixture.componentInstance;
    dialogRef = dialogHost.openDialog('Hello World!');
    fixture.detectChanges();
    harness = await loader.getHarness(ConfirmDialogHarness);
  });

  it('should create', () => {
    expect(dialogHost).toBeTruthy();
  });

  it('should render the provided content in the dialog', async () => {
    expect(await harness.dialogContent()).toBe('Hello World!');
  });

  it('clicking "Cancel" should close the dialog with "false"', fakeAsync(async () => {
    let afterClosedResult = true;
    dialogRef.afterClosed().subscribe((result: boolean) => {
      afterClosedResult = result;
    });
    expect(ConfirmDialogHarness.isOpen()).toBeTrue();

    await harness.clickCancel();

    expect(ConfirmDialogHarness.isOpen()).toBeFalse();
    expect(afterClosedResult).toBe(false);
  }));

  it('clicking "Confirm" should close the dialog with "true"', fakeAsync(async () => {
    let afterClosedResult = false;
    dialogRef.afterClosed().subscribe((result: boolean) => {
      afterClosedResult = result;
    });
    expect(ConfirmDialogHarness.isOpen()).toBeTrue();

    await harness.clickConfirm();

    expect(ConfirmDialogHarness.isOpen()).toBeFalse();
    expect(afterClosedResult).toBe(true);
  }));
});
