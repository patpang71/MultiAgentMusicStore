import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Database } from './constructs/database';
import { MusicStorePipeline } from './constructs/pipeline';
import { MusicStoreToolsLambda } from './constructs/music-store-tools-lambda';

export interface MusicStoreStackProps extends cdk.StackProps {
  githubOwner: string;
  githubRepo: string;
  githubBranch?: string;
  codeStarConnectionArn: string;
}

export class MusicStoreStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: MusicStoreStackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'MusicStoreVpc', {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });

    const database = new Database(this, 'Database', { vpc });

    new MusicStoreToolsLambda(this, 'MusicStoreToolsLambda', { vpc, database });

    new MusicStorePipeline(this, 'Pipeline', {
      vpc,
      database,
      githubOwner: props.githubOwner,
      githubRepo: props.githubRepo,
      githubBranch: props.githubBranch ?? 'main',
      codeStarConnectionArn: props.codeStarConnectionArn,
    });
  }
}
