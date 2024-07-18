/**
 * Copyright 2024 Google LLC
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

/**
 * Accessibility Object Model reflective aria property name types.
 */
export type ARIAProperty = Exclude<keyof ARIAMixin, 'role'>;

/**
 * Accessibility Object Model reflective aria properties.
 */
export const ARIA_PROPERTIES: ARIAProperty[] = [
  'ariaAtomic',
  'ariaAutoComplete',
  'ariaBusy',
  'ariaChecked',
  'ariaColCount',
  'ariaColIndex',
  'ariaColSpan',
  'ariaCurrent',
  'ariaDisabled',
  'ariaExpanded',
  'ariaHasPopup',
  'ariaHidden',
  'ariaKeyShortcuts',
  'ariaLabel',
  'ariaLevel',
  'ariaLive',
  'ariaModal',
  'ariaMultiLine',
  'ariaMultiSelectable',
  'ariaOrientation',
  'ariaPlaceholder',
  'ariaPosInSet',
  'ariaPressed',
  'ariaReadOnly',
  'ariaRequired',
  'ariaRoleDescription',
  'ariaRowCount',
  'ariaRowIndex',
  'ariaRowSpan',
  'ariaSelected',
  'ariaSetSize',
  'ariaSort',
  'ariaValueMax',
  'ariaValueMin',
  'ariaValueNow',
  'ariaValueText'
];

/**
 * Accessibility Object Model aria attribute name types.
 */
export type ARIAAttribute = ARIAPropertyToAttribute<ARIAProperty>;

/**
 * Accessibility Object Model aria attributes.
 */
export const ARIA_ATTRIBUTES = ARIA_PROPERTIES.map(ariaPropertyToAttribute);

/**
 * Checks if an attribute is one of the AOM aria attributes.
 *
 * @example
 * isAriaAttribute('aria-label'); // true
 *
 * @param attribute The attribute to check.
 * @return True if the attribute is an aria attribute, or false if not.
 */
export function isAriaAttribute(attribute: string): attribute is ARIAAttribute {
  return attribute.startsWith('aria-');
}

/**
 * Converts an AOM aria property into its corresponding attribute.
 *
 * @example
 * ariaPropertyToAttribute('ariaLabel'); // 'aria-label'
 *
 * @param property The aria property.
 * @return The aria attribute.
 */
export function ariaPropertyToAttribute<K extends ARIAProperty | 'role'>(
  property: K
) {
  return (
    property
      .replace('aria', 'aria-')
      // IDREF attributes also include an "Element" or "Elements" suffix
      .replace(/Elements?/g, '')
      .toLowerCase() as ARIAPropertyToAttribute<K>
  );
}

// Converts an `ariaFoo` string type to an `aria-foo` string type.
type ARIAPropertyToAttribute<K extends string> =
  K extends `aria${infer Suffix}Element${infer OptS}`
    ? `aria-${Lowercase<Suffix>}`
    : K extends `aria${infer Suffix}`
    ? `aria-${Lowercase<Suffix>}`
    : K;

/**
 * An extension of `ARIAMixin` that enforces strict value types for aria
 * properties.
 *
 * This is needed for correct typing in render functions with lit analyzer.
 *
 * @example
 * render() {
 *   const {ariaLabel} = this as ARIAMixinStrict;
 *   return html`
 *     <button aria-label=${ariaLabel || nothing}>
 *       <slot></slot>
 *     </button>
 *   `;
 * }
 */
