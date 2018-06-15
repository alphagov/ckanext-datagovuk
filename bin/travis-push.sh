#! /bin/bash

git config --local user.name "Travis CI"
git config --local user.email "govuk-ci@users.noreply.github.com"
git tag "release_${TRAVIS_BUILD_NUMBER}"
git push https://govuk-ci:${GOVUK_CI_TOKEN}@github.com/${TRAVIS_REPO_SLUG} "release_${TRAVIS_BUILD_NUMBER}"
git push https://govuk-ci:${GOVUK_CI_TOKEN}@github.com/${TRAVIS_REPO_SLUG} HEAD:refs/heads/release -f
