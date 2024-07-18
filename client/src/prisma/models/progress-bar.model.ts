/**
 * Copyright 2024 Google LLC
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

import { type Color, type ColorRef, type ColorVariation } from './color.model';

/**
 * Progress bar type
 * Linear: shows progress in just one bar from 'current' to 'total'.
 * Legend: shows progress in a sectioned bar of 'legend' to 'total'.
 */
export type ProgressBarType = 'linear' | 'legend';

/** Progress bar legend options represents the model to render a legend in a single model. */
export interface ProgressBarLegendOptions {
  title: string;
  color: Color;
  quantity: number;
  colorRef?: ColorRef;
  colorVariation?: ColorVariation;
}

/** Progress bar legend list options is a wrapper to render a list of legends. */
export interface ProgressBarLegendListOptions {
  legend: ProgressBarLegendOptions[];
  showLegend: boolean;
}
