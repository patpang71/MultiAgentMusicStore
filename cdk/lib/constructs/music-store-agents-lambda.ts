import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
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

    const preferencesTable = new dynamodb.Table(this, 'PreferencesTable', {
      tableName: 'music-store-customer-preferences',
      partitionKey: { name: 'customerId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const depsLayer = new lambda.LayerVersion(this, 'DepsLayer', {
      code: lambda.Code.fromAsset(
        path.join(__dirname, '../../../layers/music_store_agents_deps'),
        { exclude: ['*.pyc', '__pycache__'] }
      ),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'LangChain/LangGraph dependency layer for music-store-agents',
    });

    this.lambdaFunction = new lambda.Function(this, 'Function', {
      functionName: 'music-store-agents',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(
        path.join(__dirname, '../../../lambdas/music_store_agents'),
        { exclude: ['tests', '.venv', '*.pyc', '__pycache__', 'requirements.txt', '.pytest_cache'] }
      ),
      layers: [depsLayer],
      environment: {
        DB_SECRET_ARN: props.dbSecret.secretArn,
        MUSIC_STORE_TOOLS_FUNCTION_NAME: props.musicStoreToolsFunction.functionName,
        PREFERENCES_TABLE_NAME: preferencesTable.tableName,
      },
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
    });

    // Allow the agent to read the secret (OpenAI API key is stored alongside DB creds)
    props.dbSecret.grantRead(this.lambdaFunction);

    // Allow the agent to invoke the tools Lambda
    props.musicStoreToolsFunction.grantInvoke(this.lambdaFunction);

    // Allow the agent to read and write customer preferences
    preferencesTable.grantReadWriteData(this.lambdaFunction);

    new cdk.CfnOutput(scope, 'MusicStoreAgentsLambdaArn', {
      value: this.lambdaFunction.functionArn,
      description: 'music-store-agents Lambda ARN',
    });
  }
}
