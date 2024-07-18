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

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, from, map, mergeMap, of, tap } from 'rxjs';

import { Logger } from './logger.service';

/** Service to create and manage user uploads. */
@Injectable({
  providedIn: 'root'
})
export class UploadService {
  /** Common options to set on HTTP requests. */
  private static readonly OPTIONS = {
    headers: new HttpHeaders().set('Content-Type', 'application/json')
  };

  constructor(
    private readonly http: HttpClient,
    private readonly logger: Logger
  ) {}

  private getImageUrl(imageFile: File): Promise<ArrayBuffer | string> {
    return new Promise((resolve, reject) => {
      const fileReader = new FileReader();
      fileReader.onload = () => {
        if (fileReader.result) {
          resolve(fileReader.result);
        } else {
          reject('No image loaded.');
        }
      };
      fileReader.readAsDataURL(imageFile);
    });
  }

  /**
   * Uploads an image to match against.
   *
   * @param imageFile The image to create.
   * @returns true when the create request has been sent.
   */
  uploadImage(imageFile: File): Observable<boolean> {
    return from(this.getImageUrl(imageFile)).pipe(
      mergeMap((imgUrl: ArrayBuffer | string) => {
        return this.http.post<Record<string, never>>(
          '/upload_image',
          { name: imageFile.name, image: imgUrl },
          UploadService.OPTIONS
        );
      }),
      tap(() => {
        this.logger.info(`Successfully uploaded image: ${imageFile.name}`);
      }),
      map(() => true),
      catchError((error: Error) => {
        this.logger.error(`Failed to upload image: ${imageFile.name}`, error);
        return of(false);
      })
    );
  }
}
