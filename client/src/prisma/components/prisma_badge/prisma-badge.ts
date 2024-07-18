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

import '../prisma_text/prisma-text';

import { html, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { type BadgeType } from '../../models/badge.model';
import { type Color } from '../../models/color.model';
import { BaseComponent } from '../../utils/base-component';

import { styles } from './prisma-badge.css';

/**
 * Badges convey dynamic information, such as counts or status. A badge can
 * include labels or numbers.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-badge')
export class PrismaBadge extends BaseComponent {
  static override styles = styles;

  /** PrismaBadge.type - changes the badge's type */
  @property({ reflect: true }) type: BadgeType = 'circle';

  /** PrismaBadge.color - changes the color scheme */
  @property({ reflect: true }) color: Color = 'primary';

  /** PrismaBadge.value - a text to be shown */
  @property({ reflect: true }) value?: string;

  /** PrismaBadge.disabled - if true, applies a disabled appearance */
  @property({ type: Boolean, reflect: true }) disabled = false;

  protected override render(): TemplateResult {
    return html`
      <div
        class="prisma-badge ${this.color} ${this.type} ${this.className}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
        ?disabled=${this.disabled}
      >
        <prisma-text variant="label" size="large">${this.value}</prisma-text>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-badge': PrismaBadge;
  }
}
