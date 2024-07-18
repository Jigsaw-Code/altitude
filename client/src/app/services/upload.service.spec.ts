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
  HttpClientTestingModule,
  HttpTestingController
} from '@angular/common/http/testing';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';

import { UploadService } from './upload.service';

describe('UploadService', () => {
  let httpTestingController: HttpTestingController;
  let service: UploadService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UploadService]
    });

    httpTestingController = TestBed.inject(HttpTestingController);
    service = TestBed.inject(UploadService);

    const fakeFileReader = jasmine.createSpyObj('FileReader', [
      'readAsDataURL'
    ]);
    fakeFileReader.readAsDataURL.and.callFake((file: File) => {
      fakeFileReader.result = `dataURL(${file.name})`;
      fakeFileReader.onload();
    });
    spyOn(window, 'FileReader').and.returnValue(fakeFileReader);
  });

  afterEach(() => {
    // After every test, assert that there are no more pending requests.
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should send correct request to `/upload_image`', fakeAsync(() => {
    const testFile = new File(['hello world'], 'test.txt');

    service.uploadImage(testFile).subscribe();
    tick();

    const request = httpTestingController.expectOne('/upload_image');
    expect(request.request.method).toBe('POST');
    expect(request.request.body.image).toBe('dataURL(test.txt)');
    expect(request.request.body.name).toBe('test.txt');
    request.flush({});
  }));

  it('should return success=true on successful response', fakeAsync(() => {
    const testFile = new File(['hello world'], 'test.txt');

    service.uploadImage(testFile).subscribe((success) => {
      expect(success).toBeTrue();
    });
    tick();

    httpTestingController.expectOne('/upload_image').flush({});
  }));

  it('should return success=false on error response', fakeAsync(() => {
    const testFile = new File(['hello world'], 'test.txt');

    service.uploadImage(testFile).subscribe((success) => {
      expect(success).toBeFalse();
    });
    tick();

    httpTestingController
      .expectOne('/upload_image')
      .flush(null, { status: 500, statusText: 'Internal Server Error' });
  }));
});
