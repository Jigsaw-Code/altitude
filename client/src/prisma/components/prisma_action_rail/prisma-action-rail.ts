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

import '@material/web/menu/menu';
import '@material/web/menu/menu-item';
import '../prisma_action_button/prisma-action-button';
import '../prisma_icon/prisma-icon';

import { MdMenu } from '@material/web/menu/menu';
import { html, nothing, TemplateResult } from 'lit';
import {
  customElement,
  property,
  query,
  queryAll,
  queryAssignedNodes,
  state
} from 'lit/decorators.js';
import { ifDefined } from 'lit/directives/if-defined.js';
import { repeat } from 'lit/directives/repeat.js';

import { MoreItems } from '../../models/moreitems.model';
import { BaseComponent } from '../../utils/base-component';
import { emit } from '../../utils/event';
import {
  PrismaActionButton,
  PrismaActionButtonEventType
} from '../prisma_action_button/prisma-action-button';

import { styles } from './prisma-action-rail.css';

/**
 * Action rail component provide ergonomic access to actions and destinations
 * in an app.
 *
 * @soyCompatible
 * @final
 * @suppress {visibility}
 */
@customElement('prisma-action-rail')
export class PrismaActionRail extends BaseComponent {
  static override styles = styles;

  /** PrismaActionRail.withMoreItems - if true, enable more items */
  @property({ type: Array, attribute: 'with-more-items', reflect: true })
  withMoreItems = false;

  /** PrismaActionRail.moreItemsTop - handles items in top more menu */
  @property({ type: Array, attribute: 'more-items-top', reflect: true })
  moreItemsTop: MoreItems[] = [];

  /** PrismaActionRail.moreItemsBottom - handles items in more menu bottom */
  @property({ type: Array, attribute: 'more-items-bottom', reflect: true })
  moreItemsBottom: MoreItems[] = [];

  /** PrismaActionRail.openMoreMenuTop - Opens top more menu */
  @property({ type: Boolean, attribute: 'open-more-menu-top', reflect: true })
  openMoreMenuTop = false;

  /** PrismaActionRail.openMoreMenuBottom - Opens bottom more menu */
  @property({
    type: Boolean,
    attribute: 'open-more-menu-bottom',
    reflect: true
  })
  openMoreMenuBottom = false;

  /**
   * PrismaActionRail.positioning - define action-rail position just to display
   * more items on the correct side
   */
  @property() positioning: 'left' | 'right' = 'left';

  // Private properties used for track the visibility of actions buttons in main
  // slot or more menu.
  @state() itemsTop: MoreItems[] = [];
  @state() itemsBottom: MoreItems[] = [];

  // used to determine container top size.
  @query('.container-slot-top', true)
  private readonly containerTop!: HTMLDivElement;
  // used to determine action buttons size in top slot and handle visibility.
  @queryAssignedNodes({ slot: 'top', flatten: true })
  private readonly actionButtonsTop!: HTMLElement[];
  // used to handle visibility of list items in more menu top.
  @queryAll('.list-item-more-top')
  private readonly listItemMoreTop!: HTMLElement[];
  // used to handle open and close more menu top.
  @query('#btn-more-top', true) private readonly buttonMoreTop!: HTMLDivElement;
  // used to track the more menu top.
  @query('#menu-top', true) private readonly menuTop!: MdMenu;
  // used to determine container bottom size.
  @query('.container-slot-bottom', true)
  private readonly containerBottom!: HTMLDivElement;
  // used to determine action buttons size in bottom slot and handle visibility.
  @queryAssignedNodes({ slot: 'bottom', flatten: true })
  private readonly actionButtonsBottom!: HTMLElement[];
  // used to handle visibility of list items in more menu bottom.
  @queryAll('.list-item-more-bottom')
  private readonly listItemMoreBottom!: HTMLElement[];
  // used to handle open and close more menu bottom.
  @query('#btn-more-bottom', true)
  private readonly buttonMoreBottom!: HTMLDivElement;
  // used to track the more menu bottom.
  @query('#menu-bottom', true) private readonly menuBottom!: MdMenu;

  // Opens and close the more menu top.
  private toggleMoreMenuTop(): void {
    this.openMoreMenuTop = !this.openMoreMenuTop;
    this.openMoreMenuTop
      ? (this.menuTop.open = true)
      : (this.menuTop.open = false);
    emit(this, PrismaActionRailEventType.MORE_MENU_TOP_OPEN, {
      detail: this.openMoreMenuTop
    });
  }

  // Open and close the more menu bottom.
  private toggleMoreMenuBottom(): void {
    this.openMoreMenuBottom = !this.openMoreMenuBottom;
    this.openMoreMenuBottom
      ? (this.menuBottom.open = true)
      : (this.menuBottom.open = false);
    emit(this, PrismaActionRailEventType.MORE_MENU_BOTTOM_OPEN, {
      detail: this.openMoreMenuBottom
    });
  }

