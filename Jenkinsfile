pipeline {
    agent any

    environment {
        DOCKER_USER = 'joshitha2404'
        IMAGE_NAME = 'food-order-management'
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
        bat '"C:\\Users\\joshi\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" --version'
    }
}

stage('Install Dependencies') {
    steps {
        bat '"C:\\Users\\joshi\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pip install -r requirements.txt'
    }
}

stage('Run Tests') {
    steps {
        bat '"C:\\Users\\joshi\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pytest -v'
    }
}

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER% .'
                bat 'docker tag %DOCKER_USER%/%IMAGE_NAME%:%BUILD_NUMBER% %DOCKER_USER%/%IMAGE_NAME%:latest'
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_LOGIN_USER',
                        passwordVariable: 'DOCKER_TOKEN'
                    )
                ]) {
                    powershell '''
                        $env:DOCKER_TOKEN | docker login --username $env:DOCKER_LOGIN_USER --password-stdin
                        if ($LASTEXITCODE -ne 0) {
                            exit $LASTEXITCODE
                        }
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

        stage('Docker Logout') {
            steps {
                bat 'docker logout'
            }
        }
    }

    post {
        success {
            echo 'FoodFlow pipeline completed successfully!'
            echo 'Image: joshitha2404/food-order-management:latest'
        }

        failure {
            echo 'Pipeline failed. Check the Jenkins Console Output.'
        }

        always {
            echo 'Pipeline execution finished.'
        }
    }
}
