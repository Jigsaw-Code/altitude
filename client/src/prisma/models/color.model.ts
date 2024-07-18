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

/**
 * Color palette with baseline and extended color tokens
 */
export type Color =
  | 'inherit'
  | 'primary'
  | 'secondary'
  | 'tertiary'
  | 'error'
  | 'neutral'
  | 'neutral-variant'
  | 'yellow'
  | 'ocher'
  | 'orange'
  | 'rose'
  | 'pink'
  | 'purple'
  | 'blue'
  | 'light-blue'
  | 'teal'
  | 'green'
  | 'olive';

/** Color reference with colors tokens variations */
export type ColorRef =
  | '0'
  | '10'
  | '20'
  | '30'
  | '40'
  | '50'
  | '60'
  | '70'
  | '80'
  | '90'
  | '95'
  | '99'
  | '100';

/** Color variations */
export type ColorVariation = 'on' | 'container' | 'on-container';
