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

import { Color, ColorRef, ColorVariation } from '../models/color.model';

/**
 * Export function to set the token color on the component based on color,
 * variation and ref params
 *
 * @param color - color palette
 * @param colorVariation - color variation
 * @param colorRef - color reference
 *
 * @return color token
 */
export function setTokenColor(
  color: Color,
  colorVariation?: ColorVariation,
  colorRef?: ColorRef
) {
  const sys = '--prisma-sys-color';
  const extended = '--prisma-extended-color';
  const refPalette = '--prisma-ref-palette';
  const refExtended = '--prisma-extended-palette';

  // neutral and neutral-variant
  if (color === 'neutral') {
    if (colorRef) {
      return `${refPalette}-${color}-${colorRef}`;
    }
    return `${sys}-on-background`;
  }

  if (color === 'neutral-variant') {
    if (colorRef) {
      return `${refPalette}-${color}-${colorRef}`;
    }
    return `${sys}-on-surface-variant`;
  }

  // extended colors
  if (
    color !== 'primary' &&
    color !== 'secondary' &&
    color !== 'tertiary' &&
    color !== 'error'
  ) {
    if (colorRef) {
      return `${refExtended}-${color}-${colorRef}`;
    }

    if (colorVariation === 'on') {
      return `${extended}-on-${color}`;
    }

    if (colorVariation === 'container') {
      return `${extended}-${color}-container`;
    }

    if (colorVariation === 'on-container') {
      return `${extended}-on-${color}-container`;
    }

    return `${extended}-${color}`;
  }

  // sys colors
  if (colorRef) {
    return `${refPalette}-${color}-${colorRef}`;
  }

  if (colorVariation === 'on') {
    return `${sys}-on-${color}`;
  }

  if (colorVariation === 'container') {
    return `${sys}-${color}-container`;
  }

  if (colorVariation === 'on-container') {
    return `${sys}-on-${color}-container`;
  }

  return `${sys}-${color}`;
}
