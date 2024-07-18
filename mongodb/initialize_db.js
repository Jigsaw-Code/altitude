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
 * Initialize the database with authentication.
 *
 * This script only runs if it is the first time initializing the database (aka
 *  the ./data dir is empty).
 */
print("#################### START `initialize_db.js` ####################");

const fs = require("fs");

const USERNAME = fs.readFileSync(process.env.MONGO_USERNAME_FILE, "utf8");
const PASSWORD = fs.readFileSync(process.env.MONGO_PASSWORD_FILE, "utf8");

const db = db.getSiblingDB(process.env.MONGO_DATABASE);
db.createUser({
  user: USERNAME,
  pwd: PASSWORD,
  roles: [{ role: "readWrite", db: process.env.MONGO_DATABASE }],
});

print("#################### END `initialize_db.js`###################");