export interface ARIAMixinStrict extends ARIAMixin {
  ariaAtomic: 'true' | 'false' | null;
  ariaAutoComplete: 'none' | 'inline' | 'list' | 'both' | null;
  ariaBusy: 'true' | 'false' | null;
  ariaChecked: 'true' | 'false' | null;
  ariaColCount: `${number}` | null;
  ariaColIndex: `${number}` | null;
  ariaColSpan: `${number}` | null;
  ariaCurrent:
    | 'page'
    | 'step'
    | 'location'
    | 'date'
    | 'time'
    | 'true'
    | 'false'
    | null;
  ariaDisabled: 'true' | 'false' | null;
  ariaExpanded: 'true' | 'false' | null;
  ariaHasPopup:
    | 'false'
    | 'true'
    | 'menu'
    | 'listbox'
    | 'tree'
    | 'grid'
    | 'dialog'
    | null;
  ariaHidden: 'true' | 'false' | null;
  ariaInvalid: 'true' | 'false' | null;
  ariaKeyShortcuts: string | null;
  ariaLabel: string | null;
  ariaLevel: `${number}` | null;
  ariaLive: 'assertive' | 'off' | 'polite' | null;
  ariaModal: 'true' | 'false' | null;
  ariaMultiLine: 'true' | 'false' | null;
  ariaMultiSelectable: 'true' | 'false' | null;
  ariaOrientation: 'horizontal' | 'vertical' | 'undefined' | null;
  ariaPlaceholder: string | null;
  ariaPosInSet: `${number}` | null;
  ariaPressed: 'true' | 'false' | null;
  ariaReadOnly: 'true' | 'false' | null;
  ariaRequired: 'true' | 'false' | null;
  ariaRoleDescription: string | null;
  ariaRowCount: `${number}` | null;
  ariaRowIndex: `${number}` | null;
  ariaRowSpan: `${number}` | null;
  ariaSelected: 'true' | 'false' | null;
  ariaSetSize: `${number}` | null;
  ariaSort: 'ascending' | 'descending' | 'none' | 'other' | null;
  ariaValueMax: `${number}` | null;
  ariaValueMin: `${number}` | null;
  ariaValueNow: `${number}` | null;
  ariaValueText: string | null;
  role: ARIARole | null;
}

/**
 * Valid values for `role`.
 */
export type ARIARole =
  | 'alert'
  | 'alertdialog'
  | 'button'
  | 'checkbox'
  | 'dialog'
  | 'gridcell'
  | 'link'
  | 'log'
  | 'marquee'
  | 'menuitem'
  | 'menuitemcheckbox'
  | 'menuitemradio'
  | 'option'
  | 'progressbar'
  | 'radio'
  | 'scrollbar'
  | 'searchbox'
  | 'slider'
  | 'spinbutton'
  | 'status'
  | 'switch'
  | 'tab'
  | 'tabpanel'
  | 'textbox'
  | 'timer'
  | 'tooltip'
  | 'treeitem'
  | 'combobox'
  | 'grid'
  | 'listbox'
  | 'menu'
  | 'menubar'
  | 'radiogroup'
  | 'tablist'
  | 'tree'
  | 'treegrid'
  | 'application'
  | 'article'
  | 'cell'
  | 'columnheader'
  | 'definition'
  | 'directory'
  | 'document'
  | 'feed'
  | 'figure'
  | 'group'
  | 'heading'
  | 'img'
  | 'list'
  | 'listitem'
  | 'math'
  | 'none'
  | 'note'
  | 'presentation'
  | 'region'
  | 'row'
  | 'rowgroup'
  | 'rowheader'
  | 'separator'
  | 'table'
  | 'term'
  | 'text'
  | 'toolbar'
  | 'banner'
  | 'complementary'
  | 'contentinfo'
  | 'form'
  | 'main'
  | 'navigation'
  | 'region'
  | 'search'
  | 'doc-abstract'
  | 'doc-acknowledgments'
  | 'doc-afterword'
  | 'doc-appendix'
  | 'doc-backlink'
  | 'doc-biblioentry'
  | 'doc-bibliography'
  | 'doc-biblioref'
  | 'doc-chapter'
  | 'doc-colophon'
  | 'doc-conclusion'
  | 'doc-cover'
  | 'doc-credit'
  | 'doc-credits'
  | 'doc-dedication'
  | 'doc-endnote'
  | 'doc-endnotes'
  | 'doc-epigraph'
  | 'doc-epilogue'
  | 'doc-errata'
  | 'doc-example'
  | 'doc-footnote'
  | 'doc-foreword'
  | 'doc-glossary'
  | 'doc-glossref'
  | 'doc-index'
  | 'doc-introduction'
  | 'doc-noteref'
  | 'doc-notice'
  | 'doc-pagebreak'
  | 'doc-pagelist'
  | 'doc-part'
  | 'doc-preface'
  | 'doc-prologue'
  | 'doc-pullquote'
  | 'doc-qna'
  | 'doc-subtitle'
  | 'doc-tip'
  | 'doc-toc';
