import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Database } from './database';

export interface MusicStoreToolsLambdaProps {
  vpc: ec2.Vpc;
  database: Database;
}

export class MusicStoreToolsLambda extends Construct {
  public readonly lambdaFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: MusicStoreToolsLambdaProps) {
    super(scope, id);

    const lambdaSg = new ec2.SecurityGroup(this, 'SecurityGroup', {
      vpc: props.vpc,
      description: 'music-store-tools Lambda - egress to RDS',
    });

    // Allow this Lambda to reach RDS on port 3306
    props.database.securityGroup.addIngressRule(
      lambdaSg,
      ec2.Port.tcp(3306),
      'Allow music-store-tools Lambda to reach RDS'
    );

    this.lambdaFunction = new lambda.Function(this, 'Function', {
      functionName: 'music-store-tools',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      // requirements.txt deps are pre-installed into this directory by deploy.yml
      // before CDK packages and uploads the asset zip
      code: lambda.Code.fromAsset(
        path.join(__dirname, '../../../lambdas/music_store_tools'),
        {
          exclude: ['tests', '.venv', '*.pyc', '__pycache__', 'requirements.txt', '.pytest_cache'],
        }
      ),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [lambdaSg],
      environment: {
        DB_SECRET_ARN: props.database.secret.secretArn,
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
    });

    props.database.secret.grantRead(this.lambdaFunction);

    new cdk.CfnOutput(scope, 'MusicStoreToolsLambdaArn', {
      value: this.lambdaFunction.functionArn,
      description: 'music-store-tools Lambda ARN',
    });
  }
}
