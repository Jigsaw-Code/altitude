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

import { Component, OnDestroy } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ValidationErrors,
  ValidatorFn
} from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { BehaviorSubject, ReplaySubject, takeUntil } from 'rxjs';

import {
  AdminService,
  ImporterConfig,
  ImporterConfigs
} from 'src/app/services/admin.service';
import { Logger } from 'src/app/services/logger.service';

const ALL_PROVIDED_ERROR = 'allProvided';

@Component({
  selector: 'app-importer-config',
  templateUrl: './importer-config.component.html',
  styleUrls: ['./importer-config.component.scss']
})
export class ImporterConfigComponent implements OnDestroy {
  readonly ALL_PROVIDED_ERROR = ALL_PROVIDED_ERROR;

  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed$ = new ReplaySubject<void>(1);

  private loading = new BehaviorSubject<boolean>(true);
  loading$ = this.loading.asObservable();

  readonly configForm = new FormGroup({
    tcap: new FormGroup(
      {
        enabled: new FormControl(false),
        username: new FormControl(),
        password: new FormControl(),
        diagnosticsEnabled: new FormControl(false)
      },
      allProvidedValidator('username', 'password')
    ),
    gifct: new FormGroup(
      {
        enabled: new FormControl(false),
        privacyGroupId: new FormControl(),
        accessToken: new FormControl(),
        diagnosticsEnabled: new FormControl(false)
      },
      allProvidedValidator('privacyGroupId', 'accessToken')
    )
  });

  importers: ImporterConfigs = {};

  /** Property to track whether to hide the token field for a group. */
  readonly hideToken = {
    tcap: true,
    gifct: true
  };

  constructor(
    private readonly logging: Logger,
    private readonly admin: AdminService,
    public snackBar: MatSnackBar
  ) {
    this.configureEnabledToggle();
    this.loading.next(true);
    this.admin
      .getImporterConfigs()
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: (importers: ImporterConfigs) => {
          this.importers = importers;
          if (importers['tcap']) {
            this.configForm.controls['tcap'].patchValue(
              importers['tcap'].config
            );
            this.configForm.controls['tcap'].updateValueAndValidity();
          }
          if (importers['gifct']) {
            this.configForm.controls['gifct'].patchValue(
              importers['gifct'].config
            );
            this.configForm.controls['gifct'].updateValueAndValidity();
          }
        },
        error: (error: Error) => {
          this.loading.next(false);
          this.logging.error('Loading configuration failed.', error);
          this.snackBar.open(
            `Error loading configuration. ${error.message}`,
            'Dismiss'
          );
        },
        complete: () => this.loading.next(false)
      });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.loading.complete();
  }

  private configureEnabledToggle() {
    const updateTcapToggle = updateEnabledToggle.bind(
      this,
      this.configForm.controls.tcap,
      'username',
      'password'
    );
    const updateGifctToggle = updateEnabledToggle.bind(
      this,
      this.configForm.controls.gifct,
      'privacyGroupId',
      'accessToken'
    );
    this.configForm.controls.tcap.valueChanges.subscribe(updateTcapToggle);
    updateTcapToggle();
    this.configForm.controls.gifct.valueChanges.subscribe(updateGifctToggle);
    updateGifctToggle();
  }

  save() {
    if (this.configForm.invalid) {
      throw new Error('Form is not valid.');
    }

    this.loading.next(true);
    // Disabled FormControls are undefined in the configForm, but these values
    // should be updated on save, so we replace undefined with False.
    const importerConfigs = this.configForm.value as {
      [key: string]: ImporterConfig;
    };
    importerConfigs['tcap'].diagnosticsEnabled =
      importerConfigs['tcap'].diagnosticsEnabled ??
      this.configForm.controls['tcap'].controls[
        'diagnosticsEnabled'
      ].getRawValue();
    importerConfigs['gifct'].diagnosticsEnabled =
      importerConfigs['gifct'].diagnosticsEnabled ??
      this.configForm.controls['gifct'].controls[
        'diagnosticsEnabled'
      ].getRawValue();
    this.admin
      .saveImporterConfigs(importerConfigs)
      .pipe(takeUntil(this.destroyed$))
      .subscribe({
        next: () => {
          this.snackBar.open('Configuration saved', 'Dismiss');
          this.configForm.markAsPristine();
        },
        error: (error) => {
          this.loading.next(false);
          this.logging.error('Saving configuration failed.', error);
          this.snackBar.open(
            `Error saving configuration. ${error.message}`,
            'Dismiss'
          );
        },
        complete: () => this.loading.next(false)
      });
  }
}

/** Checks that all or none of the provided fields in a form group are set. */
function allProvidedValidator(...controlKeys: string[]): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const values = controlKeys
      .map((key: string) => group.get(key)?.value)
      .filter((value) => !!value);
    // Either provide all provided controls or leave all of them empty.
    return !values.length || controlKeys.length === values.length
      ? null
      : { [ALL_PROVIDED_ERROR]: true };
  };
}

/** Updates the "enabled" toggle based on the state of credentials. */
function updateEnabledToggle(
  formGroup: FormGroup,
  usernameKey: string,
  passwordKey: string
) {
  const toggle = formGroup.controls['enabled'];
  const missingCredentials =
    !formGroup.value[usernameKey] && !formGroup.value[passwordKey];
  if (toggle.value && missingCredentials) {
    toggle.setValue(false);
  }
  if (formGroup.invalid || missingCredentials) {
    toggle.disable({ onlySelf: true });
  } else {
    toggle.enable({ onlySelf: true });
  }

  if (toggle.value) {
    formGroup.controls['diagnosticsEnabled'].enable({ onlySelf: true });
  } else {
    formGroup.controls['diagnosticsEnabled'].disable({ onlySelf: true });
  }
}
