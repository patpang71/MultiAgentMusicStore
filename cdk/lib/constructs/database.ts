import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export interface DatabaseProps {
  vpc: ec2.Vpc;
}

export class Database extends Construct {
  public readonly instance: rds.DatabaseInstance;
  public readonly secret: secretsmanager.ISecret;
  public readonly securityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: DatabaseProps) {
    super(scope, id);

    this.securityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: props.vpc,
      description: 'RDS MySQL security group - Chinook music store',
      allowAllOutbound: false,
    });

    this.securityGroup.addIngressRule(
      ec2.Peer.ipv4('73.231.207.201/32'),
      ec2.Port.tcp(3306),
      'Allow DBeaver access from dev machine'
    );
    this.instance = new rds.DatabaseInstance(this, 'ChinookDb', {
      engine: rds.DatabaseInstanceEngine.mysql({
        version: rds.MysqlEngineVersion.VER_8_0,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MICRO
      ),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.securityGroup],
      databaseName: 'Chinook_AutoIncrement',
      credentials: rds.Credentials.fromGeneratedSecret('admin', {
        secretName: '/music-store/db-credentials',
      }),
      multiAz: false,
      allocatedStorage: 20,
      deletionProtection: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      backupRetention: cdk.Duration.days(0),
      publiclyAccessible: true
    });

    // Secret is always present when using fromGeneratedSecret
    this.secret = this.instance.secret!;

    new cdk.CfnOutput(scope, 'DbEndpoint', {
      value: this.instance.dbInstanceEndpointAddress,
      description: 'RDS MySQL endpoint',
    });

    new cdk.CfnOutput(scope, 'DbSecretArn', {
      value: this.secret.secretArn,
      description: 'Secrets Manager ARN for DB credentials',
    });
  }
}
