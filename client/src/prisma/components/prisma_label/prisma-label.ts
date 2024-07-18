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
import '@material/web/ripple/ripple';
import '../prisma_badge/prisma-badge';
import '../prisma_icon/prisma-icon';
import '../prisma_text/prisma-text';
import '../prisma_tooltip/prisma-tooltip';

import { html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import { type ButtonType } from '../../models/button.model';
import { type Color } from '../../models/color.model';
import { LabelType } from '../../models/label.model';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';
import { PrismaBadge } from '../prisma_badge/prisma-badge';

import { styles } from './prisma-label.css';

/**
 * Label are compact elements that represents a classification, attribute
 * or action to a entity
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-label')
export class PrismaLabel extends BaseComponent {
  static override styles = styles;

  /** PrismaLabel.id - sets the component id */
  @property({ reflect: true }) override id = '';

  /** PrismaLabel.label - A simple text */
  @property({ reflect: true }) label?: string;

  /** PrismaLabel.type - sets the component type and changes it appereance */
  @property({ reflect: true }) type: Exclude<LabelType, 'select'> = 'regular';

  /** PrismaLabel.buttonType -  Define in which way the component should work */
  @property({ attribute: 'button-type', reflect: true })
  buttonType: ButtonType = 'select';

  /** PrismaLabel.color - sets the color scheme */
  @property({ reflect: true })
  color: Exclude<Color, 'neutral' | 'neutral-variant'> = 'primary';

  /** PrismaLabel.indicator - a value to be used in a circle prisma-badge */
  @property({ reflect: true }) indicator?: string;

  /** PrismaLabel.selected - if true, select the component by default */
  @property({ type: Boolean, reflect: true }) selected = false;

  /**
   * PrismaLabel.disabled - if true, applies the disabled appearence and
   * behavior
   */
  @property({ type: Boolean, reflect: true }) disabled = false;

  /** PrismaLabel.fullWidth - if true, label width is 100% */
  @property({ attribute: 'full-width', type: Boolean, reflect: true })
  fullWidth = false;

  @state() indicatorInternal = '';

  private selfRemove(): void {
    const detail: PrismaLabelDetail = {
      id: this.id,
      label: this.label ?? '',
      color: this.color,
      selected: this.selected
    };

    emit(this, PrismaLabelEventType.REMOVED, { detail });

    this.remove();
    this.requestUpdate();
  }

  private select(): void {
    if (this.buttonType === 'select') {
      this.selected = !this.selected;

      if (!this.selected) {
        this.blur();
      } else {
        this.focus();
      }

      const detail = {
        label: this.label,
        indicator: this.indicator,
        selected: this.selected
      };

      emit(this, PrismaLabelEventType.SELECTED, { detail });
    } else if (this.buttonType === 'button') {
      const detail: PrismaLabelDetail = {
        label: this.label ?? '',
        indicator: this.indicator,
        color: this.color,
        selected: this.selected
      };

      emit(this, PrismaLabelEventType.CLICKED, { detail });
    }
    this.requestUpdate();
  }

  private mouseOver(): void {
    if (this.selected && this.type === 'regular') {
      const badge = this.shadowRoot!.querySelector(
        'prisma-badge'
      ) as PrismaBadge;

      if (badge) {
        badge.value = 'X';
        badge.requestUpdate();
      }
    }
  }

  private mouseOut(): void {
    if (this.type === 'regular') {
      const badge = this.shadowRoot!.querySelector(
        'prisma-badge'
      ) as PrismaBadge;

      if (badge) {
        badge.value = this.indicatorInternal;
        badge.requestUpdate();
      }
    }
  }

  override firstUpdated(): void {
    this.indicatorInternal = this.indicator!;
  }

  protected override render(): TemplateResult | typeof nothing {
    this.id = `prisma-label-${new Date().getTime()}`;

    return html`
      ${this.label !== ''
        ? html`
            <button
              id="${this.id}"
              class="prisma-label ${this.type} ${this.color} ${this.className}"
              role="${ifDefined(this.ariaRole)}"
              aria-label="${this.label ?? ''}"
              aria-hidden="${ifDefined(
                this.ariaHidden === 'true' ? this.ariaHidden : undefined
              )}"
              @click=${this.select}
              @mouseout=${this.mouseOut}
              @mouseover=${this.mouseOver}
              ?selected=${this.selected}
              ?disabled=${this.disabled}
            >
              <md-ripple ?disabled="${this.disabled}"></md-ripple>

              <prisma-icon class="label" optical-size="18" color="inherit">
                label
              </prisma-icon>

              ${this.type === 'input'
                ? html`
                    <md-icon-button
                      @click=${this.selfRemove}
                      ?disabled=${this.disabled}
                      aria-label="Click here to remove this label"
                      role="button"
                      class="close"
                    >
                      <md-icon>close</md-icon>
                    </md-icon-button>
                  `
                : nothing}

              <prisma-text
                class="label-text"
                variant="label"
                size="${this.type === 'regular' ? 'large' : 'medium'}"
              >
                ${this.label}
              </prisma-text>

              ${this.indicator
                ? html`
                    <prisma-badge
                      color="inherit"
                      type="circle"
                      value=${this.indicator}
                      ?disabled=${this.disabled}
                    >
                    </prisma-badge>
                  `
                : nothing}
            </button>

            <prisma-tooltip
              label
              .text=${this.label}
              .for=${() => this.shadowRoot!.querySelector(`#${this.id}`)!}
            >
            </prisma-tooltip>
          `
        : nothing}
    `;
  }
}

/** Event data types for PrismaLabel */
export interface PrismaLabelDetail {
  id?: string;
  color: Exclude<Color, 'neutral' | 'neutral-variant'>;
  label: string;
  indicator?: string;
  selected: boolean;
}

/**
 * Event types for PrismaLabel
 */
export enum PrismaLabelEventType {
  SELECTED = 'prisma-label-selected',
  CLICKED = 'prisma-label-clicked',
  REMOVED = 'prisma-label-removed'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-label': PrismaLabel;
  }
}
