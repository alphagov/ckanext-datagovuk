#!/usr/bin/env groovy

library("govuk")

REPOSITORY = 'ckanext-datagovuk'

node ('!(ci-agent-4)') {

  try {
    stage('Checkout') {
      govuk.checkoutFromGitHubWithSSH(REPOSITORY)
      govuk.cleanupGit()
      govuk.mergeMasterBranch()
    }

    stage('Installing Packages') {
      sh("rm -rf ./venv")
      sh("python3.6 -m venv ./venv")
      sh("./bin/install-dependencies.sh ./venv/bin/pip")
    }

    stage('Tests') {
      govuk.setEnvar("GOVUK_ENV", "ci")
      sh("bash -c 'source venv/bin/activate ; ./bin/jenkins-tests.sh'")
    }

    if (govuk.hasDockerfile()) {
      govuk.dockerBuildTasks([:], "ckan")
    }

    if (env.BRANCH_NAME == 'master') {
      stage('Push release tag') {
        govuk.pushTag(REPOSITORY, BRANCH_NAME, 'release_' + BUILD_NUMBER)
      }

      if (govuk.hasDockerfile()) {
        stage("Tag Docker image") {
          govuk.dockerTagMasterBranch("ckan", env.BRANCH_NAME, env.BUILD_NUMBER)
        }
      }

      stage('Deploy to Integration') {
        govuk.deployIntegration('ckan', BRANCH_NAME, 'release_' + BUILD_NUMBER, 'deploy')
      }
    }
  } catch (e) {
    currentBuild.result = 'FAILED'
    step([$class: 'Mailer',
          notifyEveryUnstableBuild: true,
          recipients: 'govuk-ci-notifications@digital.cabinet-office.gov.uk',
          sendToIndividuals: true])
    throw e
  }

  // Wipe the workspace
  deleteDir()
}
