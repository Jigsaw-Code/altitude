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

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CASE, IMAGE_CASE, URL_CASE } from 'src/app/testing/case_models';

import { ContentDisplayComponent } from './content-display.component';

describe('ContentDisplayComponent', () => {
  let component: ContentDisplayComponent;
  let fixture: ComponentFixture<ContentDisplayComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ContentDisplayComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ContentDisplayComponent);
    component = fixture.componentInstance;
    component.case = CASE;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('Case with URL should show iframe', () => {
    component.case = URL_CASE;
    fixture.detectChanges();
    component.ngOnChanges();

    const element: HTMLElement = fixture.nativeElement;
    expect(element.getElementsByTagName('iframe')[0]).toBeTruthy();
  });

  it('Case with image should show image', () => {
    component.case = IMAGE_CASE;
    fixture.detectChanges();

    const element: HTMLElement = fixture.nativeElement;
    expect(element.getElementsByTagName('img')[0]).toBeTruthy();
  });

  it('should open URL when clicked', () => {
    spyOn(window, 'open');
    component.case = URL_CASE;
    fixture.detectChanges();

    const button = fixture.debugElement.nativeElement.querySelector(
      'prisma-action-button'
    );
    button.click();
    expect(window.open).toHaveBeenCalledWith('https://abc.xyz/');
  });

  it('should open new tab when image is clicked', () => {
    spyOn(window, 'open');
    component.case = IMAGE_CASE;
    fixture.detectChanges();

    const button = fixture.debugElement.nativeElement.querySelector(
      'prisma-action-button'
    );
    button.click();
    expect(window.open).toHaveBeenCalledWith('about:blank');
  });
});
