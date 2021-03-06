#!/usr/bin/env groovy

pipeline {
    agent none

    options {
        skipDefaultCheckout true
        disableConcurrentBuilds()
    }

    environment {
        build_dir = 'cluster-setup'
    }

    stages {
        stage('Checkout source code') {
            agent { label 'linux' }

            steps {
                script {
                    dir(env.build_dir) {
                        env.GIT_COMMIT = checkout(scm).GIT_COMMIT
                        env.GIT_COMMIT_SHORT = (env.GIT_COMMIT).substring(0, 5)
                        echo "INFO: Checked out ${env.GIT_COMMIT} [short ${env.GIT_COMMIT_SHORT}]"
                    }
                }

                stash name: 'source', includes: '**', useDefaultExcludes: false
            }

            post { cleanup { deleteDir() } }
        }

        stage('Merge gates') {
            parallel {
                stage('Lint the ansible scripts') {
                    agent {
                        docker {
                            image 'swails/ansible:latest'
                            alwaysPull true
                        }
                    }

                    steps {
                        unstash 'source'
                        dir(env.build_dir) {
                            sh(label: 'Linting the ansible playbooks',
                               script: """#!/bin/sh -ex
                                HOME="${env.WORKSPACE}" ansible-lint ubuntu-nodes/*.yml
                               """)
                        }
                    }

                    post { cleanup { deleteDir() } }
                }

                stage('Lint the docker-compose scripts') {
                    agent { label 'docker' }

                    steps {
                        unstash 'source'
                        dir("${env.build_dir}/qnap/docker-compose") {
                            sh(label: 'Checking docker-compose for errors',
                               script: """#!/bin/sh -ex
                                cp rdbs.yml docker-compose.yml
                                docker-compose config
                                /bin/rm -f docker-compose.yml
                               """)
                        }
                    }

                    post { cleanup { deleteDir() } }
                }

                stage('Build and push the nginx docker image') {
                    agent { label 'docker' }

                    when {
                        expression { github.fileChangedIn(path: 'qnap/docker-containers/') && (env.CHANGE_ID || env.BRANCH_NAME == 'master') }
                        beforeAgent true
                    }

                    steps {
                        script {
                            String tagName = env.BRANCH_NAME == 'master' ? env.GIT_COMMIT_SHORT : 'test'
                            String imageTag = "swails/qnap-nginx:${tagName}"
                            unstash 'source'
                            dir("${env.build_dir}/qnap/docker-containers/nginx") {
                                def image = docker.build(imageTag, '.')
                                docker.withRegistry('', 'swails-dockerhub') {
                                    echo "INFO: Pushing ${imageTag} to docker hub"
                                    image.push()
                                }
                            }
                        }
                    }

                    post { cleanup { deleteDir() } }
                }
            }
        }
    }
}