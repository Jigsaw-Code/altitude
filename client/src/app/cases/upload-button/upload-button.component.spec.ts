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
import {
  ComponentFixture,
  TestBed,
  discardPeriodicTasks,
  fakeAsync,
  flush,
  tick
} from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { first, of } from 'rxjs';

import { UploadService } from 'src/app/services/upload.service';

import { UploadButtonComponent } from './upload-button.component';
import { UploadButtonHarness } from './upload-button.harness';
import { CasesModule } from '../cases.module';

describe('UploadButtonComponent', () => {
  let component: UploadButtonComponent;
  let fixture: ComponentFixture<UploadButtonComponent>;
  let harness: UploadButtonHarness;
  let mockUploadService: jasmine.SpyObj<UploadService>;

  beforeEach(async () => {
    mockUploadService = jasmine.createSpyObj(
      'ReviewService',
      Object.getOwnPropertyNames(UploadService.prototype)
    );

    await TestBed.configureTestingModule({
      imports: [CasesModule, NoopAnimationsModule],
      declarations: [UploadButtonComponent],
      providers: [{ provide: UploadService, useValue: mockUploadService }]
    }).compileComponents();

    fixture = TestBed.createComponent(UploadButtonComponent);
    fixture.detectChanges();
    component = fixture.componentInstance;
    harness = await TestbedHarnessEnvironment.harnessForFixture(
      fixture,
      UploadButtonHarness
    );
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should send selected fils to the upload service', fakeAsync(async () => {
    mockUploadService.uploadImage.and.returnValues(of(true), of(false));

    const file1 = new File(['this is file1!'], 'filename1');
    const file2 = new File(['this is file2!'], 'filename2');
    await harness.select([file1, file2]);

    expect(mockUploadService.uploadImage).toHaveBeenCalledWith(file1);
    expect(mockUploadService.uploadImage).toHaveBeenCalledWith(file2);
    discardPeriodicTasks();
  }));

  it('should emit an `upload` event when a file has been successfully uploaded', fakeAsync(async () => {
    mockUploadService.uploadImage.and.returnValues(of(true), of(false));
    let upload: boolean | undefined;
    component.upload
      .pipe(first())
      .subscribe((success: boolean) => (upload = success));

    await harness.select([
      new File(['this is file1!'], 'filename1'),
      new File(['this is file2!'], 'filename2')
    ]);
    tick(UploadButtonComponent.MIN_LOADING_TIME_MS);

    expect(upload).toBeTrue();
    flush();
  }));

  it('should not emit an `upload` event when all file uploads failed', fakeAsync(async () => {
    mockUploadService.uploadImage.and.returnValues(of(false), of(false));
    let upload: boolean | undefined;
    component.upload
      .pipe(first())
      .subscribe((success: boolean) => (upload = success));

    await harness.select([
      new File(['this is file1!'], 'filename1'),
      new File(['this is file2!'], 'filename2')
    ]);
    tick(UploadButtonComponent.MIN_LOADING_TIME_MS);

    expect(upload).toBeUndefined();
    flush();
  }));
});
