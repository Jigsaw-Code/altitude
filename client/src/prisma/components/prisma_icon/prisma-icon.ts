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

import { html } from 'lit';
import { styleMap } from 'lit-html/directives/style-map.js';
import { customElement, property } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { type Color } from '../../models/color.model';
import {
  type IconFill,
  type IconFontStyle,
  type IconGrade,
  type IconOpticalSize,
  type IconWeight
} from '../../models/icon.model';
import { BaseComponent } from '../../utils/base-component';

import { styles } from './prisma-icon.css';

/**
 * Icon component is used to create icon using prisma/google material
 * iconography tokens.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */

@customElement('prisma-icon')
export class PrismaIcon extends BaseComponent {
  static override styles = styles;

  /** PrismaIcon.color - sets the color scheme */
  @property({ reflect: true }) color?: Color = 'primary';

  /** PrismaIcon.fill - sets the icon fill */
  @property({ reflect: true }) fill?: IconFill = 0;

  /** PrismaIcon.weight - sets the icon weight */
  @property({ reflect: true }) weight?: IconWeight = 400;

  /** PrismaIcon.grade - sets the icon grade */
  @property({ reflect: true }) grade?: IconGrade = 0;

  /** PrismaIcon.fontStyle - sets the icon font style */
  @property({ reflect: true, attribute: 'font-style' })
  fontStyle?: IconFontStyle = 'outlined';

  /** PrismaIcon.opticalSize - sets the icon font size */
  @property({ reflect: true, attribute: 'optical-size' })
  opticalSize?: IconOpticalSize = 48;

  protected override render() {
    const fontSettings = `'FILL' ${this.fill},'wght' ${this.weight},'GRAD' ${this.grade},'opsz' ${this.opticalSize}`;

    const classes = {
      [`material-symbols-${this.fontStyle}`]: true,
      [`${this.color}`]: true
    };

    return html`
      <span
        role=${this.ariaRole ? this.ariaRole : 'img'}
        aria-label=${this.ariaLabel ? this.ariaLabel : 'icon'}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
        style=${styleMap({
          'font-variation-settings': fontSettings,
          'font-size': `${this.opticalSize}px`
        })}
        class="prisma-icon ${this.className}"
      >
        <span class=${classMap(classes)}><slot></slot></span>
      </span>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-icon': PrismaIcon;
  }
}