  // Handle the click event emitted by slotted prisma-action-button,
  // activating / deactivating the corresponding more item.
  handleActionButtonClick(event: Event) {
    if (event) {
      const detail = (event as CustomEvent).detail;
      const allItems = [...this.itemsTop, ...this.itemsBottom];

      allItems.forEach((eachItem: MoreItems) => {
        const icon = eachItem.icon;
        const text = eachItem.text;

        if (icon === detail.icon && text === detail.tooltip) {
          if (detail.selected) {
            eachItem.activated = false;
          } else {
            eachItem.activated = true;
          }
        }
      });
      this.requestUpdate();
    }
  }

  // Handle the click event emitted by more item,
  // activating / deactivating the more item and the corresponding
  // prisma-action-button.
  private handleMoreItemClick(item: MoreItems): void {
    if (item.buttonType === 'select') {
      const allItems = [...this.itemsTop, ...this.itemsBottom];
      const allListItems = [
        ...this.listItemMoreTop,
        ...this.listItemMoreBottom
      ];
      const allActionButtons = [
        ...this.actionButtonsTop,
        ...this.actionButtonsBottom
      ];

      allListItems.forEach((eachListItem: HTMLElement) => {
        const index = eachListItem.getAttribute('index');
        const intIndex = Number(index);

        if (intIndex === item.index) {
          const intIndex = Number(item.index);
          if (!item.activated) {
            eachListItem.setAttribute('activated', '');
            allActionButtons[intIndex].setAttribute('selected', '');
            allItems[intIndex].activated = true;
          } else {
            eachListItem.removeAttribute('activated');
            allActionButtons[intIndex].removeAttribute('selected');
            allItems[intIndex].activated = false;
          }
        }
      });
    }
    emit(this, PrismaActionRailEventType.MORE_MENU_ITEM_CLICKED, {
      detail: item
    });
    this.requestUpdate();
  }

  // Handle the overflowing prisma-action-buttons in slot-top.
  // When screen resizes the offscreen prisma-action-buttons instead of
  // overflowing the slot-top, it append the items to a 'more' button.
  handleOverflowTop(event?: Event) {
    const containerHeight = this.containerTop?.clientHeight;
    let actionButtonsHeight =
      this.actionButtonsTop.length > 0
        ? this.actionButtonsTop[0].offsetHeight * 2
        : 0;
    const hiddenItems = new Set<number>();

    if (!this.withMoreItems) {
      return;
    }

    this.actionButtonsTop.forEach((eachButton: HTMLElement, index: number) => {
      if (containerHeight >= actionButtonsHeight) {
        actionButtonsHeight += this.actionButtonsTop[index].offsetHeight;
        eachButton.classList.remove('hidden');

        if (this.itemsTop.length > 0 && this.moreItemsTop.length > 0) {
          this.buttonMoreTop.classList.remove('hidden');
          emit(this, PrismaActionRailEventType.MORE_MENU_TOP_VISIBLE);
        } else {
          this.buttonMoreTop.classList.add('hidden');
          emit(this, PrismaActionRailEventType.MORE_MENU_TOP_HIDDEN);
        }
      } else {
        hiddenItems.add(index);
        eachButton.classList.add('hidden');
        this.buttonMoreTop.classList.remove('hidden');
        emit(this, PrismaActionRailEventType.MORE_MENU_TOP_VISIBLE);
      }
      this.listItemMoreTop.forEach(
        (eachListItem: HTMLElement, index: number) => {
          if (hiddenItems.has(index)) {
            eachListItem.classList.remove('hidden');
          } else {
            eachListItem.classList.add('hidden');
          }
        }
      );
    });
  }

  // Handle the overflowing prisma-action-buttons in slot-bottom.
  // When screen resizes the offscreen prisma-action-buttons instead of
  // overflowing the slot-bottom, it append the items to a 'more' button.
  handleOverflowBottom(event?: Event) {
    const containerHeight = this.containerBottom?.clientHeight;
    let actionButtonsHeight =
      this.actionButtonsBottom.length > 0
        ? this.actionButtonsBottom[0].offsetHeight * 2
        : 0;
    const hiddenItems = new Set<number>();

    if (!this.withMoreItems) {
      return;
    }

    this.actionButtonsBottom.forEach(
      (eachButton: HTMLElement, index: number) => {
        if (containerHeight >= actionButtonsHeight) {
          actionButtonsHeight += this.actionButtonsBottom[index].offsetHeight;
          eachButton.classList.remove('hidden');

          if (this.itemsBottom.length > 0 && this.moreItemsBottom.length > 0) {
            this.buttonMoreBottom.classList.remove('hidden');
            emit(this, PrismaActionRailEventType.MORE_MENU_BOTTOM_VISIBLE);
          } else {
            this.buttonMoreBottom.classList.add('hidden');
            emit(this, PrismaActionRailEventType.MORE_MENU_BOTTOM_HIDDEN);
          }
        } else {
          hiddenItems.add(index);
          eachButton.classList.add('hidden');
          this.buttonMoreBottom.classList.remove('hidden');
          emit(this, PrismaActionRailEventType.MORE_MENU_BOTTOM_VISIBLE);
        }
        this.listItemMoreBottom.forEach(
          (eachListItem: HTMLElement, index: number) => {
            if (hiddenItems.has(index)) {
              eachListItem.classList.remove('hidden');
            } else {
              eachListItem.classList.add('hidden');
            }
          }
        );
      }
    );
  }

