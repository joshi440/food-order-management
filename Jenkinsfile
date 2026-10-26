pipeline {
    agent any

    environment {
        DOCKER_USER = 'joshitha2404'
        IMAGE_NAME = 'food-order-management'
        PYTHON = 'C:\\Users\\joshi\\AppData\\Local\\Programs\\Python\\Python310\\python.exe'
        KUBECONFIG = 'C:\\Users\\joshi\\.kube\\config'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Check Tools') {
            steps {
                bat 'docker --version'
                bat '"%PYTHON%" --version'
                bat 'kubectl version --client'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON%" -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"%PYTHON%" -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER% .'
                bat 'docker tag %DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER% %DOCKER_USER%/%IMAGE_NAME%:latest'
            }
        }

        stage('Check Docker Credential') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-pat-test',
                        usernameVariable: 'DOCKER_LOGIN_USER',
                        passwordVariable: 'DOCKER_TOKEN'
                    )
                ]) {
                    powershell '''
                        $ErrorActionPreference = "Stop"

                        Write-Host "Credential username: $env:DOCKER_LOGIN_USER"
                        Write-Host "Token present: $(-not [string]::IsNullOrWhiteSpace($env:DOCKER_TOKEN))"
                        Write-Host "Username matches expected: $($env:DOCKER_LOGIN_USER -eq 'joshitha2404')"

                        docker context show
                        docker context inspect default --format '{{.Endpoints.docker.Host}}'
                    '''
                }
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-pat-test',
                        usernameVariable: 'DOCKER_LOGIN_USER',
                        passwordVariable: 'DOCKER_TOKEN'
                    )
                ]) {
                    powershell '''
                        $ErrorActionPreference = "Stop"

                        $token = $env:DOCKER_TOKEN.Trim()
                        $username = $env:DOCKER_LOGIN_USER

                        if ([string]::IsNullOrWhiteSpace($token)) {
                            throw "Docker Hub token is empty."
                        }

                        $token | docker login --username $username --password-stdin

                        if ($LASTEXITCODE -ne 0) {
                            throw "Docker Hub login failed."
                        }

                        Write-Host "Docker Hub login successful."
                    '''
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                bat 'docker push %DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER%'
                bat 'docker push %DOCKER_USER%/%IMAGE_NAME%:latest'
            }
        }

        stage('Verify Kubernetes Access') {
            steps {
                bat 'kubectl --kubeconfig="%KUBECONFIG%" get deployment food-order-app'
            }
        }

        stage('Deploy FoodFlow') {
            steps {
                bat 'kubectl --kubeconfig="%KUBECONFIG%" set image deployment/food-order-app food-order-app=%DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER%'
            }
        }

        stage('Verify Deployment') {
            steps {
                bat 'kubectl --kubeconfig="%KUBECONFIG%" rollout status deployment/food-order-app --timeout=120s'
                bat 'kubectl --kubeconfig="%KUBECONFIG%" get deployment food-order-app'
            }
        }
    }

    post {
        success {
            echo 'FoodFlow pipeline completed successfully!'
            echo 'Image: joshitha2404/food-order-management:latest'
            echo 'FoodFlow Kubernetes deployment completed successfully.'
        }

        failure {
            echo 'FoodFlow pipeline failed. Check the Jenkins Console Output.'
        }

        always {
            bat 'docker logout'
            echo 'Pipeline execution finished.'
        }
    }
}
