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

import { Color } from './color.model';

/** Label type represents the variations of label component */
export type LabelType = 'regular' | 'input' | 'select';

/** Label options represents the model to render an label in a single model */
export declare interface LabelOptions {
  label: string;
  color?: Exclude<Color, 'neutral' | 'neutral-variant'>;
  indicator?: string;
  selected?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
}

/** Label list options is a wrapper to render a list of labels */
export declare interface LabelListOptions {
  type: LabelType;
  items: LabelOptions[];
}