  // Prepare items to provide unified data to another methods.
  async setUpSlotItems() {
    let index = 0;

    if (!this.withMoreItems) {
      return;
    }

    this.actionButtonsTop.forEach((item: HTMLElement) => {
      const visible = item.classList.contains('hidden');
      if (!(item instanceof PrismaActionButton)) {
        item = item.querySelector('prisma-action-button') as PrismaActionButton;
      }
      this.itemsTop.push({
        index: index ?? undefined,
        icon: item.getAttribute('icon') ?? undefined,
        text: item.getAttribute('tooltip') ?? undefined,
        buttonType: item.getAttribute('button-type') ?? undefined,
        activated: item.hasAttribute('selected') ?? undefined,
        visible: visible ?? undefined
      });
      index++;
    });

    this.actionButtonsBottom.forEach((item: HTMLElement) => {
      const visible = item.classList.contains('hidden');
      if (!(item instanceof PrismaActionButton)) {
        item = item.querySelector('prisma-action-button') as PrismaActionButton;
      }
      this.itemsBottom.push({
        index: index ?? undefined,
        icon: item.getAttribute('icon') ?? undefined,
        text: item.getAttribute('tooltip') ?? undefined,
        buttonType: item.getAttribute('button-type') ?? undefined,
        activated: item.hasAttribute('selected') ?? undefined,
        visible: visible ?? undefined
      });
      index++;
    });

    this.requestUpdate();
    await this.updateComplete;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener('resize', (event) => {
      this.handleOverflowTop(event);
      this.handleOverflowBottom(event);
    });
    this.addEventListener(PrismaActionButtonEventType.SELECTED, (event) => {
      this.handleActionButtonClick(event);
    });
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener('resize', (event) => {
      this.handleOverflowTop(event);
      this.handleOverflowBottom(event);
    });
    this.removeEventListener(PrismaActionButtonEventType.SELECTED, (event) => {
      this.handleActionButtonClick(event);
    });
  }

  override async firstUpdated() {
    await this.updateComplete;
    this.handleOverflowTop();
    this.handleOverflowBottom();
    await this.setUpSlotItems();
  }

  private moreMenuTop(): TemplateResult {
    return html`
      <prisma-action-button
        @click=${this.toggleMoreMenuTop}
        id="btn-more-top"
        class="btn-more hidden"
        type="square"
        variation="filled-tonal"
        icon="more_horiz"
        size="medium"
      >
      </prisma-action-button>
      <md-menu
        quick
        role="menu"
        id="menu-top"
        positioning="fixed"
        anchor="btn-more-top"
        xOffset="${this.positioning === 'left' ? '10' : '0'}"
        menu-corner="${this.positioning === 'left' ? 'end-start' : 'end-end'}"
        anchor-corner="${this.positioning === 'left' ? 'end-end' : 'end-start'}"
        ?open=${this.openMoreMenuTop}
        @close-menu=${this.toggleMoreMenuTop}
      >
        ${this.itemsTop.length > 0
          ? repeat(this.itemsTop, (item) => {
              return html`
                <md-menu-item
                  value="${item.index || ''}"
                  class="list-item-more-top ${item.visible ? '' : 'hidden'}"
                  item-end=${item.icon || ''}
                  @click=${() => {
                    this.handleMoreItemClick(item);
                  }}
                  ?activated=${item.activated || false}
                  ?selected=${item.activated || false}
                >
                  <prisma-icon
                    slot="start"
                    id="prisma-icon-${item.icon}"
                    color="inherit"
                    optical-size="24"
                    >${item.icon}</prisma-icon
                  >
                  <prisma-text slot="headline">${item.text || ''}</prisma-text>
                </md-menu-item>
              `;
            })
          : nothing}
        ${this.moreItemsTop.length > 0
          ? repeat(this.moreItemsTop, (item) => {
              return html`
                <md-menu-item
                  value="${item.index || ''}"
                  class="list-item-more-top-fixed"
                  item-end=${item.icon || ''}
                  @click=${() => {
                    this.handleMoreItemClick(item);
                  }}
                  ?activated=${item.activated || false}
                  ?selected=${item.activated || false}
                >
                  <prisma-text slot="headline">${item.text || ''}</prisma-text>
                  <prisma-icon
                    slot="start"
                    id="prisma-icon-${item.icon}"
                    color="inherit"
                    optical-size="24"
                    >${item.icon}</prisma-icon
                  >
                </md-menu-item>
              `;
            })
          : nothing}
      </md-menu>
    `;
  }

