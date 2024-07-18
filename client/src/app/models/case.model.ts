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

import { Priority } from './priority.model';
import { convertDates } from '../utils/date-utils';

/** The type of a JSON object.  */
export interface JSONObject {
  [x: string]: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

/** The likelihood equivalent of each score from the Safe Search API. */
export enum Likelihood {
  UNKNOWN = 'UNKNOWN',
  VERY_UNLIKELY = 'VERY_UNLIKELY',
  UNLIKELY = 'UNLIKELY',
  POSSIBLE = 'POSSIBLE',
  LIKELY = 'LIKELY',
  VERY_LIKELY = 'VERY_LIKELY'
}

/** The score for each category we receive from the Safe Search API. */
export interface SafeSearchScores {
  adult: Likelihood;
  spoof: Likelihood;
  medical: Likelihood;
  violence: Likelihood;
  racy: Likelihood;
}

/** This interface represents the analysis scores on a Target */
export interface Analysis {
  safeSearchScores?: SafeSearchScores;
}

/**
 * The type of content, typically a URL or some type of image hash.
 */
export enum ContentType {
  URL = 'URL',
  HASH_PDQ = 'HASH_PDQ',
  UNKNOWN = 'UNKNOWN',
  API = 'API'
}

/** The source of why this content was reported. */
export enum Source {
  UNKNOWN = 'UNKNOWN',
  TCAP = 'TCAP',
  GIFCT = 'GIFCT',
  USER_REPORT = 'USER_REPORT',
  SAFE_SEARCH = 'SAFE_SEARCH',
  PERSPECTIVE = 'PERSPECTIVE'
}

/**
 * The status of content, so whether content is accessible/live.
 */
export enum Status {
  UNKNOWN = 'UNKNOWN',
  ACTIVE = 'ACTIVE',
  REMOVED_BY_USER = 'REMOVED_BY_USER',
  REMOVED_BY_MODERATOR = 'REMOVED_BY_MODERATOR',
  UNAVAILABLE = 'UNAVAILABLE'
}

/** This is used like a bool (yes = true, no = false) but with an additional
 *  value for representing uncertainty. */
export enum Confidence {
  YES = 'YES',
  NO = 'NO',
  UNSURE = 'UNSURE'
}

/**
 * This interface contains the data about the signal's content
 * @param contentValue The actual data in the signal's content
 * @param contentType The type of data in the signal's content
 */
export interface Content {
  contentValue: string;
  contentType: ContentType;
}

/**
 * This interface contains data about a flagger.
 * @param name The name of the flagger: GIFCT, TAT, USER_REPORT.
 * @param author The original author of the flag.
 * @param time The date that the flag was created.

 */
export interface Flag {
  name: Source;
  authors?: string[];
  createTime: Date;
  tags: string[];
}

/** Whether or not a Case is still in need of Review. */
export enum State {
  ACTIVE = 'ACTIVE',
  RESOLVED = 'RESOLVED',
  UNKNOWN = 'UNKNOWN'
}

/**  The decision made the moderator. */
export enum Decision {
  APPROVE = 'APPROVE',
  BLOCK = 'BLOCK'
}

/**
 * This interface represents a Review made on a Case by a moderator.
 * @param createTime the time the review was made.
 * @param decision the decision made by the moderation
 * @param user the user who made the decision.
 */
export interface ReviewHistory {
  createTime: Date;
  decision: Decision;
  user: string;
}

/**
 * A case is an entity representing something that requires review. It brings together
 * content with reports of flagged content and adds additional metadata for review.
 * @param id The identifier for this entity.
 * @param createTime The date it was created
 * @param state The current state of the Case, i.e. whether it is still in need of
 *    review or not.
 * @param priority The priority scores.
 * @param reviewHistory all decisions made on the case, when, and by whom.
 * @param signalContent Content that flagged this case.
 * @param associatedEntities A list of entities associated with this case.
 * @param imageBytes The raw image bytes of the content.
 * @param analysis Scores of additional analysis done on the content.
 * @param title The title of the content, provided by the platform.
 * @param description The description of the content, provided by the platform.
 * @param views The amount of views the content has received, provided by the platform.
 * @param uploadTime The time this piece of content was uploaded.
 * @param reports A list of all reports on this content.
 * @param ipAddress The IP address of the original uploader.
 * @param ipRegion The IP region of the original uploader.
 * @param similarCaseIds Identifiers of cases similar to this one.
 * @param notes Stored notes that a user has added to this case.
 */
export class Case {
  constructor(
    readonly id: string,
    readonly createTime: Date,
    readonly state: State,
    readonly priority: Priority,
    readonly reviewHistory: ReviewHistory[],
    readonly signalContent: Content[],
    readonly flags: Flag[],
    readonly associatedEntities: string[],
    readonly imageBytes: string | undefined,
    readonly analysis: Analysis,
    readonly title: string,
    readonly description: string,
    readonly views: number,
    readonly uploadTime: Date,
    readonly ipAddress: string,
    readonly ipRegion: string | undefined,
    readonly similarCaseIds: string[],
    readonly notes: string | undefined
  ) {}

  static deserialize(input: JSONObject): Case {
    convertDates(input);
    return new Case(
      input['id'],
      input['createTime'],
      input['state'],
      input['priority'],
      input['reviewHistory'],
      input['signalContent'],
      input['flags'],
      input['associatedEntities'],
      input['imageBytes'],
      input['analysis'],
      input['title'],
      input['description'],
      input['views'],
      input['uploadTime'],
      input['ipAddress'],
      input['ipRegion'],
      input['similarCaseIds'],
      input['notes']
    );
  }

  /**
   * Returns True if the Case is a URL type.
   * @returns - True if the case is a URL type
   */
  isTypeUrl(): boolean {
    // We only consider the first element of the content
    return this.signalContent[0].contentType === ContentType.URL;
  }

  /**
   * Returns True if the Case is a Image type.
   * @returns - True if the case is a Image type
   */
  isTypeImage(): boolean {
    // We only consider the first element of the content
    return this.signalContent[0].contentType === ContentType.HASH_PDQ;
  }

  /** Whether there is a possibility the case represents graphic material. */
  isPotentiallyGraphic(): boolean {
    // TODO: Base this value on properties that may indicate a graphic piece of
    // content.
    return true;
  }

  get firstFlag(): Flag | undefined {
    // Reports are sorted server-side based on the creation timestamp.
    return this.flags[0];
  }
}
