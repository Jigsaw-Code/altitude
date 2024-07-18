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
import {
  ComponentFixture,
  TestBed,
  discardPeriodicTasks,
  fakeAsync,
  tick
} from '@angular/core/testing';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import MockDate from 'mockdate';

import { FormatDateAsyncPipe } from './format-date-async.pipe';
import { SharedModule } from '../shared.module';
import { DAYJS } from '../tokens';

dayjs.extend(utc);

@Component({
  template: '{{ date | formatDateAsync:"short" | async }}'
})
class TestComponentShort {
  date?: Date;
}

@Component({
  template: '{{ date | formatDateAsync | async }}'
})
class TestComponentLong {
  date?: Date;
}

describe('formatDateAsync Pipe with short format', () => {
  let fixture: ComponentFixture<TestComponentShort>;
  let pipe: FormatDateAsyncPipe;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule],
      declarations: [TestComponentShort],
      providers: [{ provide: DAYJS, useFactory: () => dayjs.utc }]
    });

    fixture = TestBed.createComponent(TestComponentShort);
    pipe = new FormatDateAsyncPipe(TestBed.inject(DAYJS));
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  describe('with mocked date', () => {
    let mockNow: Date;

    beforeEach(() => {
      mockNow = new Date('2022-12-25T12:00:00+00:00');
      MockDate.set(mockNow);
    });

    afterEach(() => {
      MockDate.reset();
    });

    it('should set full date when more than a week difference', () => {
      fixture.componentInstance.date = new Date(
        '2022-12-01T06:30:58.684882+00:00'
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('Dec 01, 2022');
    });

    it('should set days ago', () => {
      fixture.componentInstance.date = new Date(
        '2022-12-23T01:30:58.684882+00:00'
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('2 days ago');
    });

    it('should set hours ago', () => {
      fixture.componentInstance.date = new Date('2022-12-25T10:00:00+00:00');
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('2 hours ago');
    });

    it('should set minutes ago', () => {
      fixture.componentInstance.date = new Date(
        '2022-12-25T11:20:08.684882+00:00'
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('40 minutes ago');
    });

    it('should set seconds ago', () => {
      fixture.componentInstance.date = new Date(
        '2022-12-25T11:59:40.684882+00:00'
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('a few seconds ago');
    });

    it('should set now', () => {
      fixture.componentInstance.date = mockNow;
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('a few seconds ago');
    });

    it('should handle non-utc timezone', () => {
      fixture.componentInstance.date = new Date('2022-12-25T06:00-05:00');
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toEqual('an hour ago');
    });
  });

  it('should automatically update time', fakeAsync(() => {
    const now = new Date();
    MockDate.set(now);
    fixture.componentInstance.date = now;
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toEqual('a few seconds ago');

    tick(60 * 60 * 1000); // 1 hour
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toEqual('an hour ago');

    discardPeriodicTasks();
  }));
});

describe('formatDateAsync Pipe with long format', () => {
  let fixture: ComponentFixture<TestComponentLong>;
  let pipe: FormatDateAsyncPipe;
  let mockNow: Date;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule],
      declarations: [TestComponentLong],
      providers: [{ provide: DAYJS, useFactory: () => dayjs.utc }]
    });

    fixture = TestBed.createComponent(TestComponentLong);
    pipe = new FormatDateAsyncPipe(TestBed.inject(DAYJS));

    mockNow = new Date('2022-12-25T12:00:00+00:00');
    MockDate.set(mockNow);
  });

  afterEach(() => {
    MockDate.reset();
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should set full date', () => {
    fixture.componentInstance.date = new Date(
      '2022-12-01T06:30:58.684882+00:00'
    );
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toEqual('Dec 01, 2022 - 6:30AM');
  });
});
