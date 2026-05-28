import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apprunner from 'aws-cdk-lib/aws-apprunner';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { DockerImageAsset, Platform } from 'aws-cdk-lib/aws-ecr-assets';

export interface GradioAppRunnerProps {
  musicStoreToolsFunction: lambda.IFunction;
  dbSecret: secretsmanager.ISecret;
  preferencesTable: dynamodb.ITable;
  toolsFunctionName: string;
  preferencesTableName: string;
}

export class GradioAppRunner extends Construct {
  constructor(scope: Construct, id: string, props: GradioAppRunnerProps) {
    super(scope, id);

    // Build the Docker image during CDK deploy and push to a CDK-managed ECR repo.
    // Build context is the project root so the Dockerfile can access both
    // gradio_app/ and lambdas/music_store_agents/.
    const image = new DockerImageAsset(this, 'Image', {
      directory: path.join(__dirname, '../../../'),
      file: 'gradio_app/Dockerfile',
      platform: Platform.LINUX_AMD64,
      exclude: [
        'layers/**',
        'lambdas/**/\.venv/**',
        'lambdas/**/__pycache__/**',
        'lambdas/**/tests/**',
        'lambdas/**/.pytest_cache/**',
        'cdk/node_modules/**',
        'gradio_app/.venv/**',
      ],
    });

    // App Runner needs this role to pull images from ECR.
    const accessRole = new iam.Role(this, 'AccessRole', {
      assumedBy: new iam.ServicePrincipal('build.apprunner.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSAppRunnerServicePolicyForECRAccess'
        ),
      ],
    });
    image.repository.grantPull(accessRole);

    // IAM role assumed by the running container to call AWS services.
    const instanceRole = new iam.Role(this, 'InstanceRole', {
      assumedBy: new iam.ServicePrincipal('tasks.apprunner.amazonaws.com'),
    });

    // The container runs the LangGraph graph directly, so it needs the same
    // AWS permissions as the music-store-agents Lambda.
    props.musicStoreToolsFunction.grantInvoke(instanceRole);
    props.dbSecret.grantRead(instanceRole);
    props.preferencesTable.grantReadWriteData(instanceRole);

    const service = new apprunner.CfnService(this, 'Service', {
      serviceName: 'music-store-gradio',
      sourceConfiguration: {
        authenticationConfiguration: {
          accessRoleArn: accessRole.roleArn,
        },
        imageRepository: {
          imageIdentifier: image.imageUri,
          imageRepositoryType: 'ECR',
          imageConfiguration: {
            port: '7860',
            runtimeEnvironmentVariables: [
              {
                name: 'AWS_DEFAULT_REGION',
                value: cdk.Stack.of(this).region,
              },
              {
                name: 'MUSIC_STORE_TOOLS_FUNCTION_NAME',
                value: props.toolsFunctionName,
              },
              {
                name: 'DB_SECRET_ARN',
                value: props.dbSecret.secretArn,
              },
              {
                name: 'PREFERENCES_TABLE_NAME',
                value: props.preferencesTableName,
              },
            ],
          },
        },
        // CDK manages redeployment by updating imageIdentifier on each deploy.
        autoDeploymentsEnabled: false,
      },
      instanceConfiguration: {
        instanceRoleArn: instanceRole.roleArn,
        cpu: '1 vCPU',
        memory: '2 GB',
      },
      healthCheckConfiguration: {
        protocol: 'HTTP',
        path: '/',
        interval: 10,
        timeout: 5,
        healthyThreshold: 1,
        unhealthyThreshold: 5,
      },
    });

    new cdk.CfnOutput(scope, 'GradioServiceUrl', {
      value: `https://${service.attrServiceUrl}`,
      description: 'Gradio Music Store UI — public HTTPS URL',
    });
  }
}
