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

import '@material/web/ripple/ripple';
import '../prisma_icon/prisma-icon';
import '../prisma_tooltip/prisma-tooltip';

import { html, nothing, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { type ButtonType } from '../../models/button.model';
import {
  type IconFill,
  type IconFontStyle,
  type IconGrade,
  type IconOpticalSize,
  type IconWeight
} from '../../models/icon.model';
import { type Position } from '../../models/position.model';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';

import { styles } from './prisma-action-button.css';

/**
 * The action button represents the navigation actions on a screen. It puts
 * key actions within reach.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-action-button')
export class PrismaActionButton extends BaseComponent {
  static override styles = styles;

  /** PrismaActionButton.icon - the id from material symbols */
  @property({ reflect: true }) icon?: string;

  /** PrismaActionButton.tooltip - the text content to be shown in a tooltip */
  @property({ reflect: true }) tooltip?: string;

  /** PrismaActionButton.tooltipPosition - the position of the tooltip */
  @property({ attribute: 'tooltip-position', reflect: true })
  tooltipPosition: Position = 'bottom';

  /** PrismaActionButton.tooltipShow - if true, show tooltip by default */
  @property({ attribute: 'tooltip-show', reflect: true }) tooltipShow = false;

  /** PrismaActionButton.tooltipShortcut - shows a keyboard command  */
  @property({ attribute: 'tooltip-shortcut', reflect: true })
  tooltipShortcut?: string;

  /** PrismaActionButton.variation - change the action-button style */
  @property({ reflect: true }) variation: Variation = 'filled';

  /** PrismaActionButton.iconFontStyle - changes the icon style */
  @property({ attribute: 'icon-font-style', reflect: true })
  iconFontStyle?: IconFontStyle = 'outlined';

  /** PrismaActionButton.iconOpticalSize - changes the icon size */
  @property({ attribute: 'icon-optical-size', reflect: true })
  iconOpticalSize?: IconOpticalSize = 24;

  /** PrismaActionButton.iconFill - changes the icon fill */
  @property({ attribute: 'icon-fill', reflect: true }) iconFill?: IconFill = 0;

  /** PrismaActionButton.iconWeight - changes the icon weight */
  @property({ attribute: 'icon-weight', reflect: true })
  iconWeight?: IconWeight = 400;

  /** PrismaActionButton.iconGrade - changes the icon grade */
  @property({ attribute: 'icon-grade', reflect: true })
  iconGrade?: IconGrade = 0;

  /** PrismaActionButton.buttonType - changes the button type */
  @property({ attribute: 'button-type', reflect: true })
  buttonType: ButtonType = 'button';

  /** PrismaActionButton.selected - if true, set selected state to button */
  @property({ type: Boolean, reflect: true }) selected = false;

  /** PrismaActionButton.disabled - if true, disable the component */
  @property({ type: Boolean, reflect: true }) disabled = false;

  private onClick(): void {
    const detail: PrismaActionButtonDetail = {
      icon: this.icon,
      tooltip: this.tooltip,
      selected: this.selected
    };

    if (this.buttonType === 'select') {
      this.selected = !this.selected;

      if (!this.selected) {
        this.blur();
      } else {
        this.focus();
      }

      emit(this, PrismaActionButtonEventType.SELECTED, { detail });
    } else if (this.buttonType === 'button') {
      emit(this, PrismaActionButtonEventType.CLICKED, { detail });
    }
    this.requestUpdate();
  }

  private useTooltip(text?: string): TemplateResult | typeof nothing {
    if (text) {
      return html`
        <prisma-tooltip
          .for=${() => this.shadowRoot?.querySelector('.prisma-action-button')!}
          .text="${text || ''}"
          .shortcut="${this.tooltipShortcut}"
          .position="${this.tooltipPosition}"
          .show=${this.tooltipShow}
        >
        </prisma-tooltip>
      `;
    } else {
      return nothing;
    }
  }

  override firstUpdated(): void {
    if (this.disabled) {
      const slot = this.shadowRoot!.querySelector('slot') as HTMLSlotElement;
      const nodes = slot.assignedElements({ flatten: true });
      if (nodes instanceof Array) {
        nodes.forEach((node) => {
          node.setAttribute('style', 'opacity: var(--prisma-opacity-disabled)');
        });
      }
    }
  }

  protected override render(): TemplateResult {
    if (this.icon) {
      return html`
        <button
          class="prisma-action-button ${this.variation} ${this
            .buttonType} ${this.className}"
          role=${ifDefined(this.ariaRole)}
          aria-label=${ifDefined(
            this.ariaLabel !== null ? this.ariaLabel : undefined
          )}
          aria-hidden=${ifDefined(
            this.ariaHidden === 'true' ? this.ariaHidden : undefined
          )}
          @click=${this.onClick}
          ?selected=${this.selected}
          ?disabled=${this.disabled}
        >
          <div class="state-layer">
            <md-ripple ?disabled="${this.disabled}"></md-ripple>
            <prisma-icon
              font-style=${this.iconFontStyle!}
              optical-size=${this.iconOpticalSize!}
              fill=${this.iconFill!}
              weight=${this.iconWeight!}
              grade=${this.iconGrade!}
              color="inherit"
              >${this.icon}</prisma-icon
            >
          </div>
        </button>
        ${this.tooltip && this.useTooltip(this.tooltip)}
      `;
    }

    return html`
      <button
        class="prisma-action-button ${this.variation} ${this.buttonType} ${this
          .className}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
        @click=${this.onClick}
        ?selected=${this.selected}
        ?disabled=${this.disabled}
      >
        <div class="state-layer">
          <md-ripple ?disabled="${this.disabled}"></md-ripple>
          <slot name="content"></slot>
        </div>
      </button>
      ${this.tooltip && this.useTooltip(this.tooltip)}
    `;
  }
}

/** Variation type for PrismaActionButton */
export type Variation = 'filled' | 'filled-tonal';

/** Event data types for PrismaActionButton */
export interface PrismaActionButtonDetail {
  icon?: string;
  tooltip?: string;
  selected: boolean;
}

/**
 * Event types for PrismaActionButton
 */
export enum PrismaActionButtonEventType {
  SELECTED = 'prisma-action-button-selected',
  CLICKED = 'prisma-action-button-clicked'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-action-button': PrismaActionButton;
  }
}
