import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export interface MusicStoreAgentsLambdaProps {
  dbSecret: secretsmanager.ISecret;
  musicStoreToolsFunction: lambda.IFunction;
}

export class MusicStoreAgentsLambda extends Construct {
  public readonly lambdaFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: MusicStoreAgentsLambdaProps) {
    super(scope, id);

    this.lambdaFunction = new lambda.Function(this, 'Function', {
      functionName: 'music-store-agents',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      // requirements.txt deps are pre-installed into this directory by deploy.yml
      // before CDK packages and uploads the asset zip
      code: lambda.Code.fromAsset(
        path.join(__dirname, '../../../lambdas/music_store_agents'),
        {
          exclude: ['tests', '.venv', '*.pyc', '__pycache__', 'requirements.txt', '.pytest_cache'],
        }
      ),
      environment: {
        DB_SECRET_ARN: props.dbSecret.secretArn,
        MUSIC_STORE_TOOLS_FUNCTION_NAME: props.musicStoreToolsFunction.functionName,
      },
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
    });

    // Allow the agent to read the secret (OpenAI API key is stored alongside DB creds)
    props.dbSecret.grantRead(this.lambdaFunction);

    // Allow the agent to invoke the tools Lambda
    props.musicStoreToolsFunction.grantInvoke(this.lambdaFunction);

    new cdk.CfnOutput(scope, 'MusicStoreAgentsLambdaArn', {
      value: this.lambdaFunction.functionArn,
      description: 'music-store-agents Lambda ARN',
    });
  }
}
