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
import { Observable, map, tap } from 'rxjs';

import { Logger } from './logger.service';
import { convertDates } from '../utils/date-utils';

export interface TcapConfig {
  enabled: boolean;
  diagnosticsEnabled: boolean;
  password: string;
  username: string;
}

export interface GifctConfig {
  enabled: boolean;
  diagnosticsEnabled: boolean;
  privacyGroupId: string;
  accessToken: string;
}

export type ImporterConfig = TcapConfig | GifctConfig;

export interface ImporterConfigs {
  [key: string]: {
    config: ImporterConfig;
    lastRunTime?: Date;
    totalImportCount: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  /** Common options to set on HTTP requests. */
  private static readonly OPTIONS = {
    headers: new HttpHeaders().set('Content-Type', 'application/json')
  };

  constructor(
    private readonly http: HttpClient,
    private readonly logger: Logger
  ) {}

  getImporterConfigs(): Observable<ImporterConfigs> {
    return this.http
      .get<ImporterConfigs>('/get_importer_configs', AdminService.OPTIONS)
      .pipe(
        map((config: ImporterConfigs) => {
          convertDates(config);
          return config;
        })
      );
  }

  saveImporterConfigs(configs: {
    [key: string]: ImporterConfig;
  }): Observable<boolean> {
    const importerTypes = Object.keys(configs);
    this.logger.info(`Saving configs for importers: ${importerTypes}`);

    return this.http
      .post<boolean>('/update_importer_configs', configs, AdminService.OPTIONS)
      .pipe(
        tap(() => {
          this.logger.info(
            `Successfully updated configs for importers: ${importerTypes}`
          );
        })
      );
  }
}
