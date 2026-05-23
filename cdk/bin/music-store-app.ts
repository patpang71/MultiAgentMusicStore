#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MusicStoreStack } from '../lib/music-store-stack';

const app = new cdk.App();

new MusicStoreStack(app, 'MusicStoreStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  githubOwner: app.node.tryGetContext('githubOwner'),
  githubRepo: app.node.tryGetContext('githubRepo'),
  githubBranch: app.node.tryGetContext('githubBranch') ?? 'main',
  codeStarConnectionArn: app.node.tryGetContext('codeStarConnectionArn'),
});
