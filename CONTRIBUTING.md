# How to Contribute

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

## Before you begin

### Contributor License Agreement

Contributions to this project must be accompanied by a Contributor License
Agreement. You (or your employer) retain the copyright to your contribution;
this simply gives us permission to use and redistribute your contributions as
part of the project. Head over to <https://cla.developers.google.com/> to see
your current agreements on file or to sign a new one.

You generally only need to submit a CLA once, so if you've already submitted one
(even if it was for a different project), you probably don't need to do it
again.

### Code Reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

### Community Guidelines

This project follows [Google's Open Source Community
Guidelines](https://opensource.google/conduct/).

## Setup

1. Install [`pre-commit`](https://pre-commit.com/) and associated [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks):

   ```shell
   sudo pip install pre-commit
   pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type post-checkout
   ```

1. Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

### Pre-commit

We use `pre-commit` to run multi-language pre-commits configured in
`.pre-commit-config.yaml` on the entire repo, such as testing, formatting,
and linting. The Git Hooks ensure the `pre-commit` rules run every time you
run `git commit`.

If you wish to run the `pre-commit` rules without committing you can run
`pre-commit` directly:

- `pre-commit run`: run all pre-commit hooks against currently staged files.
- `pre-commit run --all-files`: run all pre-commit hooks against all the files.
- `pre-commit run unittest --hook-stage=push`: run all unit test hooks against
  currently staged files.

Check out the [`pre-commit` documentation](https://pre-commit.com/#pre-commit-run)
for other useful invocations.

## Running all services locally

You can bring up the entire stack using multi-container Docker applications. Run
the utility script from the top-level directory in dev mode:

```shell
make DEV build start
```

This runs the entire stack using Docker Compose and helps you configure some
prerequisites, such as configuration files with usernames and passwords for the
database.

> **TIP:** Run `make help` to see what other actions are supported.

A number of services will be brought up and run on your local machine, the most
important ones are:

| Service                                   | Description                                        | Port    | URL                               |
| ----------------------------------------- | -------------------------------------------------- | ------- | --------------------------------- |
| `gateway`                                 | The entrypoint to the web app                      | `80`    | <http://localhost:80>             |
| `client`                                  | Angular web application                            | `8080`  | <http://localhost:8080>           |
| `ui-service`                              | "Backend For Frontend" of the client               | `8081`  | <http://localhost:8081>           |
| `signal-service`                          | Backend REST API                                   | `8082`  | <http://localhost:8082>           |
| `mongodb`                                 | Database                                           | `27017` | <http://localhost:27017>          |
| `mongodb-admin`                           | mongo-express database admin interface             | `8181`  | <http://localhost:8181/mongodbz/> |
| `taskqueue-worker`, `taskqueue-scheduler` | Celery based taskqueue with a worker and scheduler | -       | -                                 |
| `taskqueue-monitor`                       | Flower web interface to monitor the taskqueue      | `5555`  | <http://localhost:5555/tasksz/>   |

Logs for all these containers are merged and written to stdout.

### Debugging

You can view which containers are running with the following command, and use
the -a flag to show all containers, not just the currently running ones.

```shell
docker container ls
```

### Pruning Docker assets

If you are running into Docker issues, it can sometimes be useful
to[prune stale Docker assets](https://docs.docker.com/engine/reference/commandline/system_prune/)
(e.g. containers, images, and networks) before running the script again:

```shell
docker system prune -a
```

Note that this will affect assets from all projects, so if you are working on
other projects that user Docker this will prune their stale assets as well.

#### MongoDB database

#### Using the admin UI

The MongoDB admin UI, powered by
[mongo-express](https://github.com/mongo-express/mongo-express), is running on
<http://localhost:8181>.

#### Using the MongoDB Shell

You can access a running `mongodb` container using the MongoDB Shell (`mongosh`)
by [installing](https://www.mongodb.com/docs/mongodb-shell/install/) it and then
connecting to the container with:

```shell
docker exec -it altitude-dev-mongodb-1 mongosh -u <admin> -p <password>

# Switch to the app's database
use altitude

# See all the entries in the signals table
db.signal.find()
```

Check out the
[`mongosh` documentation](https://www.mongodb.com/docs/mongodb-shell/) for
details on how to use the MongoDB Shell.
