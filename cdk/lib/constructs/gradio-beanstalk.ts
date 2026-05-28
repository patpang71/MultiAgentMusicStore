import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as eb from 'aws-cdk-lib/aws-elasticbeanstalk';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface GradioBeanstalkProps {
  musicStoreToolsFunction: lambda.IFunction;
  dbSecret: secretsmanager.ISecret;
  preferencesTable: dynamodb.ITable;
  toolsFunctionName: string;
  preferencesTableName: string;
}

export class GradioBeanstalk extends Construct {
  /** S3 bucket the pipeline uploads source bundles to. */
  public readonly bundleBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: GradioBeanstalkProps) {
    super(scope, id);

    const appName = 'music-store-gradio';
    const envName = 'music-store-gradio-env';

    // S3 bucket for Beanstalk source bundles (one per pipeline run).
    this.bundleBucket = new s3.Bucket(this, 'BundleBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Service role that Elastic Beanstalk itself assumes to manage EC2, ELB, ASG, etc.
    const serviceRole = new iam.Role(this, 'ServiceRole', {
      assumedBy: new iam.ServicePrincipal('elasticbeanstalk.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSElasticBeanstalkEnhancedHealth'
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy'
        ),
      ],
    });

    // Instance role assumed by each EC2 instance running the Gradio container.
    const instanceRole = new iam.Role(this, 'InstanceRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AWSElasticBeanstalkWebTier'),
      ],
    });

    // Grant container the same AWS access as the agents Lambda.
    props.musicStoreToolsFunction.grantInvoke(instanceRole);
    props.dbSecret.grantRead(instanceRole);
    props.preferencesTable.grantReadWriteData(instanceRole);

    const instanceProfile = new iam.CfnInstanceProfile(this, 'InstanceProfile', {
      roles: [instanceRole.roleName],
    });

    const application = new eb.CfnApplication(this, 'Application', {
      applicationName: appName,
    });

    const optionSettings: eb.CfnEnvironment.OptionSettingProperty[] = [
      // Roles
      {
        namespace: 'aws:elasticbeanstalk:environment',
        optionName: 'ServiceRole',
        value: serviceRole.roleArn,
      },
      {
        namespace: 'aws:autoscaling:launchconfiguration',
        optionName: 'IamInstanceProfile',
        value: instanceProfile.ref,
      },
      // Single EC2 instance — no load balancer needed for a capstone demo.
      {
        namespace: 'aws:elasticbeanstalk:environment',
        optionName: 'EnvironmentType',
        value: 'SingleInstance',
      },
      // t3.small has 2GB RAM — enough for LangChain + LangGraph imports.
      {
        namespace: 'aws:autoscaling:launchconfiguration',
        optionName: 'InstanceType',
        value: 't3.small',
      },
      // Application environment variables — same set as the agents Lambda.
      {
        namespace: 'aws:elasticbeanstalk:application:environment',
        optionName: 'AWS_DEFAULT_REGION',
        value: cdk.Stack.of(this).region,
      },
      {
        namespace: 'aws:elasticbeanstalk:application:environment',
        optionName: 'MUSIC_STORE_TOOLS_FUNCTION_NAME',
        value: props.toolsFunctionName,
      },
      {
        namespace: 'aws:elasticbeanstalk:application:environment',
        optionName: 'DB_SECRET_ARN',
        value: props.dbSecret.secretArn,
      },
      {
        namespace: 'aws:elasticbeanstalk:application:environment',
        optionName: 'PREFERENCES_TABLE_NAME',
        value: props.preferencesTableName,
      },
      // EB's nginx proxies port 80 → 5000; Gradio reads PORT to know where to bind.
      {
        namespace: 'aws:elasticbeanstalk:application:environment',
        optionName: 'PORT',
        value: '5000',
      },
    ];

    // No versionLabel: EB deploys the built-in sample app on first creation.
    // The pipeline creates real application versions and updates this environment.
    // To find the latest Docker platform: aws elasticbeanstalk list-available-solution-stacks
    const cfnEnv = new eb.CfnEnvironment(this, 'Environment', {
      applicationName: application.applicationName!,
      environmentName: envName,
      solutionStackName: '64bit Amazon Linux 2023 v4.13.0 running Docker',
      optionSettings,
    });
    cfnEnv.addDependency(application);

    new cdk.CfnOutput(scope, 'GradioBundleBucketName', {
      value: this.bundleBucket.bucketName,
      description: 'S3 bucket for Gradio Beanstalk source bundles',
    });

    new cdk.CfnOutput(scope, 'GradioServiceUrl', {
      value: `http://${cfnEnv.attrEndpointUrl}`,
      description: 'Gradio Music Store UI URL',
    });
  }
}
