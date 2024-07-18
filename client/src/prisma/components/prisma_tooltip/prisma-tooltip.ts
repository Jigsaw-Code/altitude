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

import '../prisma_badge/prisma-badge';

import { html, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import tippy, { type Instance } from 'tippy.js';

import { type Position } from '../../models/position.model';
import { styles as tooltipStyles } from '../../tokens/tooltip.css';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';
import { applyGlobalStyle } from '../../utils/styles';

/**
 * Tooltips display informative text when users hover over, focus on, or tap an
 * element.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-tooltip')
export class PrismaTooltip extends BaseComponent {
  /** PrismaTooltip.text - the tooltip text */
  @property({ reflect: true }) text?: string;

  /** PrismaTooltip.position - set the tooltip position */
  @property({ reflect: true }) position: Position = 'bottom';

  /** PrismaTooltip.show - if true, on page load tooltip will start opened */
  @property({ type: Boolean, reflect: true }) show = false;

  /**
   * PrismaTooltip.label - if true, apply tooltip for label component if the
   * content it's wrapped
   */
  @property({ type: Boolean }) label = false;

  /** PrismaTooltip.shortcut - renders prisma-badge with shortcut text */
  @property({ reflect: true }) shortcut?: string;

  /**
   * PrismaTooltip.for - the element that the tooltip is for () =>
   * document.querySelector('#id')
   */
  @property({ type: Object }) for!: () => Element;

  @state() instance?: Instance | Instance[];

  private createTooltip(content: HTMLElement | string): void {
    const element = this.for();
    let showTooltip = true;
    let tooltipContent: string | HTMLElement = content;

    if (this.label) {
      const labelElement = element.querySelector('.label-text') as HTMLElement;
      if (labelElement) {
        const textElement = labelElement.shadowRoot!.querySelector(
          '.prisma-text'
        ) as HTMLElement;
        showTooltip =
          textElement.clientWidth < textElement.scrollWidth ||
          textElement.clientHeight < textElement.scrollHeight;
      }
    }

    if (this.shortcut && typeof content === 'string') {
      const badge = document.createElement('prisma-badge');
      const text = document.createElement('span');

      text.textContent = content;

      badge.setAttribute('type', 'rounded');
      badge.setAttribute('color', 'inherit');
      badge.setAttribute('value', this.shortcut);

      tooltipContent = document.createElement('div');
      tooltipContent.appendChild(text);
      tooltipContent.appendChild(badge);
    }

    if (showTooltip) {
      const disableTabIndex0 = element.classList.contains('remove-tabindex-0');
      if (!this.instance) {
        this.instance = tippy(element, {
          arrow: false,
          theme: 'prisma',
          allowHTML: false,
          animation: 'fade',
          interactive: true,
          placement: this.position,
          onShown: () => emit(this, PrismaTooltipEventType.SHOWN)
        });

        if (Array.isArray(this.instance)) {
          for (const el of this.instance) {
            if (el.popper) {
              this.applyStyleTooltipPopper(element, el.popper);
            }
          }
        } else {
          if (this.instance.popper) {
            this.applyStyleTooltipPopper(element, this.instance.popper);
          }
        }
      }

      if (Array.isArray(this.instance)) {
        for (const el of this.instance) {
          el.setContent(tooltipContent);
        }
      } else {
        this.instance.setContent(tooltipContent);
      }

      if (this.show) {
        if (Array.isArray(this.instance)) {
          for (const el of this.instance) {
            el.show();
          }
        } else {
          this.instance.show();
        }
      }
    }
  }

  private applyStyleTooltipPopper(
    element: Element,
    popperElement: HTMLElement
  ): void {
    applyGlobalStyle([tooltipStyles], popperElement);
    if (element.classList.contains('prisma-theme-dark')) {
      popperElement.classList.add('prisma-theme-dark');
    } else if (element.classList.contains('prisma-theme-light')) {
      popperElement.classList.add('prisma-theme-light');
    }
  }

  private handleSlotChange(e: Event): void {
    if (!this.text) {
      const slot = e.target as HTMLSlotElement;
      const elements = slot.assignedElements({ flatten: true });

      if (elements.length > 0) {
        const wrapper = document.createElement('div');

        wrapper.style.display = 'flex';
        wrapper.style.flexDirection = 'column';

        elements.forEach((element) => {
          wrapper.appendChild(element);
        });

        this.createTooltip(wrapper);
      }
    }
  }

  override updated(): void {
    if (this.text) this.createTooltip(this.text);
  }

  protected override render(): TemplateResult {
    return html`
      <div
        class="prisma-tooltip ${this.className}"
        role=${ifDefined(this.ariaRole)}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        @slotchange=${this.handleSlotChange}
      >
        <slot></slot>
      </div>
    `;
  }
}

/**
 * Event types for PrismaTooltip
 */
export enum PrismaTooltipEventType {
  SHOWN = 'prisma-tooltip-shown'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-tooltip': PrismaTooltip;
  }
}
