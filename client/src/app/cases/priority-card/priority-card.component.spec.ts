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

import { SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PriorityCardComponent } from './priority-card.component';
import { CasesModule } from '../cases.module';

describe('PriorityCardComponent', () => {
  let component: PriorityCardComponent;
  let fixture: ComponentFixture<PriorityCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CasesModule],
      declarations: [PriorityCardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PriorityCardComponent);
    component = fixture.componentInstance;
    component.label = 'MEDIUM';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list score label', () => {
    component.ngOnChanges({ confidence: new SimpleChange(null, 'HIGH', true) });
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement.querySelector('.title');
    // Gets capitalized with CSS
    expect(el.textContent).toContain('high Confidence');
  });
});
