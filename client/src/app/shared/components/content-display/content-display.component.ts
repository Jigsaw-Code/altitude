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

import { Component, HostBinding, Input, OnChanges } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import 'src/prisma/components/prisma_action_button/prisma-action-button';
import { Case } from '../../../models/case.model';
import { AbsoluteLinkPipe } from '../../pipes/absolute-link.pipe';

@Component({
  selector: 'app-content-display',
  templateUrl: './content-display.component.html',
  styleUrls: ['./content-display.component.scss']
})
export class ContentDisplayComponent implements OnChanges {
  // TODO: Replace with `required: true` once we've upgraded to Angular v16.
  /** The Case with the content to display. */
  @Input() case!: Case;

  @HostBinding('class.is-potentially-graphic')
  get isPotentiallyGraphic() {
    return this.case.isPotentiallyGraphic();
  }

  private safeSrc: SafeResourceUrl =
    this.sanitizer.bypassSecurityTrustResourceUrl('');

  getSafeSrc(): SafeResourceUrl {
    return this.safeSrc;
  }

  constructor(private readonly sanitizer: DomSanitizer) {}

  ngOnChanges() {
    this.assertRequiredProperty('case');
    if (this.case.isTypeUrl()) {
      const absoluteUrl = new AbsoluteLinkPipe().transform(
        // Currently, the information to be displayed is the first element
        //  of the content list.
        // TODO: Figure out how to accomodate signals with multiple contents.
        this.case.signalContent[0].contentValue
      );
      // Since these URLs come from a different domain they are untrusted by
      // default. This bypasses those checks.
      this.safeSrc = this.sanitizer.bypassSecurityTrustResourceUrl(absoluteUrl);
    }
  }

  private assertRequiredProperty(name: string) {
    const value = (this as any)[name]; // eslint-disable-line @typescript-eslint/no-explicit-any
    if (value === null || value === undefined) {
      throw Error(`Required property not set: \`${name}\``);
    }
  }

  openContent() {
    if (this.case.isTypeUrl()) {
      window.open(
        new AbsoluteLinkPipe().transform(
          this.case.signalContent[0].contentValue
        )
      );
    } else if (this.case.isTypeImage()) {
      const image = new Image();
      image.src = 'data:image/png;base64,' + this.case.imageBytes;
      const w = window.open('about:blank');
      if (w) {
        w.document.write(image.outerHTML);
      }
    }
  }
}
