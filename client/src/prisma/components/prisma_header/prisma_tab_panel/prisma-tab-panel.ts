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

import { html, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import { repeat } from 'lit/directives/repeat.js';

import { BaseComponent } from '../../../utils/base-component';

import { styles } from './prisma-tab-panel.css';

/**
 * Tab panel is a wrapper component to be used together with prisma-tab to
 * make it easy to explore and switch between different views.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-tab-panel')
export class PrismaTabPanel extends BaseComponent {
  static override styles = styles;

  /** PrismaTabPanel.panels - indicate the number of panels */
  @property({ type: Number, reflect: true }) panels = 1;

  @state() defaultTab = 0;

  private handleTabClick(e: Event): void {
    this.hidden = false;

    try {
      const event = e as CustomEvent;
      const panelsToHide = this.shadowRoot!.querySelectorAll('slot');
      const panelToShow = this.shadowRoot!.querySelector(
        `#panel-${Number(event.detail.index) + 1}`
      );

      if (panelsToHide.length > 0) {
        panelsToHide.forEach((panel) => {
          panel.setAttribute('hidden', 'true');
        });
      }

      if (panelToShow) {
        panelToShow.removeAttribute('hidden');
      }
    } catch (e) {
      this.hidden = true;

      throw new Error('prisma-tab-panel: incorrect index');
    }
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this.parentElement?.parentElement?.addEventListener(
      'prisma-tabs-default-tab-defined',
      (e) => {
        const event = e as CustomEvent;
        this.defaultTab = event.detail;
      }
    );
    this.parentElement?.parentElement?.addEventListener(
      'prisma-tab-clicked',
      (e) => {
        this.handleTabClick(e);
      }
    );
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.parentElement?.parentElement?.removeEventListener(
      'prisma-tabs-default-tab-defined',
      (e) => {
        const event = e as CustomEvent;
        this.defaultTab = event.detail;
      }
    );
    this.parentElement?.parentElement?.removeEventListener(
      'prisma-tab-clicked',
      (e) => {
        this.handleTabClick(e);
      }
    );
  }

  protected override render(): TemplateResult {
    return html`
      <div
        class="prisma-tab-panel ${this.className}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        ${repeat(
          Array.from({ length: this.panels }, (option, i) => i),
          (index) => {
            const id = `panel-${index + 1}`;
            const ariaLabelledby = `mdc-tab-${index + 1}`;

            return html`
              <slot
                role="tabpanel"
                aria-labelledby=${ariaLabelledby}
                id=${id}
                ?hidden=${index !== this.defaultTab}
                name=${id}
              >
              </slot>
            `;
          }
        )}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-tab-panel': PrismaTabPanel;
  }
}
