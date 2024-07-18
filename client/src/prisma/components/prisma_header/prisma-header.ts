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

import '@material/web/checkbox/checkbox';
import '@material/web/iconbutton/icon-button';
import '../prisma_badge/prisma-badge';
import '../prisma_icon/prisma-icon';
import '../prisma_pagination/prisma-pagination';
import '../prisma_text/prisma-text';
import '../prisma_tooltip/prisma-tooltip';
import './prisma_tab_panel/prisma-tab-panel';
import { PrismaTabs } from './prisma_tabs/prisma-tabs';
import './prisma_toolbar/prisma-toolbar';

import { html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import { ifDefined } from 'lit/directives/if-defined.js';

import {
  type IconFill,
  type IconFontStyle,
  type IconGrade,
  type IconOpticalSize,
  type IconWeight
} from '../../models/icon.model';
import { type As } from '../../models/typography.model';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';

import { styles } from './prisma-header.css';

/**
 * Header displays information and actions at the top of a screen or
 * component.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-header')
export class PrismaHeader extends BaseComponent {
  static override styles = styles;

  /** PrismaHeader.title - a text as a title */
  @property({ reflect: true }) override title = '';

  /** PrismaHeader.titleTag - sets the html tag for the title */
  @property({ reflect: true, attribute: 'title-tag' }) titleTag: As = 'h2';

  /** PrismaHeader.subtitle - a text as subtile */
  @property({ reflect: true }) subtitle?: string;

  /** PrismaHeader.icon - an id from the Material Symbols */
  @property({ reflect: true }) icon?: string;

  /** PrismaHeader.iconFontStyle - changes the icon style */
  @property({ attribute: 'icon-font-style', reflect: true })
  iconFontStyle?: IconFontStyle = 'outlined';

  /** PrismaHeader.iconOpticalSize - changes the icon font size */
  @property({ attribute: 'icon-optical-size', reflect: true })
  iconOpticalSize?: IconOpticalSize = 24;

  /** PrismaHeader.iconFill - changes the icon fill */
  @property({ attribute: 'icon-fill', reflect: true }) iconFill?: IconFill = 0;

  /** PrismaHeader.iconWeight - changes the icon weight */
  @property({ attribute: 'icon-weight', reflect: true })
  iconWeight?: IconWeight = 400;

  /** PrismaHeader.iconGrade - changes the icon grade */
  @property({ attribute: 'icon-grade', reflect: true })
  iconGrade?: IconGrade = 0;

  /**
   * PrismaHeader.shortcutBadge - a keyboard command to be showed in
   * prisma-badge as a shortcut
   */
  @property({ reflect: true, attribute: 'shortcut-badge' })
  shortcutBadge?: string;

  /** PrismaHeader.iconButton - if true, creates a clickable icon */
  @property({ type: Boolean, reflect: true, attribute: 'icon-button' })
  iconButton = false;

  /** PrismaHeader.checkbox - if true, creates a md-checkbox */
  @property({ type: Boolean, reflect: true }) checkbox = false;

  /** PrismaHeader.checked - if true, applies the checked appearence */
  @property({ type: Boolean, reflect: true }) checked = false;

  /**
   * PrismaHeader.roundedTop - if true, applies border-radius on both top left
   * and top right corners
   */
  @property({ type: Boolean, reflect: true, attribute: 'rounded-top' })
  roundedTop = false;

  /**
   * PrismaHeader.roundedBottom - if true, applies border-radius on both bottom
   * left and bottom right corners
   */
  @property({ type: Boolean, reflect: true, attribute: 'rounded-bottom' })
  roundedBottom = false;

  @state() hasPrismaTabs = false;

  private handleIconButton(): void {
    emit(this, PrismaHeaderEventType.BUTTON_CLICK);
  }

  private handleCheckbox(): void {
    emit(this, PrismaHeaderEventType.CHECK);
  }

  private handlePrismaTabs(): void {
    const tabsSlot = this.shadowRoot?.querySelector(
      'slot[name=tabs]'
    ) as HTMLSlotElement;

    if (tabsSlot) {
      const assignedTabs = tabsSlot.assignedElements({ flatten: true });
      this.hasPrismaTabs = assignedTabs.some(
        (item) =>
          item instanceof PrismaTabs || item.querySelector('prisma-tabs')
      );
    }
  }

  override firstUpdated(): void {
    this.handlePrismaTabs();
  }

  protected override render(): TemplateResult {
    const classes = {
      ['prisma-header']: true,
      [this.className]: true,
      ['rounded-top']: this.roundedTop,
      ['rounded-bottom']: this.roundedBottom,
      ['has-checkbox']: this.checkbox,
      ['has-prisma-tabs']: this.hasPrismaTabs
    };

    return html`
      <div
        class=${classMap(classes)}
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <slot name="logo"></slot>

        ${this.icon && !this.iconButton
          ? html`
              <prisma-icon
                font-style=${this.iconFontStyle!}
                optical-size=${this.iconOpticalSize!}
                fill=${this.iconFill!}
                weight=${this.iconWeight!}
                grade=${this.iconGrade!}
                class="icon"
                color="inherit"
              >
                ${this.icon}
              </prisma-icon>
            `
          : nothing}
        ${this.icon && this.iconButton
          ? html`
              <md-icon-button @click=${this.handleIconButton}>
                <prisma-icon
                  font-style=${this.iconFontStyle!}
                  optical-size=${this.iconOpticalSize!}
                  fill=${this.iconFill!}
                  weight=${this.iconWeight!}
                  grade=${this.iconGrade!}
                  class="icon"
                >
                  ${this.icon}
                </prisma-icon>
              </md-icon-button>
            `
          : nothing}
        ${this.checkbox
          ? html`
              <md-checkbox
                @change=${this.handleCheckbox}
                ?checked=${this.checked || false}
                name="checkbox"
                aria-label="checkbox"
                touch-target="wrapper"
              >
              </md-checkbox>
            `
          : nothing}

        <div class="container-titles">
          ${this.title
            ? html`
                <prisma-text
                  as="${this.titleTag}"
                  size="medium"
                  variant="title"
                  class="title"
                >
                  ${this.title}
                </prisma-text>
              `
            : nothing}
          ${this.subtitle
            ? html`
                <prisma-text
                  as="h3"
                  size="small"
                  variant="body"
                  class="subtitle"
                >
                  ${this.subtitle}
                </prisma-text>
              `
            : nothing}
        </div>

        <slot name="badge"></slot>
        <slot name="tabs"></slot>
        <slot class="open-slot"></slot>
        <slot name="pagination"></slot>
        <slot name="toolbar"></slot>

        ${this.shortcutBadge
          ? html`
              <prisma-badge
                type="rounded"
                color="inherit"
                value=${this.shortcutBadge}
              >
              </prisma-badge>
            `
          : nothing}
      </div>
    `;
  }
}

/**
 * Event types for PrismaHeader
 */
export enum PrismaHeaderEventType {
  BUTTON_CLICK = 'prisma-header-button-click',
  CHECK = 'prisma-header-check'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-header': PrismaHeader;
  }
}
