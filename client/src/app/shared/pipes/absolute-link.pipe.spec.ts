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

import { AbsoluteLinkPipe } from './absolute-link.pipe';
import { SharedModule } from '../shared.module';

@Component({
  template: '{{ link | absoluteLink }}'
})
class TestComponent {
  link?: string;
}

describe('absoluteLink Pipe', () => {
  let fixture: ComponentFixture<TestComponent>;
  let pipe: AbsoluteLinkPipe;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule],
      declarations: [TestComponent]
    });

    fixture = TestBed.createComponent(TestComponent);
    pipe = new AbsoluteLinkPipe();
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should not change absolute URLs', () => {
    fixture.componentInstance.link = 'https://google.com';
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toEqual('https://google.com');
  });

  it('should change relative URLs', () => {
    fixture.componentInstance.link = 'google.com';
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toEqual('//google.com');
  });
});
