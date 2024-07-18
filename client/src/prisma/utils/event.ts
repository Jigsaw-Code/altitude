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

/**
 * Emit the event 'name' from the element 'el' with customized options
 *
 * @param el - html element
 * @param name - The name of the event
 * @param options - the options of the event
 * @return custom event
 */
export function emit(
  el: HTMLElement,
  name: string,
  options?: CustomEventInit
): CustomEvent<unknown> {
  const event = new CustomEvent(name, {
    bubbles: true,
    cancelable: false,
    composed: true,
    detail: {},
    ...options
  });

  el.dispatchEvent(event);

  return event;
}

/**
 * Debounce function {fn} in given {ms} time
 *
 * @param callback - function
 * @param waitFor - number in milliseconds
 * @return the given function
 */
export function debounce<F extends (...args: Parameters<F>) => ReturnType<F>>(
  callback: F,
  waitFor = 100
): (...args: Parameters<F>) => void {
  let timeout: number;

  return (...args: Parameters<F>): void => {
    clearTimeout(timeout);
    timeout = window.setTimeout(() => callback(...args), waitFor);
  };
}