  private moreMenuBottom(): TemplateResult {
    return html`
      <prisma-action-button
        @click=${this.toggleMoreMenuBottom}
        id="btn-more-bottom"
        class="btn-more hidden"
        type="square"
        variation="filled-tonal"
        icon="more_horiz"
        size="medium"
      >
      </prisma-action-button>
      <md-menu
        quick
        role="menu"
        id="menu-bottom"
        anchor="btn-more-bottom"
        anchor-corner="${this.positioning === 'left'
          ? 'start-end'
          : 'start-start'}"
        menu-corner="${this.positioning === 'left'
          ? 'start-start'
          : 'start-end'}"
        positioning="fixed"
        xOffset="${this.positioning === 'left' ? '10' : '0'}"
        ?open=${this.openMoreMenuBottom}
        @close-menu=${this.toggleMoreMenuBottom}
      >
        ${this.itemsBottom.length > 0
          ? repeat(this.itemsBottom, (item) => {
              return html`
                <md-menu-item
                  value="${item.index || ''}"
                  class="list-item-more-bottom ${item.visible ? '' : 'hidden'}"
                  @click=${() => {
                    this.handleMoreItemClick(item);
                  }}
                  ?activated=${item.activated || false}
                  ?selected=${item.activated || false}
                >
                  <prisma-icon
                    slot="start"
                    id="prisma-icon-${item.icon}"
                    color="inherit"
                    optical-size="24"
                    >${item.icon}</prisma-icon
                  >
                  <prisma-text slot="headline">${item.text || ''}</prisma-text>
                </md-menu-item>
              `;
            })
          : nothing}
        ${this.moreItemsBottom.length > 0
          ? repeat(this.moreItemsBottom, (item) => {
              return html`
                <md-menu-item
                  value="${item.index || ''}"
                  class="list-item-more-bottom-fixed"
                  @click=${() => {
                    this.handleMoreItemClick(item);
                  }}
                  ?activated=${item.activated || false}
                  ?selected=${item.activated || false}
                >
                  <prisma-icon
                    slot="start"
                    id="prisma-icon-${item.icon}"
                    color="inherit"
                    optical-size="24"
                    >${item.icon}</prisma-icon
                  >
                  <prisma-text slot="headline">${item.text || ''}</prisma-text>
                </md-menu-item>
              `;
            })
          : nothing}
      </md-menu>
    `;
  }

  protected override render(): TemplateResult {
    return html`
      <div
        class="prisma-action-rail ${this.className} ${this.positioning}"
        aria-label=${ifDefined(
          this.ariaLabel !== null ? this.ariaLabel : undefined
        )}
        aria-hidden=${ifDefined(
          this.ariaHidden === 'true' ? this.ariaHidden : undefined
        )}
      >
        <div class="container-slot-top">
          <slot name="top"></slot>
          ${this.withMoreItems ? this.moreMenuTop() : nothing}
        </div>

        <div class="container-slot-bottom">
          ${this.withMoreItems ? this.moreMenuBottom() : nothing}
          <slot name="bottom"></slot>
        </div>
      </div>
    `;
  }
}

/**
 * Event types for PrismaActionRail
 */
export enum PrismaActionRailEventType {
  MORE_MENU_TOP_OPEN = 'prisma-action-rail-more-menu-top-open',
  MORE_MENU_TOP_VISIBLE = 'prisma-action-rail-button-more-top-visible',
  MORE_MENU_TOP_HIDDEN = 'prisma-action-rail-button-more-top-hidden',
  MORE_MENU_BOTTOM_OPEN = 'prisma-action-rail-more-menu-bottom-open',
  MORE_MENU_BOTTOM_VISIBLE = 'prisma-action-rail-button-more-bottom-visible',
  MORE_MENU_BOTTOM_HIDDEN = 'prisma-action-rail-button-more-bottom-hidden',
  MORE_MENU_ITEM_CLICKED = 'prisma-action-rail-more-item-clicked'
}

declare global {
  interface HTMLElementTagNameMap {
    'prisma-action-rail': PrismaActionRail;
  }
}
