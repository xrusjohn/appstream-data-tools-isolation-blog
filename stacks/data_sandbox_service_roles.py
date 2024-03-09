#// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#// SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    aws_appstream as appstream,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_cloudformation as cfn,
    custom_resources as cr,
    NestedStack,
    Duration,
    Aws
)
from constructs import Construct


current_dir = os.path.dirname(__file__)


class AppstreamServiceRolesStack(NestedStack):
    def __init__(self, scope: Construct, id: str, aws_region='', **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Build Lambda Function Resources

        # Define Lambda Function Policy

        lambda_inline_policy = {
            'AllowIAMCreate': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            'iam:CreateRole',
                            'iam:AttachRolePolicy'
                        ],
                        resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/service-role/AmazonAppStreamServiceAccess",f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/service-role/ApplicationAutoScalingForAmazonAppStreamAccess"]
                    )
                ]
            )
        }

        # Build Lambda Role
        lambda_role = iam.Role(
            self,
            id='lambda-role',
            description='AppStream Service roles lambda',
            max_session_duration=Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
            inline_policies=lambda_inline_policy
            )


        # Build Lambda Function
        appstream_service_roles_lambda = _lambda.Function(self, 'AppStreamServiceRoles',
           handler='appstream_service_roles_lambda.lambda_handler',
           runtime=_lambda.Runtime.PYTHON_3_11,
           code=_lambda.Code.from_asset(os.path.join(current_dir, '../lambda')),
           role=lambda_role,
           memory_size=256,
           timeout=Duration.seconds(60)
           )

        #build custom resource to start appstream fleet
        appstream_deploy_service_roles_policy = cr.AwsCustomResourcePolicy.from_statements(statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['lambda:InvokeFunction'],
                resources=[appstream_service_roles_lambda.function_arn]
            )
        ])

        appstream_deploy_service_roles_create = cr.AwsSdkCall(
            action='invoke',
            service='Lambda',
            physical_resource_id=cr.PhysicalResourceId.of(id='AppStreamServiceRolesCreate'),
            parameters={
                "FunctionName": appstream_service_roles_lambda.function_arn
            }
        )
        

        appstream_deploy_service_roles_trigger = cr.AwsCustomResource(
            self, 'appstream-service-role',
            on_create=appstream_deploy_service_roles_create,
            policy=appstream_deploy_service_roles_policy,
            log_retention=logs.RetentionDays.THREE_MONTHS
        )