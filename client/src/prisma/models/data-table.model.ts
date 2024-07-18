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

import { BadgeType } from './badge.model';
import { Color } from './color.model';
import {
  IconFill,
  IconFontStyle,
  IconGrade,
  IconOpticalSize,
  IconWeight
} from './icon.model';
import { ProfilePictureStatusType } from './profile-picture.model';
import { SensitivityType } from './sensitivity-badge.model';

/** Cell type represents the cell content types  */
export type DataTableCellType =
  | 'title'
  | 'text'
  | 'user'
  | 'progress-bar'
  | 'sensitivity-badge'
  | 'menu'
  | 'icon-button'
  | 'icon'
  | 'badge'
  | 'slot';

/** Cell scope determine the colscope of row */
export type DataTableCellScope = 'row' | 'col' | 'rowgroup' | 'colgroup';

/** Density represents the size of row */
export type DataTableDensity = 'small' | 'medium' | 'large';

/** Cell props represents all possible properties to the cell element */
export interface DataTableCellProps {
  id?: string;
  text?: string;
  icon?: string;
  color?: Color;
  width?: string;
  sorted?: boolean;
  header?: boolean;
  disabled?: boolean;
  divider?: boolean;
  headerId?: string;
  sortable?: boolean;
  iconFontStyle?: IconFontStyle;
  iconFill?: IconFill;
  iconWeight?: IconWeight;
  iconGrade?: IconGrade;
  iconOpticalSize?: IconOpticalSize;
  badgeType?: BadgeType;
  progressTotal?: number;
  progressTitle?: string;
  progressLabel?: string;
  progressHide?: boolean;
  type: DataTableCellType;
  progressCurrent?: number;
  density?: DataTableDensity;
  colScope?: DataTableCellScope;
  profilePictureSource?: string;
  sensitivityBadge?: SensitivityType;
  profilePictureStatus?: ProfilePictureStatusType;
  menuOptions?: Array<{ id: string; label: string; action?: string }>;
}

/** Row props represents all possible properties to the row element */
export interface DataTableRowProps {
  cells: DataTableCellProps[];
  header?: boolean;
  disabled?: boolean;
  indeterminate?: boolean;
  density?: DataTableDensity;
  noCheckbox?: boolean;
  checked?: boolean;
  rowIndex?: number;
}
