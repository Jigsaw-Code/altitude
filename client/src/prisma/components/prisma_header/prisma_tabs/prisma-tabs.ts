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

import '@material/web/button/outlined-button';
import '@material/web/icon/icon';
import '@material/web/menu/menu';
import '@material/web/menu/menu-item';
import '@material/web/tabs/primary-tab';
import '@material/web/tabs/tabs';
import '../../prisma_text/prisma-text';

import { html, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import { repeat } from 'lit/directives/repeat.js';

import { BaseComponent } from '../../../utils/base-component';
import { debounce, emit } from '../../../utils/event';

import { styles } from './prisma-tabs.css';

/** Tab model represents an array of items to be used as tabs. */
export interface Tab {
  /** Tab represents the name of the tab. */
  tab: string;
  /** Index represents a unique number related to the tab. */
  index?: number;
  /**
   * Collapse means items that should be showing in more
   * button by default.
   */
  collapse?: boolean;
}

/**
 * Tabs make it easy to explore and switch between different views
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-tabs')
export class PrismaTabs extends BaseComponent {
  static override styles = styles;

  /** PrismaTabs.tabs - array with tabs */
  @property({ type: Array, reflect: true, attribute: 'tabs' }) tabs: Tab[] = [];

  /** PrismaTabs.tabsMore - array with tabs for the more menu */
  @property({ type: Array, reflect: true, attribute: 'tabs-more' })
  tabsMore: Tab[] = [];

  /**
   * PrismaTabs.defaultTab - index from `tabs` to indicate which tab should be
   * opened by default
   */
  @property({ type: Number, reflect: true, attribute: 'default-tab' })
  defaultTab = 0;

  /** PrismaTabs.morePositionX - set more menu horizontally position */
  @property({ type: Number, reflect: true, attribute: 'more-position-x' })
  morePositionX = 0;

  /** PrismaTabs.noBorder - removes the border-bottom if its true */
  @property({ type: Boolean, reflect: true, attribute: 'no-border' })
  noBorder?: boolean;

  @state() isMoreOpen = false;

  private handleDefaultTab(): void {
    if (this.defaultTab > 0) {
      emit(this, 'prisma-tabs-default-tab-defined', {
        detail: this.defaultTab
      });
    }

    const tabBarChildren = Array.from(
      this.shadowRoot!.querySelectorAll('md-primary-tab')
    );
    const moreChildren = Array.from(
      this.shadowRoot!.querySelectorAll('md-menu-item')
    );

    if (tabBarChildren.length > 0 && moreChildren.length > 0) {
      tabBarChildren.forEach((item, i) => {
        if (item.hasAttribute('active')) {
          moreChildren[i].setAttribute('selected', 'true');
        }
      });
    }
  }

  private handleTabClick(item: Tab): void {
    if (item.collapse) {
      const tabBar = this.shadowRoot!.querySelector('.prisma-tab-bar');
      tabBar!.removeAttribute('activeIndex');
    } else {
      const tabBarChildren = Array.from(
        this.shadowRoot!.querySelectorAll('md-primary-tab')
      );
      const moreChildren = Array.from(
        this.shadowRoot!.querySelectorAll('md-menu-item')
      );

      if (tabBarChildren.length > 0 && moreChildren.length > 0) {
        tabBarChildren.forEach((item, i) => {
          if (item.hasAttribute('active')) {
            moreChildren[i].setAttribute('selected', 'true');
          }
        });
      }
    }

    emit(this, 'prisma-tab-clicked', { detail: item });

    this.requestUpdate();
  }

  private handleMoreOpen(): void {
    this.isMoreOpen = !this.isMoreOpen;
    const detail = {
      isMoreOpen: this.isMoreOpen
    };
    emit(this, 'prisma-tab-more-open', { detail });
    this.requestUpdate();
  }

  // This method is responsible to hide offscreen tabs and instead of
  // showing a vertical scroll, it append the items to a 'more' button
  // @return void
  handleResize(): void {
    window.requestAnimationFrame(() => {
      const tabBar = this.shadowRoot!.querySelector('.prisma-tab-bar')!;
      const tabBarWidth = tabBar.clientWidth;
      const tabBarChildren = Array.from(
        this.shadowRoot!.querySelectorAll('md-primary-tab')
      );
      const moreList = this.shadowRoot!.querySelector('md-menu');
      const moreChildren = Array.from(
        this.shadowRoot!.querySelectorAll('md-menu-item')
      );
      const moreBtn = this.shadowRoot!.querySelector('.more-btn');
      const hiddenItems: number[] = [];

      // When resize screen, starts the width count with the width of a single
      // tab
      let childrenWidth =
        tabBarChildren.length > 0 ? tabBarChildren[0].clientWidth : 0;

      tabBarChildren.forEach((item, i) => {
        if (tabBarWidth >= childrenWidth) {
          childrenWidth += tabBarChildren[i].clientWidth;
          item.classList.remove('hidden');

          if (this.tabsMore?.length === 0) {
            if (moreBtn && moreList) {
              moreBtn.classList.add('hidden');
              moreList.classList.add('hidden');
            }
            emit(this, 'prisma-tab-more-btn-hidden');
          }
        } else {
          item.classList.add('hidden');
          hiddenItems.push(i);
          if (moreBtn && moreList) {
            moreList.classList.remove('hidden');
            moreBtn.classList.remove('hidden');
          }
          emit(this, 'prisma-tab-more-btn-visible');
        }
      });

      if (moreChildren.length > 0) {
        moreChildren.forEach((item, i) => {
          if (!hiddenItems.includes(i)) {
            if (!item.classList.contains('collapse-more')) {
              item.classList.add('hidden');
            }
          } else {
            item.classList.remove('hidden');
          }
        });
      }
    });
  }

  override updated(): void {
    this.handleDefaultTab();
    this.handleResize();
  }

  override firstUpdated(): void {
    if (this.tabsMore.length === 0) return;

    this.tabsMore.forEach((item) => {
      item.collapse = true;
    });
  }

  override connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener(
      'resize',
      debounce(() => {
        this.handleResize();
      })
    );
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener(
      'resize',
      debounce(() => {
        this.handleResize();
      })
    );
  }

  protected override render(): TemplateResult {
    // Add explicit role="tablist" and role="tab" for a11y tests rather than
    // using ElementInternals.role.
    const noBorderClass = this.noBorder ? 'no-border' : '';

    return html`
      <div
        class="prisma-tabs ${this.className} ${noBorderClass}"
        role=${ifDefined(this.ariaRole)}
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <md-tabs
          role="tablist"
          .activeTabIndex=${this.defaultTab}
          class="prisma-tab-bar"
        >
          ${this.tabs
            ? html`
                ${repeat(
                  this.tabs,
                  (item) => item.tab,
                  (item) => html`
                    <md-primary-tab
                      role="tab"
                      @click=${() => {
                        this.handleTabClick(item);
                      }}
                      >${item.tab}</md-primary-tab
                    >
                  `
                )}
              `
            : ''}
        </md-tabs>
        <div class="more">
          ${this.tabsMore && this.tabsMore.length > 0
            ? html`
                <md-outlined-button
                  class="more-btn"
                  id="more-btn"
                  trailing-icon
                  aria-label="menu with more tabs"
                  label="more"
                  @click=${this.handleMoreOpen}
                >
                  more
                  <md-icon slot="icon">arrow_drop_down</md-icon>
                </md-outlined-button>
                <md-menu
                  quick
                  role="menu"
                  anchor="more-btn"
                  class="more-list"
                  yOffset="-10"
                  xOffset=${this.morePositionX}
                  @close-menu=${this.handleMoreOpen}
                  ?open=${this.isMoreOpen}
                >
                  ${repeat(
                    [...this.tabs, ...this.tabsMore],
                    (item) => item.tab,
                    (item, index) => {
                      item.index = index;
                      return html`
                        <md-menu-item
                          @click=${() => {
                            this.handleTabClick(item);
                          }}
                          value=${item.index || ''}
                          class=${item.collapse ? 'collapse-more' : ''}
                        >
                          <prisma-text slot="headline"
                            >${item.tab || ''}</prisma-text
                          >
                        </md-menu-item>
                      `;
                    }
                  )}
                </md-menu>
              `
            : ''}
        </div>
      </div>
    `;
  }
}

/**
 * Event types for PrismaTabs
 */
export enum PrismaTabsEventType {
  DEFAULT_TAB_DEFINED = 'prisma-tabs-default-tab-defined',
  TAB_CLICKED = 'prisma-tab-clicked',
  MORE_OPEN = 'prisma-tab-more-open',
  MORE_BUTTON_HIDDEN = 'prisma-tab-more-btn-hidden',
  MORE_BUTTON_VISIBLE = 'prisma-tab-more-btn-visible'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-tabs': PrismaTabs;
  }
}
