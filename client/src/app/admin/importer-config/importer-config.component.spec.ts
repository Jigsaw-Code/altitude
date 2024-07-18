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
import {
  ComponentFixture,
  TestBed,
  fakeAsync,
  flush
} from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonHarness } from '@angular/material/button/testing';
import { MatFormFieldHarness } from '@angular/material/form-field/testing';
import { MatInputHarness } from '@angular/material/input/testing';
import { MatSlideToggleHarness } from '@angular/material/slide-toggle/testing';
import { of } from 'rxjs';

import { AdminService } from 'src/app/services/admin.service';

import { ImporterConfigComponent } from './importer-config.component';
import { AdminModule } from '../admin.module';

describe('ImporterConfigComponent', () => {
  let component: ImporterConfigComponent;
  let fixture: ComponentFixture<ImporterConfigComponent>;
  let loader: HarnessLoader;

  let mockAdminService: jasmine.SpyObj<AdminService>;

  beforeEach(async () => {
    mockAdminService = jasmine.createSpyObj(
      'AdminService',
      Object.getOwnPropertyNames(AdminService.prototype)
    );
    mockAdminService.getImporterConfigs.and.returnValue(
      of({
        tcap: {
          config: {
            enabled: true,
            diagnosticsEnabled: true,
            username: 'foo',
            password: 'bar'
          },
          lastRunTime: new Date(),
          totalImportCount: 12
        },
        gifct: {
          config: {
            enabled: false,
            diagnosticsEnabled: false,
            privacyGroupId: 'foo1',
            accessToken: 'bar1'
          },
          lastRunTime: new Date(),
          totalImportCount: 3
        }
      })
    );

    await TestBed.configureTestingModule({
      imports: [AdminModule, ReactiveFormsModule],
      declarations: [ImporterConfigComponent],
      providers: [{ provide: AdminService, useValue: mockAdminService }]
    }).compileComponents();

    fixture = TestBed.createComponent(ImporterConfigComponent);
    loader = TestbedHarnessEnvironment.loader(fixture);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should pre-fill input fields with existing configs', fakeAsync(async () => {
    const usernameInput = (await loader
      .getHarness(MatFormFieldHarness.with({ floatingLabelText: 'Username' }))
      .then((h) => h.getControl())) as MatInputHarness;
    const passwordInput = (await loader
      .getHarness(MatFormFieldHarness.with({ floatingLabelText: 'Password' }))
      .then((h) => h.getControl())) as MatInputHarness;
    const privacyGroupIdInput = (await loader
      .getHarness(
        MatFormFieldHarness.with({ floatingLabelText: 'Privacy group ID' })
      )
      .then((h) => h.getControl())) as MatInputHarness;
    const accessTokenInput = (await loader
      .getHarness(
        MatFormFieldHarness.with({ floatingLabelText: 'Access token' })
      )
      .then((h) => h.getControl())) as MatInputHarness;
    expect(await usernameInput.getValue()).toEqual('foo');
    expect(await passwordInput.getValue()).toEqual('bar');
    expect(await privacyGroupIdInput.getValue()).toEqual('foo1');
    expect(await accessTokenInput.getValue()).toEqual('bar1');
  }));

  it('should update configs by calling the AdminService', fakeAsync(async () => {
    const usernameInput = (await loader
      .getHarness(MatFormFieldHarness.with({ floatingLabelText: 'Username' }))
      .then((h) => h.getControl())) as MatInputHarness;
    await usernameInput.setValue('updated username');

    const blockButton = await loader.getHarness(
      MatButtonHarness.with({ text: 'Save' })
    );
    await blockButton.click();
    expect(mockAdminService.saveImporterConfigs).toHaveBeenCalledOnceWith({
      tcap: {
        enabled: true,
        diagnosticsEnabled: true,
        username: 'updated username',
        password: 'bar'
      },
      gifct: {
        enabled: false,
        diagnosticsEnabled: false,
        privacyGroupId: 'foo1',
        accessToken: 'bar1'
      }
    });
    flush();
  }));

  it('should update enable value when importer is disabled', fakeAsync(async () => {
    const toggleHarnesses = await loader.getAllHarnesses(MatSlideToggleHarness);
    for (const toggleHarness of toggleHarnesses) {
      await toggleHarness.toggle();
    }

    const blockButton = await loader.getHarness(
      MatButtonHarness.with({ text: 'Save' })
    );
    await blockButton.click();
    expect(mockAdminService.saveImporterConfigs).toHaveBeenCalledOnceWith({
      tcap: {
        enabled: false,
        diagnosticsEnabled: true,
        username: 'foo',
        password: 'bar'
      },
      gifct: {
        enabled: true,
        diagnosticsEnabled: false,
        privacyGroupId: 'foo1',
        accessToken: 'bar1'
      }
    });
    flush();
  }));
});
