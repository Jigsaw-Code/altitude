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

import { LabelListOptions } from './label.model';

/**
 * Expander list type represents how expander list should open: item by item or
 * multiple items
 */
export type ExpanderListType = 'single' | 'multiple';

/** Expander item type represents if item is expandable or fixed */
export type ExpanderItemType = 'expandable' | 'fixed';

/**
 * Expander item options represents the model to render an expander item with
 * labels in a single model.
 */
export declare interface ExpanderItemOptions {
  id: string;
  title: string;
  expand?: boolean;
  type: ExpanderItemType;
  rounded?: boolean;
  subtitle?: string;
  shortcut?: string;
  labels: LabelListOptions;
}

/** Expander list options is a wrapper to render a list of expanders */
export declare interface ExpanderListOptions {
  gap: boolean;
  type?: ExpanderListType;
  items: ExpanderItemOptions[];
}
