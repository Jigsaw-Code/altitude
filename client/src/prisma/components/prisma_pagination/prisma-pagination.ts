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

import '@material/web/icon/icon';
import '@material/web/iconbutton/icon-button';
import '../prisma_text/prisma-text';

import { html, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';

import { styles } from './prisma-pagination.css';

/**
 * Pagination component enables the user to navigate through to a specific
 * page from a range of pages
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-pagination')
export class PrismaPagination extends BaseComponent {
  static override styles = styles;

  /** PrismaPagination.pages - sets the total of pages. default is 1 */
  @property({ type: Number, reflect: true }) pages = 1;

  /** PrismaPagination.currentPage - sets the current page. default is 1 */
  @property({ type: Number, reflect: true, attribute: 'current-page' })
  currentPage = 1;

  private previous(): void {
    this.currentPage--;
    const detail = {
      currentPage: this.currentPage
    };
    emit(this, PrismaPaginationEventType.PREVIOUS, { detail });
    this.requestUpdate();
  }

  private next(): void {
    this.currentPage++;
    const detail = {
      currentPage: this.currentPage
    };
    emit(this, PrismaPaginationEventType.NEXT, { detail });
    this.requestUpdate();
  }

  protected override render(): TemplateResult {
    return html`
      <div
        class="prisma-pagination ${this.className}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <prisma-text as="div" size="small" variant="body">
          ${this.currentPage}<span>of</span>${this.pages}
        </prisma-text>

        <md-icon-button
          class="button-previous"
          @click="${this.previous}"
          aria-label="Go to the previous page"
          ?disabled=${this.currentPage <= 1}
        >
          <md-icon>keyboard_arrow_left</md-icon>
        </md-icon-button>

        <md-icon-button
          class="button-next"
          aria-label="Go to the next page"
          ?disabled=${this.currentPage === this.pages}
          @click="${this.next}"
        >
          <md-icon>keyboard_arrow_right</md-icon>
        </md-icon-button>
      </div>
    `;
  }
}

/**
 * Event types for PrismaPagination
 */
export enum PrismaPaginationEventType {
  PREVIOUS = 'prisma-pagination-previous',
  NEXT = 'prisma-pagination-next'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-pagination': PrismaPagination;
  }
}
