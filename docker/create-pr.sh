#!/bin/bash

set -eux

export IMAGE_TAG=$(gh api repos/alphagov/ckanext-datagovuk/branches/main | jq .commit.sha -r)

cd charts/charts/ckan/images

git checkout -b ci/${IMAGE_TAG}
git config --global user.email "govuk-ci@users.noreply.github.com"
git config --global user.name "govuk-ci"

gh auth setup-git

for ENV in integration; do
  (
    cd "${ENV}"
    for APP in ckan pycsw solr; do
      yq -i '.tag = env(IMAGE_TAG)' "${APP}.yaml"
      git add "${APP}.yaml"
    done
    git commit -m "Update image tags for ${ENV} to ${IMAGE_TAG}"
    gh pr create --title "Update image tags for ${ENV} (${IMAGE_TAG})" --base main --head "ci/${IMAGE_TAG}" --fill
  )
done
