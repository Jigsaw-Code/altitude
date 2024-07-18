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
import { Component, EventEmitter, OnDestroy, Output } from '@angular/core';
import {
  MatDialog,
  MatDialogRef,
  MatDialogState
} from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import {
  BehaviorSubject,
  ReplaySubject,
  combineLatest,
  forkJoin,
  map,
  takeUntil,
  timer
} from 'rxjs';

import 'src/prisma/components/prisma_icon/prisma-icon';
import 'src/prisma/components/prisma_text/prisma-text';
import { LoadingDialogComponent } from 'src/app/shared/components/loading-dialog/loading-dialog.component';

import { UploadService } from '../../services/upload.service';

@Component({
  selector: 'app-upload-button',
  templateUrl: './upload-button.component.html',
  styleUrls: ['./upload-button.component.scss']
})
export class UploadButtonComponent implements OnDestroy {
  /**
   * Minimum time for the loading state on uploads.
   *
   * Some uploads are so quick it flashes the loading state too quickly. So we
   * artificially set a minimum amount of time we want uploads to take to make
   * the experience less jittery.
   */
  static readonly MIN_LOADING_TIME_MS = 2_000; // 2 seconds.

  /** Handle on-destroy Subject, used to unsubscribe. */
  private readonly destroyed$ = new ReplaySubject<void>(1);

  /** Emitted whenever a new upload has succeeded. */
  @Output() readonly upload = new EventEmitter<boolean>();

  private readonly loading = new BehaviorSubject<boolean>(false);
  readonly loading$ = this.loading.asObservable();

  private loadingDialogRef?: MatDialogRef<LoadingDialogComponent>;

  constructor(
    private readonly uploadService: UploadService,
    private readonly dialog: MatDialog,
    private readonly snackBar: MatSnackBar
  ) {
    this.loading$.subscribe((loading) => this.toggleLoadingSpinner(loading));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.loading.complete();
  }

  private toggleLoadingSpinner(loading: boolean) {
    if (loading) {
      if (
        this.loadingDialogRef &&
        this.loadingDialogRef.getState() == MatDialogState.OPEN
      ) {
        // There's already a loading dialog open. Do not open another one.
        return;
      }
      this.loadingDialogRef = this.dialog.open(LoadingDialogComponent, {
        disableClose: true,
        minHeight: 300,
        minWidth: 300
      });
    } else {
      this.loadingDialogRef?.close();
    }
  }

  uploadFile(event: Event) {
    const target = event.target as HTMLInputElement;
    if (!target.files) {
      return;
    }

    const files: File[] = Array.from(target.files);
    if (!target.files.length) {
      return;
    }

    this.loading.next(true);
    combineLatest([
      forkJoin(
        files.reduce(
          (obj, file) => ({
            ...obj,
            [file.name]: this.uploadService.uploadImage(file)
          }),
          {}
        )
      ),
      timer(UploadButtonComponent.MIN_LOADING_TIME_MS)
    ])
      .pipe(
        takeUntil(this.destroyed$),
        map((result) => result[0])
      )
      .subscribe((result: { [filename: string]: boolean }) => {
        this.loading.next(false);
        target.value = '';

        const anySucceeded = Object.values(result).some(Boolean);
        if (anySucceeded) {
          this.upload.emit(true);
        }

        const failedFiles: string[] = Object.keys(result).filter(
          (key) => !result[key]
        );
        if (!failedFiles.length) {
          this.snackBar.open(
            `Successfully uploaded ${Object.keys(result).length} file(s)`,
            'Dismiss'
          );
          return;
        }

        const moreFailed = failedFiles.slice(2);
        const moreFailedSuffix = moreFailed.length
          ? ` (+${moreFailed.length} more)`
          : '';
        this.snackBar.open(
          `Failed to upload file(s): ${failedFiles.slice(0, 2).join(', ')}` +
            moreFailedSuffix,
          'Dismiss'
        );
      });
  }
}
