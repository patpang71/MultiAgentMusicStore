import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Database } from './database';

export interface MusicStorePipelineProps {
  vpc: ec2.Vpc;
  database: Database;
  githubOwner: string;
  githubRepo: string;
  githubBranch: string;
  codeStarConnectionArn: string;
}

export class MusicStorePipeline extends Construct {
  constructor(scope: Construct, id: string, props: MusicStorePipelineProps) {
    super(scope, id);

    // Artifacts
    const sourceOutput = new codepipeline.Artifact('SourceOutput');
    const buildOutput = new codepipeline.Artifact('BuildOutput');

    // --- Test Stage ---
    const testProject = new codebuild.PipelineProject(this, 'TestProject', {
      projectName: 'music-store-test',
      buildSpec: codebuild.BuildSpec.fromAsset(
        path.join(__dirname, '../../buildspecs/test.yml')
      ),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
      },
    });

    // --- DB Init Stage ---
    // CodeBuild needs to be in the VPC to reach RDS on the private subnet
    const dbInitSg = new ec2.SecurityGroup(this, 'DbInitSecurityGroup', {
      vpc: props.vpc,
      description: 'CodeBuild DB init - allows egress to RDS',
    });

    // Allow the DB init CodeBuild to connect to RDS on port 3306
    props.database.securityGroup.addIngressRule(
      dbInitSg,
      ec2.Port.tcp(3306),
      'Allow DB init CodeBuild to reach RDS'
    );

    const dbInitProject = new codebuild.PipelineProject(this, 'DbInitProject', {
      projectName: 'music-store-db-init',
      vpc: props.vpc,
      subnetSelection: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [dbInitSg],
      buildSpec: codebuild.BuildSpec.fromAsset(
        path.join(__dirname, '../../buildspecs/db-init.yml')
      ),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
        environmentVariables: {
          DB_SECRET_ARN: { value: props.database.secret.secretArn },
          SSM_INIT_FLAG: { value: '/music-store/db-initialized' },
        },
      },
    });

    // Grant Secrets Manager read for DB credentials
    props.database.secret.grantRead(dbInitProject);

    // Grant SSM read/write for the initialization flag
    dbInitProject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter', 'ssm:PutParameter'],
        resources: [
          `arn:aws:ssm:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:parameter/music-store/*`,
        ],
      })
    );

    // --- DB Health Check Stage ---
    // Runs in the VPC so it can reach RDS directly via pytest
    const dbHealthSg = new ec2.SecurityGroup(this, 'DbHealthSecurityGroup', {
      vpc: props.vpc,
      description: 'CodeBuild DB health check - allows egress to RDS',
    });

    props.database.securityGroup.addIngressRule(
      dbHealthSg,
      ec2.Port.tcp(3306),
      'Allow DB health check CodeBuild to reach RDS'
    );

    const dbHealthProject = new codebuild.PipelineProject(this, 'DbHealthProject', {
      projectName: 'music-store-db-health',
      vpc: props.vpc,
      subnetSelection: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [dbHealthSg],
      buildSpec: codebuild.BuildSpec.fromAsset(
        path.join(__dirname, '../../buildspecs/db-health.yml')
      ),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
        environmentVariables: {
          DB_SECRET_ARN: { value: props.database.secret.secretArn },
        },
      },
    });

    props.database.secret.grantRead(dbHealthProject);

    // --- Deploy Stage ---
    const deployProject = new codebuild.PipelineProject(this, 'DeployProject', {
      projectName: 'music-store-deploy',
      buildSpec: codebuild.BuildSpec.fromAsset(
        path.join(__dirname, '../../buildspecs/deploy.yml')
      ),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
      },
    });

    // Grant deploy project permissions to manage CloudFormation, Lambda, IAM, and S3
    deployProject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'cloudformation:*',
          'lambda:*',
          's3:*',
          'apigateway:*',
          'logs:*',
        ],
        resources: ['*'],
      })
    );

    deployProject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['iam:PassRole', 'iam:CreateRole', 'iam:AttachRolePolicy',
                  'iam:DeleteRole', 'iam:DetachRolePolicy', 'iam:GetRole',
                  'iam:PutRolePolicy', 'iam:DeleteRolePolicy', 'iam:TagRole'],
        resources: ['*'],
      })
    );

    // CDK deploy reads the bootstrap version from SSM and assumes CDK toolkit roles
    deployProject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter'],
        resources: [
          `arn:aws:ssm:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:parameter/cdk-bootstrap/*`,
        ],
      })
    );

    deployProject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['sts:AssumeRole'],
        resources: [
          `arn:aws:iam::${cdk.Stack.of(this).account}:role/cdk-*`,
        ],
      })
    );

    // --- Pipeline ---
    const pipeline = new codepipeline.Pipeline(this, 'MusicStorePipeline', {
      pipelineName: 'music-store-pipeline',
      crossAccountKeys: false,
      pipelineType: codepipeline.PipelineType.V2,
    });

    // Source: GitHub via CodeStar connection
    pipeline.addStage({
      stageName: 'Source',
      actions: [
        new codepipeline_actions.CodeStarConnectionsSourceAction({
          actionName: 'GitHub_Source',
          owner: props.githubOwner,
          repo: props.githubRepo,
          branch: props.githubBranch,
          connectionArn: props.codeStarConnectionArn,
          output: sourceOutput,
        }),
      ],
    });

    // Test: run unit/integration tests
    pipeline.addStage({
      stageName: 'Test',
      actions: [
        new codepipeline_actions.CodeBuildAction({
          actionName: 'Run_Tests',
          project: testProject,
          input: sourceOutput,
        }),
      ],
    });

    // DB Init: seed Chinook database on first run only (guarded by SSM flag)
    pipeline.addStage({
      stageName: 'DB_Init',
      actions: [
        new codepipeline_actions.CodeBuildAction({
          actionName: 'Initialize_Database',
          project: dbInitProject,
          input: sourceOutput,
        }),
      ],
    });

    // DB Health Check: verify all tables exist and contain rows before deploying
    pipeline.addStage({
      stageName: 'DB_Health_Check',
      actions: [
        new codepipeline_actions.CodeBuildAction({
          actionName: 'Check_Database_Health',
          project: dbHealthProject,
          input: sourceOutput,
        }),
      ],
    });

    // Deploy: build and deploy Lambda functions via SAM
    pipeline.addStage({
      stageName: 'Deploy',
      actions: [
        new codepipeline_actions.CodeBuildAction({
          actionName: 'Deploy_Lambda',
          project: deployProject,
          input: sourceOutput,
          outputs: [buildOutput],
        }),
      ],
    });

    new cdk.CfnOutput(scope, 'PipelineConsoleUrl', {
      value: `https://${cdk.Stack.of(this).region}.console.aws.amazon.com/codesuite/codepipeline/pipelines/music-store-pipeline/view`,
      description: 'CodePipeline console URL',
    });
  }
}
