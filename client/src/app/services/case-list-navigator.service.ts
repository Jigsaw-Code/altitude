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

import { Injectable } from '@angular/core';

/** The default number of cases per page. */
export const DEFAULT_PAGE_SIZE = 10;
/** The page size options for case list paginator. */
const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 250];

/**
 * Interface representing pagination cursor tokens that are sent to and
 * received by the UI service.
 */
export interface CursorTokens {
  previous?: string;
  next?: string;
}

// TODO: Consider merging this service with the `CaseTableDataSource`.

/** Service to manage navigation between cases. */
@Injectable({
  providedIn: 'root'
})
export class CaseListNavigator {
  private caseList = new Dll();
  currentPageSize = DEFAULT_PAGE_SIZE;
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS;
  currentPageIndex = 0;
  lastTokens: CursorTokens = {};
  currentTokens: CursorTokens = {};

  reset() {
    this.caseList.reset();
  }

  add(caseId: string) {
    this.caseList.add(caseId);
  }

  previous(caseId: string): string | null {
    return this.caseList.previous(caseId);
  }

  next(caseId: string): string | null {
    return this.caseList.next(caseId);
  }

  remove(caseId: string) {
    this.caseList.remove(caseId);
  }
}
/**
 * Represents a node in a double linked list
 */
class DllNode {
  data: string;
  next: DllNode | undefined;
  prev: DllNode | undefined;

  constructor(data: string) {
    this.data = data;
  }
}

/**
 * Data structure implemented as a double linked list
 * whose nodes are stored in a map and refernced by the node's data.
 */
class Dll {
  private current: DllNode | undefined;
  private nodes = new Map<string, DllNode>();
  /* Empties all data in the data structure. */
  reset() {
    this.current = undefined;
    this.nodes.clear();
  }

  /**
   * Adds one data element to the data structure.
   * @param data the data element to be added.
   */
  add(data: string) {
    if (!this.nodes.size) {
      const node = new DllNode(data);
      this.nodes.set(data, node);
      this.current = node;
    } else {
      (<DllNode>this.current).next = new DllNode(data);
      (<DllNode>(<DllNode>this.current).next).prev = this.current;
      this.current = (<DllNode>this.current).next;
      this.nodes.set(data, <DllNode>this.current);
    }
  }

  /**
   * Gets the previous data item in the structure.
   * @param nodeId The identifier/data for the node we would like to get the previous of.
   * @returns The data element in the previous position in the structure.
   */
  previous(nodeId: string): string | null {
    this.setCurrent(nodeId);
    if (this.current && (<DllNode>this.current).prev) {
      this.current = (<DllNode>this.current).prev;
      return (<DllNode>this.current).data;
    }
    return null;
  }

  /**
   * Gets the next data item in the structure.
   * @param nodeId The identifier/data for the node we would like to get the next of.
   * @returns The data element in the next position in the structure.
   */
  next(nodeId: string): string | null {
    this.setCurrent(nodeId);
    if (this.current && (<DllNode>this.current).next) {
      this.current = (<DllNode>this.current).next;
      return (<DllNode>this.current).data;
    }
    return null;
  }

  /**
   * Sets the current position in the data structure.
   * @param nodeId The identifier/data for the node we would like to set.
   */
  private setCurrent(nodeId: string) {
    this.current = this.nodes.get(nodeId);
  }

  /**
   * Removes a data element from the structure.
   * @param nodeId The identifier/data for the node we would like to remove.
   */
  remove(nodeId: string) {
    const node = <DllNode>this.nodes.get(nodeId);
    if (node.prev) {
      node.prev.next = node.next;
    }
    if (node.next) {
      node.next.prev = node.prev;
    }
    this.nodes.delete(nodeId);
  }
}
