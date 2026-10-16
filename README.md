# ckanext-datagovuk

The CKAN extension for data.gov.uk

## Features

- Configures Sentry automatically using a `SENTRY_DSN` environment variable.

## Development

### Pre-requisites

In order to run CKAN locally you will need a local postgres 18 server running. 
This server will need a `ckan` role and a `ckan` database created with permissions to access, read and write to it.

On the postgres server run these commands:

```sql
CREATE USER ckan WITH PASSWORD 'ckan';
CREATE DATABASE ckan OWNER ckan;
GRANT ALL PRIVILEGES ON DATABASE "ckan" to ckan; 
```

### Using the Makefile

1. Run `make run` to start up the docker compose stack
  - access CKAN on http://localhost:5001
  - access Find on http://localhost:4001

2. Run `make test` to just run the tests

### Running commands on the docker compose stack

It is easier to run things on the docker compose stack and get integrations with the different services rather than installing all the services on your machine.

1. Exec on to the ckan container by running `docker exec -it ckan-2.10 bash`

```
cd ../ckanext-datagovuk
pip install -r dev-requirements.txt
```

## Running the Tests

Run the tests inside the CKAN container on the docker compose stack:

```
python -m pytest --ckan-ini=test.ini ckanext/datagovuk/tests/
```

## Creating test data

First set the environment variables:

- `CKAN_INI` - location of CKAN ini file, this is already set on the docker stack
- `CKAN_TEST_SYSADMIN_NAME` and `CKAN_TEST_SYSADMIN_PASSWORD`

Then run the ckan command:

```
ckan datagovuk create-dgu-test-data
ckan datagovuk reindex-organisations  # this will create an organisations index used by the Find app
```

To remove the test data:

```
ckan datagovuk remove-dgu-test-data
```

## Deploying CKAN core and base images

> You rarely need to perform these steps and should only be used when there's an upstream CKAN change or a change to a dcat, spatial or harvester sha in the base Dockerfile.

Before building and pushing updates to the core and base CKAN images you will need to ensure that the version number or patch is incremented to prevent overwriting of existing images in the `build-config.yaml` and ensure that the CKAN Dockerfiles have the correct version and patch values.

You only need to run the `build_push_core` if there are changes to CKAN to deploy. If there are changes to the extensions then you should run `build_push_base` instead.

The CKAN core and base images can be built on Github actions by clicking on the `Build and push multi-arch image` workflow then under `Run workflow` selecting the branch with your update if it not on the `main` branch and the `build_push_core` build. Once the `build_push_core` has successfully completed you will need to run the `build_push_base` on the same branch.

If you are releasing a change to the base image, which handles the extension versions or a change to the CKAN version, tests might fail until the images are built and pushed into GHCR.

You can check if the images have been correctly built and pushed on the [CKAN package page](https://github.com/alphagov/ckanext-datagovuk/pkgs/container/ckan)

## Deploying CKAN

### Environments and URLs

- **Integration**: [https://ckan.integration.publishing.service.gov.uk](https://ckan.integration.publishing.service.gov.uk/)
- **Staging**: [https://ckan.staging.publishing.service.gov.uk](https://ckan.staging.publishing.service.gov.uk//)
- **Production**: [https://ckan.publishing.service.gov.uk/](https://ckan.publishing.service.gov.uk/)

---

### Deploying to Integration

1. **Make your change on a branch**
   Develop your feature or fix on a dedicated branch.

2. **Have the change approved**
   Open a Pull Request, get it reviewed and approved.

3. **Merge the change into `main`**
   Once approved, merge your branch into `main`. This triggers a GitHub Action that:
   - Builds a new CKAN Docker image.
   - Creates a Pull Request in the [govuk-dgu-charts](https://github.com/alphagov/govuk-dgu-charts) repo, updating the CKAN image tag.

4. **Merge the newly created PR**
   In the govuk-dgu-charts repo, merge the auto-created PR. Your changes will then be deployed to **Integration** at:
   [https://ckan.integration.publishing.service.gov.uk/](https://ckan.integration.publishing.service.gov.uk)

---

### Promoting to Staging and Production

1. **Create a release in GitHub**
   When you’re ready to promote changes beyond Integration, navigate to your repository’s “Releases” section, then:
   - Click “Draft a new release”.
   - Create a new tag (e.g. `v1.2.3`) and provide a release title/description
   - Publish the release.

2. **Merge the Staging and Production PRs**
   Creating a release triggers another GitHub Action that opens two Pull Requests in the govuk-dgu-charts repo:
   - One for [Staging](https://ckan.staging.publishing.service.gov.uk)
   - One for [Production](https://ckan.publishing.service.gov.uk)

   Merge these PRs in govuk-dgu-charts to deploy your changes to the respective environments.

Once both PRs are merged, your new CKAN version will be live on Staging and Production.

## Deploying PyCSW and Solr

To deploy a new version of PyCSW or Solr, the version and/or patch needs to be updated in the [build-config.yaml](https://github.com/alphagov/ckanext-datagovuk/blob/main/build-config.yaml) before triggering the build for `pycsw` or `solr` manually via the "Build and push multi-arch image" workflow in the github actions tab. You will then need to  manually update the pycsw or solr tag in [govuk-dgu-charts](https://github.com/alphagov/govuk-dgu-charts/tree/main/charts/ckan/images) repo for each environment.

## Deploying test branches to integration

To deploy test branches to integration you will need to run the `Build and push images` workflow from your test branch, and then once that has finished run the `Create charts PR`  also from your test branch.
