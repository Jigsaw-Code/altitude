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
import '../../../prisma_icon/prisma-icon';
import '../../../prisma_tooltip/prisma-tooltip';

import { html, nothing, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import { repeat } from 'lit/directives/repeat.js';

import { type Color } from '../../../../models/color.model';
import { Icon, IconFill } from '../../../../models/icon.model';
import { BaseComponent } from '../../../../utils/base-component';
import { emit } from '../../../../utils/event';

import { styles } from './prisma-icon-group.css';

/**
 * Icon group is a set of icon buttons that represents actions and features in a
 * screen.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-icon-group')
export class PrismaIconGroup extends BaseComponent {
  static override styles = styles;

  /** PrismaIconGroup.icons - array of icons  */
  @property({ type: Array, reflect: true }) icons: Icon[] = [];

  /** PrismaIconGroup.activeColor - color of the active icon  */
  @property({ type: String, attribute: 'active-color', reflect: true })
  activeColor: Color = 'primary';

  private handleToolbarMoreSelected(evt: Event): void {
    const event = evt as CustomEvent;
    const selectedItem = event.detail as string;

    if (this.icons instanceof Array) {
      this.icons.forEach((icon) => {
        if (icon.iconOff === selectedItem || icon.iconKey === selectedItem) {
          // This condition checks if it's a toggle
          icon.activated = icon.iconOff ? !icon.activated : false;
        }
      });
    }

    this.requestUpdate();
  }

  private handleIconButtonClick(icon: string): void {
    const currentIcon: Icon = this.icons.filter(
      (current) => current.iconKey === icon
    )[0];
    emit(this, PrismaIconGroupEventType.SELECTED, { detail: currentIcon });
  }

  private handleIconButtonToggle(evt: CustomEvent): void {
    const iconButton = evt.currentTarget as HTMLElement;
    const selectedIcon: Icon = {
      ...this.icons.filter((icon) => icon.iconKey === iconButton.id)[0]
    };
    selectedIcon.activated = iconButton.hasAttribute('selected');
    emit(this, PrismaIconGroupEventType.SELECTED, { detail: selectedIcon });
  }

  private useIconButton(
    selector: string,
    iconKey: string,
    text: string,
    fill?: IconFill
  ): TemplateResult {
    return html`
      <md-icon-button
        id="${iconKey}"
        class="${selector}"
        aria-label="${text}"
        @click="${() => {
          this.handleIconButtonClick(iconKey);
        }}"
      >
        <prisma-icon
          fill="${fill || 0}"
          weight="${400}"
          font-style="outlined"
          optical-size=${24}
          color="inherit"
          >${iconKey}</prisma-icon
        >
      </md-icon-button>
    `;
  }

  private useIconButtonToggle(
    activeColor: Color,
    selector: string,
    iconKey: string,
    fill?: IconFill,
    iconOff?: string,
    activated?: boolean
  ): TemplateResult {
    return html`
      <md-icon-button
        toggle
        id="${iconKey}"
        class="${selector + ' toggle-' + activeColor}"
        aria-label="${`Toggle ${iconKey} option`}"
        ?selected="${activated || false}"
        @click="${this.handleIconButtonToggle}"
      >
        <prisma-icon
          fill="${fill || 0}"
          weight="${400}"
          font-style="outlined"
          optical-size=${24}
          color="inherit"
          >${iconOff || iconKey}</prisma-icon
        >
        <prisma-icon
          fill="${fill || 0}"
          weight="${400}"
          font-style="outlined"
          optical-size=${24}
          color="inherit"
          slot="selected"
          >${iconKey}</prisma-icon
        >
      </md-icon-button>
    `;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this.parentElement?.addEventListener(
      PrismaIconGroupEventType.SELECTED,
      (e) => {
        this.handleToolbarMoreSelected(e);
      }
    );
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.parentElement?.removeEventListener(
      PrismaIconGroupEventType.SELECTED,
      (e) => {
        this.handleToolbarMoreSelected(e);
      }
    );
  }

  protected override render(): TemplateResult | typeof nothing {
    const { activeColor } = this;

    return html`
      <div
        class="prisma-icon-group"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(this.ariaLabel ?? undefined)}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        ${repeat(
          this.icons,
          (icon: Icon) => icon.iconKey,
          ({
            iconKey,
            iconOff,
            buttonType,
            text,
            activated,
            shortcut,
            fill
          }: Icon) => {
            const selector = iconKey;
            let element: TemplateResult | typeof nothing;

            if (buttonType === 'select') {
              element = this.useIconButtonToggle(
                activeColor,
                selector,
                iconKey,
                fill,
                iconOff,
                activated
              );
            } else if (buttonType === 'button') {
              element = this.useIconButton(selector, iconKey, text, fill);
            } else {
              element = nothing;
            }

            return html`
              ${element}
              <prisma-tooltip
                .for=${() => this.shadowRoot?.querySelector(`.${selector}`)!}
                text=${text}
                .shortcut=${shortcut}
              >
              </prisma-tooltip>
            `;
          }
        )}
      </div>
    `;
  }
}

/**
 * Event types for PrismaIconGroup
 */
export enum PrismaIconGroupEventType {
  SELECTED = 'prisma-icon-group-selected'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-icon-group': PrismaIconGroup;
  }
}
