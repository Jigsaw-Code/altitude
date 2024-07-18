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

import { ButtonType } from './button.model';

/** Icon fill variation */
export type IconFill = 0 | 1;

/** Icon weight variation */
export type IconWeight = 100 | 200 | 300 | 400 | 500 | 600 | 700;

/** Icon grade variation */
export type IconGrade = -25 | 0 | 200;

/** Icon font variation */
export type IconFontStyle = 'outlined' | 'rounded' | 'sharp';

/** Icon optical size variation */
export type IconOpticalSize = 20 | 24 | 40 | 48;

/** Icon model represents the types of a set of icons */
export interface Icon {
  /** name of icon */
  iconKey: string;
  /** text of the icon */
  text: string;
  /**
   * represents how the icon should work as a button normally or as a select
   * button
   */
  buttonType: ButtonType;
  /**
   * when use buttonType=select, icon work as a toggle, so iconOff means the
   * icon when toggles the button
   */
  iconOff?: string;
  /** activated toggles the icon by default */
  activated?: boolean;
  /** iconGroup represents icon that should live in groups or not */
  iconGroup?: boolean;
  /** Sets if icon is filled */
  fill?: IconFill;
  /** Sets the icon weight */
  weight?: IconWeight;
  /** Sets the icon grade */
  grade?: IconGrade;
  /** Sets the font style */
  fontStyle?: IconFontStyle;
  /** Sets the optical size */
  opticalSize?: IconOpticalSize;
  /** a text that represents a keyboard command */
  shortcut?: string;
}
