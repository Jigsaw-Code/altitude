# Web Client

This project was generated with
[Angular CLI](https://github.com/angular/angular-cli) version 14.2.3.

## Development server

Install dependencies:

```shell
sudo npm install -g @angular/cli
```

```shell
npm install
```

Run `npm run start` for a dev server. Navigate to `http://localhost:4200/`. The
application will automatically reload if you change any of the source files.

### Inside a Docker container

For development purposes, you can build and run the dev server with Docker:

```shell
docker build -t jigsaw/altitude-client .
docker run \
    -p 8080:4200 \
    -p 49153:49153 \
    -v "/$(pwd):/build" \
    jigsaw/altitude-client
```

See the `../gateway` directory on how to run the client as part of the Gateway
Docker container.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can
also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `npm run build` to build the project. The build artifacts will be stored in the
`dist/` directory.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To
use this command, you need to first add a package that implements end-to-end
testing capabilities.

## Running formatter and linter

Run `npm run format` to format files and `npm run lint` to run linter. If you
want linter to attempt to fix any issues it has found, you can run
`npm run lint:fix`.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the
[Angular CLI Overview and Command Reference](https://angular.io/cli) page.
