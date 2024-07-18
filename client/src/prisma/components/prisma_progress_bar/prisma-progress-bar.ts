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
import { styleMap } from 'lit-html/directives/style-map.js';
import { customElement, property } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import type {
  ProgressBarLegendListOptions,
  ProgressBarType
} from '../../models/progress-bar.model';

import {
  type Color,
  type ColorRef,
  type ColorVariation
} from '../../models/color.model';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';
import { setTokenColor } from '../../utils/set-token-color';

import { styles } from './prisma-progress-bar.css';

/**
 * Progress bar inform users about the status of ongoing processes, such as
 * tasks assigned to the user or submitting a form.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-progress-bar')
export class PrismaProgressBar extends BaseComponent {
  static override styles = styles;

  /** PrismaProgressBar.type - defines the type between 'linear' or 'legend' */
  @property({ reflect: true }) type: ProgressBarType = 'linear';

  /** PrismaProgressBar.current - a number to represent the current progress */
  @property({ type: Number, reflect: true }) current?: number;

  /** PrismaProgressBar.total - a number to represent the total progress */
  @property({ type: Number, reflect: true }) total = 0;

  /** PrismaProgressBar.primaryContent - the top-left text of the bar */
  @property({ attribute: 'primary-content', reflect: true })
  primaryContent?: string;

  /** PrismaProgressBar.secondaryContent - the top-right text of the bar */
  @property({ attribute: 'secondary-content', reflect: true })
  secondaryContent?: string;

  /** PrismaProgressBar.legends - an object with legengds related to the progress */
  @property({ type: Object, reflect: true })
  legends?: ProgressBarLegendListOptions;

  /** PrismaProgressBar.color - sets the color scheme */
  @property({ reflect: true }) color: Color = 'primary';

  /**
   * PrismaProgressBar.colorRef - define an specific color reference from the
   * palette
   */
  @property({ attribute: 'color-ref', reflect: true }) colorRef?: ColorRef;

  /**
   * PrismaProgressBar.colorVariation - define an specific variation to the
   * color prop
   */
  @property({ attribute: 'color-variation', reflect: true })
  colorVariation?: ColorVariation;

  renderLinearBar() {
    if (!this.current) {
      return;
    }

    //  Emits an event when “current” exceeds “total” reporting the wrong use.
    if (this.current > this.total) {
      const detail = `The "current" exceeds the "total". Please see the doc: (internal)`;
      emit(this, PrismaProgressBarEventType.CURRENT_EXCEEDS_TOTAL, { detail });
    }

    const pct = (this.current / this.total) * 100;
    const colorToken = setTokenColor(
      this.color,
      this.colorVariation,
      this.colorRef
    );
    const linearBarStyles = {
      width: `${pct}%`,
      backgroundColor: `var(${colorToken})`
    };

    return html`<div
      class="progress"
      style="${styleMap(linearBarStyles)}"
    ></div>`;
  }

  renderLegendBar() {
    let legendsQuantityTotal = 0;

    if (!this.legends) {
      return;
    }

    return this.legends.legend.map((item) => {
      legendsQuantityTotal += item.quantity;

      //  Emits an event when “legend.quantity” exceeds the “total” reporting the wrong use.
      if (legendsQuantityTotal > this.total) {
        const detail = `The total of "legend.quantity" exceeds the "total". Please see the doc: (internal)`;
        emit(this, PrismaProgressBarEventType.LEGEND_QUANTITY_EXCEEDS_TOTAL, {
          detail
        });
      }

      const pct = (item.quantity / this.total) * 100;
      const colorToken = setTokenColor(
        item.color,
        item.colorVariation,
        item.colorRef
      );
      const legendBarStyles = {
        width: `${pct}%`,
        backgroundColor: `var(${colorToken})`
      };
      return html`
        <div class="progress" style=${styleMap(legendBarStyles)}></div>
      `;
    });
  }

  private renderLegend() {
    // When we don't have legends or "showLegend" is false end the process.
    if (!this.legends || !this.legends.showLegend) {
      return;
    }

    return this.legends.legend.map((item) => {
      const colorToken = setTokenColor(
        item.color,
        item.colorVariation,
        item.colorRef
      );
      const legendStyles = {
        backgroundColor: `var(${colorToken})`
      };
      return html`
        <div class="legend">
          <div class="badge" style=${styleMap(legendStyles)}></div>
          <prisma-text size="small">${item.title}</prisma-text>
          <prisma-text as="b" size="small" class="quantity"
            >${item.quantity}</prisma-text
          >
        </div>
      `;
    });
  }

  protected override render(): TemplateResult {
    return html`
      <div
        role="progressbar"
        name="prisma-progress-bar"
        class="progress-bar ${this.className}"
        aria-label=${this.ariaLabel || 'Shows progress'}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <div class="text-content">
          <prisma-text>${this.primaryContent}</prisma-text>
          <prisma-text size="small">${this.secondaryContent}</prisma-text>
        </div>

        ${this.type === 'legend'
          ? html`
              <div class="bar">${this.renderLegendBar()}</div>
              <div class="legends">${this.renderLegend()}</div>
            `
          : html` <div class="bar">${this.renderLinearBar()}</div> `}
      </div>
    `;
  }
}

/**
 * Event types for PrismaProgressBar
 */
export enum PrismaProgressBarEventType {
  CURRENT_EXCEEDS_TOTAL = 'current-exceeds-total',
  LEGEND_QUANTITY_EXCEEDS_TOTAL = 'legend-quantity-exceeds-total'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-progress-bar': PrismaProgressBar;
  }
}
