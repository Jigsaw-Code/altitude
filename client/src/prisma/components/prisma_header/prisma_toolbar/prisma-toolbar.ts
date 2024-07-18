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
import '@material/web/menu/menu';
import '@material/web/menu/menu-item';
import '../../prisma_icon/prisma-icon';
import './prisma_icon_group/prisma-icon-group';

import { MdMenu } from '@material/web/menu/menu';
import { html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import { repeat } from 'lit/directives/repeat.js';

import { type Color } from '../../../models/color.model';
import { Icon } from '../../../models/icon.model';
import { BaseComponent } from '../../../utils/base-component';
import { emit } from '../../../utils/event';

import { styles } from './prisma-toolbar.css';
import {
  PrismaIconGroup,
  PrismaIconGroupEventType
} from './prisma_icon_group/prisma-icon-group';

/**
 * Toolbar represents a list of icon groups that represents a set of features
 * in a screen.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-toolbar')
export class PrismaToolbar extends BaseComponent {
  static override styles = styles;

  /** PrismaToolbar.activeColor - color of the active icon */
  @property({ attribute: 'active-color', reflect: true })
  activeColor: Color = 'primary';

  /** PrismaToolbar.moreItems - array of items to show in the more menu */
  @property({ type: Array, attribute: 'more-items', reflect: true })
  moreItems?: Icon[] = [];

  /** PrismaToolbar.open - if true, open the menu options by default  */
  @property({ type: Boolean, reflect: true }) open = false;

  /** PrismaToolbar.morePositionX - set more menu horizontally position */
  @property({ type: Number, reflect: true, attribute: 'more-position-x' })
  morePositionX = 0;

  @state() items: Icon[] = [];

  private toggleMenu(): void {
    const menu = this.shadowRoot!.querySelector('md-menu') as MdMenu;
    this.open = !this.open;
    menu.open = this.open;
  }

  private handleMoreSelected(selectedItem: string): void {
    if (this.moreItems instanceof Array) {
      this.moreItems.forEach((item) => {
        if (item.iconOff === selectedItem || item.iconKey === selectedItem) {
          // This condition checks if it's a toggle
          item.activated = item.iconOff ? !item.activated : false;
        }
      });
    }

    emit(this, PrismaToolbarEventType.MORE_SELECTED, { detail: selectedItem });
  }

  private handleIconGroupSelected(evt: Event): void {
    const event = evt as CustomEvent;
    const selected = event.detail;
    const newItems = this.items.map((item) => {
      if (item.iconKey === selected.iconKey) {
        item = { ...selected, iconGroup: true };
      }
      return item;
    });
    this.items = newItems;
    this.requestUpdate();
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this.addEventListener(PrismaIconGroupEventType.SELECTED, (e) => {
      this.handleIconGroupSelected(e);
    });
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.removeEventListener(PrismaIconGroupEventType.SELECTED, (e) => {
      this.handleIconGroupSelected(e);
    });
  }

  override async firstUpdated() {
    await this.updateComplete;
    const slot = this.shadowRoot!.querySelector('slot')!;
    const assignedElements = slot.assignedElements();

    if (assignedElements instanceof Array) {
      assignedElements.forEach((el) => {
        const iconGroup = el as PrismaIconGroup;

        if (iconGroup.icons instanceof Array) {
          iconGroup.icons.forEach((icon, index) => {
            this.items.push({
              ...icon,
              iconGroup: true
            });
          });
        }
      });

      if (this.moreItems) {
        this.items = [...this.items, ...this.moreItems];
      }
    }

    this.requestUpdate();
  }

  protected override render(): TemplateResult | typeof nothing {
    return html`
      <div
        class="prisma-toolbar ${this.className}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(this.ariaLabel ?? undefined)}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <slot></slot>
        <div class="more">
          ${this.moreItems && this.moreItems.length > 0
            ? html`
                <md-icon-button
                  class="more"
                  @click=${this.toggleMenu}
                  aria-label="Menu with more options"
                  id="anchor"
                >
                  <md-icon>more_horiz</md-icon>
                </md-icon-button>

                <md-menu
                  quick
                  role="menu"
                  anchor="anchor"
                  xOffset="${this.morePositionX}"
                  yOffset="18"
                  @close-menu=${this.toggleMenu}
                >
                  ${repeat(
                    this.moreItems,
                    ({ iconKey }) => `toolbar-more-item-${iconKey}`,
                    ({
                      iconKey,
                      iconOff,
                      text,
                      activated,
                      iconGroup,
                      fill,
                      opticalSize,
                      grade,
                      weight
                    }) => {
                      const currentIcon = activated
                        ? iconKey
                        : iconOff !== undefined
                        ? iconOff
                        : iconKey;
                      return html`
                        <md-menu-item
                          class="${this.activeColor} ${iconGroup
                            ? 'hidden'
                            : ''}"
                          ?active="${activated || false}"
                          ?selected="${activated || false}"
                          @click=${() => {
                            this.handleMoreSelected(currentIcon);
                          }}
                          value=${currentIcon}
                        >
                          <prisma-icon
                            slot="start"
                            color="${activated ? this.activeColor : 'inherit'}"
                            id="prisma-icon-${currentIcon}"
                            fill=${ifDefined(fill)}
                            grade=${ifDefined(grade)}
                            weight=${ifDefined(weight)}
                            optical-size=${opticalSize || 24}
                          >
                            ${currentIcon}
                          </prisma-icon>
                          <prisma-text slot="headline"
                            >${text || ''}</prisma-text
                          >
                        </md-menu-item>
                        <li
                          divider
                          class=${iconGroup ? 'hidden' : ''}
                          role="separator"
                        ></li>
                      `;
                    }
                  )}
                </md-menu>
              `
            : nothing}
        </div>
      </div>
    `;
  }
}

/**
 * Event types for PrismaToolbar
 */
export enum PrismaToolbarEventType {
  MORE_SELECTED = 'prisma-toolbar-more-selected'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-toolbar': PrismaToolbar;
  }
}
