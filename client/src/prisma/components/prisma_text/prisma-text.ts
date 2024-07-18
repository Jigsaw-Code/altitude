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

import { TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { html as staticHtml } from 'lit/static-html.js';

import { type Size } from '../../models/size.model';
import { type As, type Variant } from '../../models/typography.model';
import { BaseComponent } from '../../utils/base-component';

import { styles } from './prisma-text.css';

/**
 * Text component is used to create text using prisma typography tokens
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-text')
export class PrismaText extends BaseComponent {
  static override styles = styles;

  /** PrismaText.as - define the html render tag */
  @property({ reflect: true }) as: As = 'p';

  /** PrismaText.size - define the text size */
  @property({ reflect: true }) size: Size = 'medium';

  /** PrismaText.variant - define the variant */
  @property({ reflect: true }) variant: Variant = 'body';

  private renderTag(tag: string): TemplateResult {
    const styles = `prisma-text prisma-sys-typescale-${this.variant}-${this.size} ${this.className}`;

    switch (tag) {
      case 'h1':
        return staticHtml`<h1 title="${this.title}" class="${styles}">
          <slot></slot>
        </h1>`;
      case 'h2':
        return staticHtml`<h2 title="${this.title}" class="${styles}">
          <slot></slot>
        </h2>`;
      case 'h3':
        return staticHtml`<h3 title="${this.title}" class="${styles}">
          <slot></slot>
        </h3>`;
      case 'h4':
        return staticHtml` <h4 title="${this.title}" class="${styles}">
          <slot></slot>
        </h4>`;
      case 'h5':
        return staticHtml`<h5 title="${this.title}" class="${styles}">
          <slot></slot>
        </h5>`;
      case 'h6':
        return staticHtml`<h6 title="${this.title}" class="${styles}">
          <slot></slot>
        </h6>`;
      case 'label':
        return staticHtml`<label class="${styles}">
          <slot></slot>
        </label>`;
      case 'div':
        return staticHtml`<div class="${styles}">
          <slot></slot>
        </div>`;
      case 'b':
        return staticHtml`<b class="${styles}">
          <slot></slot>
        </b>`;
      case 'p':
      default:
        return staticHtml`<p class="${styles}">
          <slot></slot>
        </p>`;
    }
  }

  protected override render() {
    return this.renderTag(this.as);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-text': PrismaText;
  }
}
